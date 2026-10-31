"""Offline host HTTP boundary tests; parent runs these only in isolated checks."""
import json
import os
import unittest
from unittest.mock import patch

from github_evidence import (COMMENTS_QUERY, HEADERS, MAX_RESPONSE, THREADS_QUERY,
                             FixedEvidenceTransport)

try:
    import github_transport
except ModuleNotFoundError as exc:
    if exc.name != 'github_transport':
        raise
    github_transport = None


ROOT = 'https://api.github.com/repos/Perryong/pokemon-tracker'
GRAPHQL = 'https://api.github.com/graphql'
TOKEN = 'synthetic-host-only-token'


class Response:
    def __init__(self, body=b'{}', status=200, headers=()):
        self.body, self.status, self.headers = body, status, headers
        self.read_sizes = []

    def read(self, size):
        self.read_sizes.append(size)
        return self.body[:size]

    def getheaders(self):
        return list(self.headers)


class Wire:
    """Only replace the external socket boundary; exercise all client policy."""
    def __init__(self, responses):
        self.responses = list(responses)
        self.connections, self.requests, self.closed = [], [], 0

    def connect(self, host, **kwargs):
        self.connections.append((host, kwargs))
        wire = self

        class Connection:
            def request(self, method, path, body=None, headers=None):
                wire.requests.append((method, path, body, headers))

            def getresponse(self):
                value = wire.responses.pop(0)
                if isinstance(value, Exception):
                    raise value
                return value

            def close(self):
                wire.closed += 1

        return Connection()


class TransportTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(github_transport,
                             'fixed host HTTPS transport missing (expected RED)')

    def client(self, wire):
        patcher = patch('github_transport.http.client.HTTPSConnection', wire.connect)
        patcher.start()
        self.addCleanup(patcher.stop)
        return github_transport.FixedGitHubHTTP(TOKEN)

    def query(self, query=THREADS_QUERY, variables=None):
        return json.dumps({'query': query, 'variables': variables or
                           {'number': 28, 'cursor': None}}).encode()

    def test_fixed_tls_origin_auth_timeout_and_bounded_read(self):
        response = Response(b'{"ok":true}')
        wire = Wire([response])
        client = self.client(wire)
        with patch.dict(os.environ, {'HTTPS_PROXY': 'https://attacker.invalid',
                                     'ALL_PROXY': 'https://attacker.invalid'}):
            result = client.request('GET', ROOT, dict(HEADERS))
        self.assertEqual(result, {'status': 200, 'headers': {}, 'body': b'{"ok":true}'})
        self.assertEqual(wire.connections[0][0], 'api.github.com')
        self.assertGreater(wire.connections[0][1]['timeout'], 0)
        self.assertLessEqual(wire.connections[0][1]['timeout'], 30)
        context = wire.connections[0][1]['context']
        self.assertTrue(context.check_hostname)
        self.assertEqual(context.verify_mode, 2)
        method, path, body, headers = wire.requests[0]
        self.assertEqual((method, path, body), ('GET', '/repos/Perryong/pokemon-tracker', None))
        self.assertEqual(headers['Authorization'], 'Bearer ' + TOKEN)
        self.assertEqual(response.read_sizes, [MAX_RESPONSE + 1])
        self.assertEqual(wire.closed, 1)
        self.assertNotIn(TOKEN, repr(client))

    def test_arbitrary_origins_paths_headers_methods_rejected_before_network(self):
        wire = Wire([])
        client = self.client(wire)
        cases = [
            ('GET', 'http://api.github.com/repos/Perryong/pokemon-tracker', HEADERS, None),
            ('GET', ROOT.replace('api.github.com', 'api.github.com.evil.invalid'), HEADERS, None),
            ('GET', ROOT.replace('api.github.com', 'token@api.github.com'), HEADERS, None),
            ('GET', ROOT.replace('api.github.com', 'api.github.com:443'), HEADERS, None),
            ('GET', ROOT + '#fragment', HEADERS, None),
            ('GET', ROOT + '/../../private/repo', HEADERS, None),
            ('GET', ROOT + '/issues/%32%37', HEADERS, None),
            ('GET', ROOT + '/issues/27?access_token=secret', HEADERS, None),
            ('GET', ROOT + '/issues/27/comments?per_page=100&page=21', HEADERS, None),
            ('GET', ROOT + '/contents/secret', HEADERS, None),
            ('DELETE', ROOT + '/issues/27', HEADERS, None),
            ('POST', ROOT + '/issues/27/comments', HEADERS, b'{}'),
            ('GET', ROOT, dict(HEADERS, Authorization='host-token'), None),
            ('GET', ROOT, dict(HEADERS, Host='attacker.invalid'), None),
            ('GET', ROOT, HEADERS, b'{}'),
        ]
        for args in cases:
            with self.subTest(args=args), self.assertRaises(ValueError):
                client.request(*args)
        self.assertEqual(wire.connections, [])

    def test_only_evidence_rest_routes_and_canonical_pagination(self):
        paths = ['', '/issues/27', '/pulls/28',
                 '/issues/8/comments?per_page=100&page=1',
                 '/issues/27/timeline?per_page=100&page=20',
                 '/issues/27/dependencies/blocked_by?per_page=100&page=1',
                 '/pulls/28/reviews?per_page=100&page=1',
                 '/commits/' + 'a' * 40 + '/check-runs?per_page=100&page=1',
                 '/commits/' + 'b' * 40 + '/statuses?per_page=100&page=1']
        wire = Wire([Response() for _ in paths])
        client = self.client(wire)
        for path in paths:
            self.assertEqual(client.request('GET', ROOT + path, dict(HEADERS))['status'], 200)
        self.assertEqual(len(wire.requests), len(paths))

    def test_redirect_status_oversize_and_socket_errors_do_not_reflect_secrets(self):
        for response in [Response(b'SECRET ' + TOKEN.encode(), 302,
                                  [('Location', 'https://attacker.invalid')]),
                         Response(TOKEN.encode(), 403),
                         Response(b'x' * (MAX_RESPONSE + 1)),
                         OSError(TOKEN + ' SECRET')]:
            wire = Wire([response])
            client = self.client(wire)
            with self.assertRaises(ValueError) as caught:
                client.request('GET', ROOT, dict(HEADERS))
            self.assertNotIn(TOKEN, str(caught.exception))
            self.assertNotIn('SECRET', str(caught.exception))
            self.assertTrue(caught.exception.__suppress_context__)
            self.assertEqual(len(wire.requests), 1)
            self.assertEqual(wire.closed, 1)

    def test_graphql_only_fixed_queries_and_validated_variables(self):
        wire = Wire([Response()])
        client = self.client(wire)
        client.request('POST', GRAPHQL, dict(HEADERS), self.query())
        self.assertEqual(wire.requests[0][0:2], ('POST', '/graphql'))
        bad = [self.query('mutation { deleteRepository }'),
               self.query(variables={'number': True, 'cursor': None}),
               self.query(variables={'number': 28, 'cursor': None, 'repo': 'private'}),
               self.query(variables={'number': 28, 'cursor': 'x' * 513}),
               b'{"query":"x","query":"y","variables":{}}', b'{}']
        for body in bad:
            with self.assertRaises(ValueError):
                client.request('POST', GRAPHQL, dict(HEADERS), body)
        with self.assertRaises(ValueError):
            client.request('GET', GRAPHQL, dict(HEADERS))
        self.assertEqual(len(wire.requests), 1)

    def test_graphql_node_query_requires_thread_observed_from_scoped_pr_query(self):
        body = json.dumps({'data': {'repository': {'pullRequest': {
            'reviewThreads': {'nodes': [{'id': 'PRRT_public'}]}}}}}).encode()
        wire = Wire([Response(body), Response()])
        client = self.client(wire)
        node = self.query(COMMENTS_QUERY, {'id': 'PRRT_public', 'cursor': 'next'})
        with self.assertRaises(ValueError):
            client.request('POST', GRAPHQL, dict(HEADERS), node)
        client.request('POST', GRAPHQL, dict(HEADERS), self.query())
        client.request('POST', GRAPHQL, dict(HEADERS), node)
        with self.assertRaises(ValueError):
            client.request('POST', GRAPHQL, dict(HEADERS), self.query(
                COMMENTS_QUERY, {'id': 'PRRT_private', 'cursor': 'next'}))
        self.assertEqual(len(wire.requests), 2)

    def test_existing_fixed_evidence_transport_uses_real_http_client(self):
        repo = {'full_name': 'Perryong/pokemon-tracker', 'private': False, 'visibility': 'public'}
        issue = {'number': 27, 'title': 'Control', 'body': 'Public contract', 'state': 'open',
                 'html_url': 'https://github.com/Perryong/pokemon-tracker/issues/27',
                 'labels': [], 'assignees': []}
        values = [repo, issue, [], [], [], repo]
        wire = Wire([Response(json.dumps(value).encode()) for value in values])
        result = FixedEvidenceTransport(self.client(wire), [27]).snapshot('Perryong/pokemon-tracker', 27)
        self.assertEqual(result['issue_record']['body'], 'Public contract')
        self.assertEqual(result['visibility'], 'public')
        self.assertNotIn(TOKEN, json.dumps(result))

    def test_invalid_credentials_refused_without_network(self):
        wire = Wire([])
        self.client(wire)
        for token in ('', 'bad\r\nHeader: injected', None, b'token'):
            with self.assertRaises(ValueError):
                github_transport.FixedGitHubHTTP(token)
        self.assertEqual(wire.connections, [])


if __name__ == '__main__':
    unittest.main()
