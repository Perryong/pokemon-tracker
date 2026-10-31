import os
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from uuid import uuid4

import httpx
import pytest

from pokemon_market.server import make_server
from pokemon_market.storage import PostgresMarketStore
from pokemon_market.workflow import WorkflowService


@pytest.fixture
def private_api(bundle, now, tmp_path):
    dsn = os.environ.get('MARKET_TEST_DSN')
    if not dsn:
        pytest.skip('MARKET_TEST_DSN required')
    store = PostgresMarketStore(dsn)
    store.setup()
    workspace = 'api-' + uuid4().hex
    store.create(bundle.model_copy(update={'session_id': workspace}))
    service = WorkflowService(store, workspace, clock=lambda: now)
    (tmp_path / 'index.html').write_text('<h1>Market UI</h1>')
    server = make_server(service, port=0, token='operator-test-key-with-32-characters',
                         peer_token='peer-test-key-distinct-32-characters', dist=tmp_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f'http://127.0.0.1:{server.server_port}'
    with httpx.Client(base_url=origin, headers={'Origin': origin}) as client:
        yield client, service
    server.shutdown()
    server.server_close()
    thread.join(5)


def test_private_records_require_cookie_and_login_is_origin_bound(private_api):
    client, _ = private_api
    assert client.get('/api/operations/state').status_code == 401
    assert client.post('/api/operations/login', headers={'Origin': 'https://evil.invalid'}, json={'token':'operator-test-key-with-32-characters'}).status_code == 403
    assert client.post('/api/operations/login', json={'token':'wrong'}).status_code == 401
    response = client.post('/api/operations/login', json={'token':'operator-test-key-with-32-characters'})
    assert response.status_code == 204
    cookie = response.headers['set-cookie']
    assert 'HttpOnly' in cookie and 'SameSite=Strict' in cookie
    state = client.get('/api/operations/state')
    assert state.status_code == 200 and state.json()['mode'] == 'simulation'
    assert 'operator-test-key' not in state.text
    assert client.post('/api/operations/pause', headers={'Origin':'https://evil.invalid'}, json={'paused':True}).status_code == 403
    assert client.post('/api/operations/logout', json={}).status_code == 204
    assert client.get('/api/operations/state').status_code == 401


def test_operator_controls_and_strict_request_validation(private_api):
    client, service = private_api
    client.post('/api/operations/login', json={'token':'operator-test-key-with-32-characters'})
    assert client.post('/api/operations/schedule', json={'times':['09:00'],'timezone':'Asia/Singapore'}).status_code == 200
    assert client.post('/api/operations/schedule', json={'times':[{}],'timezone':'Asia/Singapore'}).status_code == 400
    assert client.post('/api/operations/pause', json={'paused':'false'}).status_code == 400
    assert client.post('/api/operations/assess', json={'listing_id':'listing-1'}).status_code == 200
    assert len(client.get('/api/operations/state').json()['mandates']) == 1
    assert client.post('/api/operations/pause', json={'paused':True}).status_code == 200
    assert service.state()['paused'] is True
    assert client.post('/api/operations/assess', json={'listing_id':'listing-1'}).status_code == 409


def test_malformed_oversized_and_unknown_endpoints_fail_closed(private_api):
    client, _ = private_api
    client.post('/api/operations/login', json={'token':'operator-test-key-with-32-characters'})
    assert client.post('/api/operations/pause', content='{',headers={'Content-Type':'application/json'}).status_code == 400
    assert client.post('/api/operations/pause', content='x'*70000,headers={'Content-Type':'application/json'}).status_code == 413
    assert client.get('/api/operations/nope').status_code == 404
    assert client.get('/api/operations/state',headers={'Host':'evil.invalid'}).status_code == 403
    assert client.get('/').status_code == 200
    assert client.get('/.env').status_code == 404
    assert client.get('/api/cardmarket/base1-1').status_code == 503


def test_short_or_reused_secrets_are_rejected(private_api, tmp_path):
    _, service = private_api
    with pytest.raises(ValueError):
        make_server(service, port=0, token='short',peer_token='short',dist=tmp_path)


def test_demo_seed_is_explicit_and_restart_does_not_refresh_dates(private_api, now):
    from pokemon_market.server import initialize_fixture

    _, service = private_api
    workspace = 'seed-' + uuid4().hex
    initialize_fixture(service.store, workspace, now=now)
    before = service.store.session(workspace, clock=lambda: now).snapshot()
    from datetime import timedelta
    initialize_fixture(service.store, workspace, now=now + timedelta(days=30))
    assert service.store.session(workspace, clock=lambda: now).snapshot() == before
    assert len(before['inventory']['units']) > 0


def test_serve_cli_requires_private_configuration(monkeypatch, capsys):
    from pokemon_market.__main__ import main

    for key in ('MARKET_DATABASE_URL', 'MARKET_OPERATOR_TOKEN', 'MARKET_PEER_TOKEN'):
        monkeypatch.delenv(key, raising=False)
    assert main(['serve']) == 1
    assert capsys.readouterr().err.strip() == 'missing_server_configuration'


@pytest.mark.parametrize(('path', 'priority', 'expected'), [
    ('/api/market/cards/base1-1', 'background', 'background'),
    ('/api/market/cards/base1-1', 'unexpected', None),
    ('/api/market/cards/base1-1', None, None),
    ('/api/cardmarket/base1-1', 'background', None),
])
def test_reference_proxy_preserves_only_supported_market_priority(tmp_path, path, priority, expected):
    class ReferenceBackend(BaseHTTPRequestHandler):
        def do_GET(self):
            body = json.dumps(dict(self.headers)).encode()
            self.send_response(200)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_):
            pass

    backend = ThreadingHTTPServer(('127.0.0.1', 0), ReferenceBackend)
    proxy = make_server(None, port=0, token='operator-test-key-with-32-characters',
                        peer_token='peer-test-key-distinct-32-characters', dist=tmp_path,
                        reference_url=f'http://127.0.0.1:{backend.server_port}')
    threads = [threading.Thread(target=server.serve_forever, daemon=True) for server in (backend, proxy)]
    for thread in threads:
        thread.start()
    try:
        headers = {'Authorization': 'Bearer private-test-only', 'Cookie': 'market_session=private-test-only'}
        if priority is not None:
            headers['X-Market-Priority'] = priority
        response = httpx.get(f'http://127.0.0.1:{proxy.server_port}{path}', headers=headers, trust_env=False)
        assert response.status_code == 200
        forwarded = {key.lower(): value for key, value in response.json().items()}
        assert forwarded.get('x-market-priority') == expected
        assert 'authorization' not in forwarded
        assert 'cookie' not in forwarded
    finally:
        for server in (proxy, backend):
            server.shutdown()
            server.server_close()
        for thread in threads:
            thread.join(5)
