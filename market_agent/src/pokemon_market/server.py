"""Loopback operator service. Credentials and business records never enter static UI."""

import hashlib
import json
import mimetypes
import secrets
import threading
import time
from datetime import datetime, timezone
from importlib.resources import files
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

import httpx

from .contracts import MarketError

MAX_BODY = 65536


def make_server(service, *, port=8790, token, peer_token, dist, reference_url=None, peer_service=None):
    if len(token) < 32 or len(peer_token) < 32 or secrets.compare_digest(token, peer_token):
        raise ValueError('distinct server secrets of at least 32 characters required')
    root = Path(dist).resolve()
    if reference_url:
        target = urlsplit(reference_url)
        if target.scheme != 'http' or target.hostname != '127.0.0.1' or not target.port or target.path not in ('', '/') or target.username or target.password or target.query or target.fragment:
            raise ValueError('reference backend must be trusted numeric loopback HTTP')
    sessions = {}
    attempts = {}
    auth_lock = threading.Lock()

    class Handler(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'

        def setup(self):
            super().setup()
            self.connection.settimeout(15)

        def log_message(self, *_):
            pass  # Access keys, cookies, private request bodies and URLs stay out of logs.

        def respond(self, code, data=None, *, headers=None, raw=None, content_type='application/json'):
            body = raw if raw is not None else (json.dumps(data).encode() if data is not None else b'')
            if code >= 400:
                # Rejected requests may still have unread bodies; never reuse them.
                self.close_connection = True
            self.send_response(code)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            if self.close_connection:
                self.send_header('Connection', 'close')
            for key, value in (headers or {}).items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body)

        def authorize(self):
            cookie = SimpleCookie()
            try:
                cookie.load(self.headers.get('Cookie', ''))
            except Exception:
                return False
            item = cookie.get('market_session')
            if not item:
                return False
            digest = hashlib.sha256(item.value.encode()).hexdigest()
            with auth_lock:
                expiry = sessions.get(digest, 0)
                if expiry <= time.monotonic():
                    sessions.pop(digest, None)
                    return False
            return True

        def peer_authorized(self):
            return secrets.compare_digest(self.headers.get('Authorization', '').encode(), ('Bearer ' + peer_token).encode())

        def body(self):
            try:
                size = int(self.headers.get('Content-Length', '0'))
            except ValueError:
                raise MarketError('invalid_request') from None
            if size < 0 or size > MAX_BODY:
                raise MarketError('body_too_large')
            if self.headers.get('Transfer-Encoding'):
                raise MarketError('invalid_request')
            if size and self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                raise MarketError('invalid_request')
            try:
                payload = json.loads(self.rfile.read(size)) if size else {}
            except (ValueError, RecursionError, UnicodeDecodeError):
                raise MarketError('invalid_request') from None
            if not isinstance(payload, dict):
                raise MarketError('invalid_request')
            return payload

        def dispatch(self):
            origin = f'http://127.0.0.1:{self.server.server_port}'
            if self.headers.get('Host') != f'127.0.0.1:{self.server.server_port}':
                self.respond(403, {'error': 'invalid_host'})
                return
            if len(self.path) > 1024:
                raise MarketError('invalid_request')
            path = urlsplit(self.path).path
            if path.startswith('/api/operations/'):
                if self.command == 'POST' and self.headers.get('Origin') != origin:
                    self.respond(403, {'error': 'invalid_origin'})
                    return
                if path == '/api/operations/login' and self.command == 'POST':
                    payload = self.body()
                    with auth_lock:
                        now = time.monotonic()
                        recent = [t for t in attempts.get(self.client_address[0], []) if t > now - 60]
                        if len(recent) >= 10:
                            self.respond(429, {'error': 'login_rate_limited'})
                            return
                        attempts[self.client_address[0]] = recent + [now]
                    value = payload.get('token')
                    if set(payload) != {'token'} or not isinstance(value, str) or not secrets.compare_digest(value.encode(), token.encode()):
                        self.respond(401, {'error': 'unauthorized'})
                        return
                    key = secrets.token_urlsafe(32)
                    with auth_lock:
                        now = time.monotonic()
                        for old in list(sessions):
                            if sessions[old] <= now:
                                sessions.pop(old)
                        if len(sessions) >= 256:
                            self.respond(429, {'error': 'session_limit'})
                            return
                        sessions[hashlib.sha256(key.encode()).hexdigest()] = now + 8 * 3600
                    self.respond(204, headers={'Set-Cookie': f'market_session={key}; Path=/api/operations/; HttpOnly; SameSite=Strict; Max-Age=28800'})
                    return
                if not self.authorize():
                    self.respond(401, {'error': 'unauthorized'})
                    return
                if path == '/api/operations/state' and self.command == 'GET':
                    self.respond(200, service.state())
                    return
                if self.command != 'POST':
                    self.respond(404, {'error': 'not_found'})
                    return
                payload = self.body()
                if path == '/api/operations/logout' and not payload:
                    cookie = SimpleCookie(self.headers.get('Cookie', ''))
                    with auth_lock:
                        sessions.pop(hashlib.sha256(cookie['market_session'].value.encode()).hexdigest(), None)
                    self.respond(204, headers={'Set-Cookie': 'market_session=; Path=/api/operations/; HttpOnly; SameSite=Strict; Max-Age=0'})
                    return
                if path == '/api/operations/pause' and set(payload) == {'paused'}:
                    service.set_paused(payload['paused'])
                elif path == '/api/operations/schedule' and set(payload) == {'times', 'timezone'}:
                    service.set_schedule(payload['times'], payload['timezone'])
                elif path == '/api/operations/assess' and set(payload) == {'listing_id'} and isinstance(payload['listing_id'], str) and len(payload['listing_id']) <= 300:
                    service.assess(payload['listing_id'])
                elif path == '/api/operations/run' and not payload:
                    service.run_due()
                else:
                    raise MarketError('invalid_request')
                self.respond(200, {'ok': True})
                return

            if path.startswith('/a2a/'):
                if not self.peer_authorized():
                    self.respond(401, {'error': 'unauthorized_peer'})
                    return
                if peer_service is None:
                    self.respond(503, {'error': 'peer_unconfigured'})
                    return
                parts = path.strip('/').split('/')
                if len(parts) < 3 or parts[1] not in ('market', 'sales'):
                    raise MarketError('invalid_request')
                role = parts[1]
                if parts[2:] == ['.well-known', 'agent-card.json'] and self.command == 'GET':
                    self.respond(200, peer_service.agent_card(origin, role=role))
                elif parts[2:] == ['message:send'] and self.command == 'POST':
                    if service.state()['paused']:
                        raise MarketError('paused')
                    self.respond(200, peer_service.send(self.body(), role=role))
                elif len(parts) == 4 and parts[2] == 'tasks' and self.command == 'GET':
                    self.respond(200, peer_service.get_task(unquote(parts[3]), role=role))
                else:
                    self.respond(404, {'error': 'not_found'})
                return

            if self.command != 'GET':
                self.respond(405, {'error': 'method_not_allowed'})
                return
            if path.startswith(('/api/market/', '/api/cardmarket/')):
                if not reference_url:
                    self.respond(503, {'error': 'backend_unavailable'})
                    return
                try:
                    with httpx.Client(timeout=12, follow_redirects=False, trust_env=False) as client:
                        with client.stream('GET', reference_url.rstrip('/') + self.path) as response:
                            output = bytearray()
                            for chunk in response.iter_bytes():
                                output.extend(chunk)
                                if len(output) > 2 * 1024 * 1024:
                                    raise ValueError('oversized response')
                            self.respond(response.status_code, raw=bytes(output))
                except Exception:
                    self.respond(502, {'error': 'backend_unavailable'})
                return
            if path.startswith('/api/'):
                self.respond(404, {'error': 'not_found'})
                return
            decoded = unquote(path)
            file = (root / decoded.lstrip('/')).resolve()
            if not file.is_relative_to(root) or any(part.startswith('.') for part in Path(decoded).parts if part not in ('/', '.')):
                self.respond(404, {'error': 'not_found'})
                return
            if path == '/':
                file = root / 'index.html'
            if not file.is_file():
                self.respond(404, {'error': 'not_found'})
                return
            self.respond(200, raw=file.read_bytes(), content_type=mimetypes.guess_type(file)[0] or 'application/octet-stream')

        def handle_request(self):
            try:
                self.dispatch()
            except MarketError as exc:
                self.close_connection = True
                status = 413 if exc.code == 'body_too_large' else (409 if exc.code in ('paused', 'run_failed', 'run_in_progress', 'request_conflict', 'stale_state', 'authority_inactive') else 400)
                self.respond(status, {'error': exc.code})
            except (BrokenPipeError, ConnectionResetError):
                self.close_connection = True
            except Exception:
                self.close_connection = True
                self.respond(503, {'error': 'service_unavailable'})

        def do_GET(self):
            self.handle_request()

        def do_POST(self):
            self.handle_request()

    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.daemon_threads = True
    return server


def initialize_fixture(store, workspace, *, now):
    """Explicitly seed synthetic data once; restart never refreshes stale evidence."""
    from .contracts import FixtureBundle, InventoryBundle
    from .demo import DEMO_TIME

    try:
        store.session(workspace).snapshot()
        return
    except MarketError as exc:
        if exc.code != 'record_not_found':
            raise
    delta = now - DEMO_TIME
    date_fields = {'created_at', 'observed_at', 'reviewed_at', 'expires_at',
                   'acquired_at', 'received_at', 'inspected_at', 'returned_at'}

    def rebase(value):
        if isinstance(value, dict):
            return {key: ((datetime.fromisoformat(item.replace('Z', '+00:00')) + delta).isoformat()
                          if key in date_fields and isinstance(item, str) else rebase(item))
                    for key, item in value.items()}
        if isinstance(value, list):
            return [rebase(item) for item in value]
        return value

    data = rebase(json.loads(files('pokemon_market').joinpath('fixtures/qualified.json').read_text()))
    data['session_id'] = workspace
    inventory = rebase(json.loads(files('pokemon_market').joinpath('fixtures/inventory.json').read_text()))
    store.create(FixtureBundle.model_validate(data), inventory=InventoryBundle.model_validate(inventory))


def serve(args):
    import os
    from .contracts import Request
    from .peer import FixturePeerService, peer_message
    from .storage import PostgresMarketStore
    from .workflow import WorkflowService

    dsn = os.environ.get('MARKET_DATABASE_URL')
    token = os.environ.get('MARKET_OPERATOR_TOKEN', '')
    peer_token = os.environ.get('MARKET_PEER_TOKEN', '')
    if not dsn or len(token) < 32 or len(peer_token) < 32 or token == peer_token:
        raise MarketError('missing_server_configuration')
    store = PostgresMarketStore(dsn)
    if args.initialize_demo:
        store.setup()
        initialize_fixture(store, args.workspace, now=datetime.now(timezone.utc))
    service = WorkflowService(store, args.workspace)
    peer = FixturePeerService(store, args.workspace)
    server = make_server(service, port=args.port, token=token, peer_token=peer_token,
                         dist=args.dist, reference_url=args.reference_url, peer_service=peer)

    def dispatch_fixture(artifact):
        mandate = artifact.mandate
        request = Request(request_id='peer-' + artifact.request_id,
                          operation='negotiate_acquisition', correlation_id=artifact.correlation_id,
                          policy_version=mandate.policy_version,
                          assessment_version=mandate.assessment_version,
                          conversation_version=mandate.conversation_version,
                          expires_at=mandate.expires_at, mandate_id=mandate.id)
        url = f'http://127.0.0.1:{server.server_port}/a2a/sales/message:send'
        try:
            with httpx.Client(timeout=8, trust_env=False, follow_redirects=False) as client:
                response = client.post(url, headers={'Authorization': 'Bearer ' + peer_token},
                                       json=peer_message(request, args.workspace))
        except httpx.HTTPError:
            raise MarketError('fixture_peer_unavailable') from None
        if response.status_code != 200:
            raise MarketError('fixture_peer_unavailable')

    service.peer = dispatch_fixture
    stop = threading.Event()

    def worker():
        while not stop.wait(5):
            try:
                service.run_due()
            except Exception:
                # Job failures remain in private durable run state, never raw logs.
                pass

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    print(f'Private fixture Market UI: http://127.0.0.1:{server.server_port}/', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        server.server_close()
        thread.join(6)
    return 0
