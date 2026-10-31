"""Offline contract for fixed public evidence acquisition; never contacts GitHub."""
import copy
import json
import unittest

try:
    from github_evidence import EvidenceError, FixedEvidenceTransport
except ModuleNotFoundError as exc:
    if exc.name != 'github_evidence':
        raise
    EvidenceError, FixedEvidenceTransport = ValueError, None


REPO = 'Perryong/pokemon-tracker'
ROOT = 'https://api.github.com/repos/' + REPO


def comment_record(**extra):
    return dict({'id': 1, 'body': 'Comment', 'user': {'login': 'operator'},
                 'created_at': '2026-10-30T10:00:00Z',
                 'updated_at': '2026-10-31T10:00:00Z'}, **extra)


class HTTP:
    def __init__(self):
        self.routes = {}
        self.calls = []

    def add(self, path, value, status=200, headers=None):
        self.routes[ROOT + path] = dict(status=status, headers=headers or {},
                                       body=json.dumps(value).encode())

    def request(self, method, url, headers, body=None):
        self.calls.append((method, url, headers, body))
        if url not in self.routes:
            raise RuntimeError('SECRET unknown URL')
        return copy.deepcopy(self.routes[url])


def issue(number=27, **extra):
    return dict(number=number, title='Public issue', body='Complete acceptance text',
                state='open', html_url='https://github.com/' + REPO + '/issues/' + str(number),
                user={'login': 'operator'}, labels=[], assignees=[], **extra)


def fixture():
    http = HTTP()
    http.add('', {'full_name': REPO, 'private': False, 'visibility': 'public'})
    http.add('/issues/27', issue())
    for suffix in ('comments', 'timeline', 'dependencies/blocked_by'):
        http.add('/issues/27/' + suffix + '?per_page=100&page=1', [])
    return http


def pr_fixture():
    http = fixture()
    http.add('/issues/27/timeline?per_page=100&page=1', [{'event': 'cross-referenced',
             'source': {'issue': dict(issue(28), pull_request={},
                        repository={'full_name': REPO, 'private': False})}}])
    pr = dict(number=28, title='Security', body='Review this', state='open',
              base={'ref': 'feature/sales-agent', 'sha': 'b' * 40, 'repo': {'full_name': REPO}},
              head={'ref': 'security', 'sha': 'a' * 40})
    http.add('/pulls/28', pr)
    http.add('/issues/28', dict(issue(28), pull_request={}))
    http.add('/issues/28/comments?per_page=100&page=1', [])
    http.add('/issues/28/timeline?per_page=100&page=1', [])
    http.add('/issues/28/dependencies/blocked_by?per_page=100&page=1', [])
    http.add('/pulls/28/reviews?per_page=100&page=1',
             [{'id': 5, 'state': 'CHANGES_REQUESTED', 'body': 'Fix boundary',
               'user': {'login': 'reviewer'}, 'submitted_at': '2026-10-30T10:00:00Z'}])
    http.add('/commits/' + 'a' * 40 + '/check-runs?per_page=100&page=1',
             {'total_count': 1, 'check_runs': [{'id': 6, 'name': 'offline', 'status': 'completed',
                                             'conclusion': 'success', 'head_sha': 'a' * 40}]})
    http.add('/commits/' + 'a' * 40 + '/statuses?per_page=100&page=1', [])
    http.routes['https://api.github.com/graphql'] = dict(status=200, headers={}, body=json.dumps({
        'data': {'repository': {'pullRequest': {'reviewThreads': {'nodes': [{
            'id': 'PRRT_1', 'isResolved': False, 'comments': {'nodes': [
                {'id': 'PRRC_1', 'body': 'Unresolved finding', 'author': {'login': 'reviewer'},
                 'createdAt': '2026-10-30T10:00:00Z', 'updatedAt': '2026-10-31T10:00:00Z'}],
                'pageInfo': {'hasNextPage': False, 'endCursor': None}}}],
            'pageInfo': {'hasNextPage': False, 'endCursor': None}}}}}}).encode())
    return http, pr


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(FixedEvidenceTransport, 'github_evidence implementation is missing (expected RED)')

    def test_issue_without_pr_has_readable_complete_evidence(self):
        http = fixture()
        http.add('/issues/27/comments?per_page=100&page=1',
                 [comment_record(body='Retained ownership')])
        result = FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)
        self.assertEqual(result['issue_record']['body'], 'Complete acceptance text')
        self.assertEqual(result['comments'][0]['body'], 'Retained ownership')
        self.assertEqual(result['pull_requests'], [])
        self.assertEqual(result['dependencies'], [])
        self.assertEqual(result['visibility'], 'public')

    def test_scope_denied_before_http(self):
        http = fixture()
        transport = FixedEvidenceTransport(http, [27])
        for repo, number in [(REPO, 24), ('private/repo', 27), (REPO, True), (REPO, '27')]:
            with self.assertRaises(EvidenceError):
                transport.snapshot(repo, number)
        self.assertEqual(http.calls, [])

    def test_native_dependency_fetches_full_body(self):
        http = fixture()
        http.add('/issues/27/dependencies/blocked_by?per_page=100&page=1', [issue(8)])
        http.add('/issues/8', issue(8))
        http.add('/issues/8/comments?per_page=100&page=1', [comment_record(id=4, body='Dependency acceptance')])
        http.add('/issues/8/timeline?per_page=100&page=1', [{'id': 5, 'event': 'closed'}])
        http.add('/issues/8/dependencies/blocked_by?per_page=100&page=1', [])
        result = FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)
        self.assertEqual(result['dependencies'][0]['issue_record']['body'], 'Complete acceptance text')
        self.assertEqual(result['dependencies'][0]['comments'][0]['body'], 'Dependency acceptance')
        self.assertEqual(result['dependencies'][0]['timeline'][0]['event'], 'closed')
        self.assertTrue(any(call[1].endswith('/issues/8') for call in http.calls))

    def test_foreign_dependency_fails_closed_without_private_text(self):
        http = fixture()
        http.add('/issues/27/dependencies/blocked_by?per_page=100&page=1',
                 [dict(issue(8), html_url='https://github.com/private/SECRET/issues/8')])
        with self.assertRaises(EvidenceError) as caught:
            FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)
        self.assertNotIn('SECRET', str(caught.exception))
        self.assertFalse(any('private' in call[1] for call in http.calls))

    def test_pagination_uses_fixed_next_page_and_returns_all_comments(self):
        http = fixture()
        first = [comment_record(id=n + 1, body=str(n)) for n in range(100)]
        http.add('/issues/27/comments?per_page=100&page=1', first)
        http.add('/issues/27/comments?per_page=100&page=2',
                 [comment_record(id=101, body='last')])
        result = FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)
        self.assertEqual(len(result['comments']), 101)
        self.assertEqual(result['comments'][-1]['body'], 'last')

    def test_cross_reference_private_source_is_removed(self):
        http = fixture()
        http.add('/issues/27/timeline?per_page=100&page=1',
                 [{'id': 9, 'event': 'cross-referenced', 'source': {'issue':
                   {'number': 4, 'title': 'SECRET', 'repository': {'full_name': 'private/SECRET', 'private': True}}}}])
        result = FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)
        self.assertNotIn('SECRET', json.dumps(result))

    def test_redirect_and_raw_transport_failures_are_sanitized(self):
        for status in (302, 403, 500):
            http = fixture()
            http.add('', {'SECRET': 'token'}, status, {'Location': 'https://private/SECRET'})
            with self.assertRaises(EvidenceError) as caught:
                FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)
            self.assertNotIn('SECRET', str(caught.exception))
            self.assertEqual(len(http.calls), 1)

    def test_nonpublic_repo_denied_and_unrecognized_fields_not_returned(self):
        http = fixture()
        http.add('', {'full_name': REPO, 'private': True, 'visibility': 'private'})
        with self.assertRaises(EvidenceError):
            FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)
        http = fixture()
        http.add('/issues/27', dict(issue(), secret='SECRET'))
        self.assertNotIn('SECRET', json.dumps(FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)))

    def test_pr_reviews_threads_and_checks_are_required(self):
        http = fixture()
        http.add('/issues/27/timeline?per_page=100&page=1', [{'event': 'cross-referenced',
                 'source': {'issue': dict(issue(28), pull_request={},
                            repository={'full_name': REPO, 'private': False})}}])
        # Missing any required PR evidence must fail, never produce a partial snapshot.
        with self.assertRaises(EvidenceError):
            FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)

    def test_successful_pr_has_exact_revisions_reviews_threads_and_checks(self):
        http, _ = pr_fixture()
        pr = FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)['pull_requests'][0]
        self.assertEqual(pr['base_sha'], 'b' * 40)
        self.assertEqual(pr['head_sha'], 'a' * 40)
        self.assertEqual(pr['reviews'][0]['body'], 'Fix boundary')
        self.assertEqual(pr['review_threads'][0]['comments'][0]['body'], 'Unresolved finding')
        self.assertFalse(pr['review_threads'][0]['isResolved'])
        self.assertEqual(pr['checks'][0]['conclusion'], 'success')

    def test_missing_graphql_page_info_and_errors_fail_closed(self):
        for bad in ({'data': {'repository': {'pullRequest': {'reviewThreads': {'nodes': []}}}}},
                    {'errors': [{'message': 'SECRET'}], 'data': None}):
            http, _ = pr_fixture()
            http.routes['https://api.github.com/graphql']['body'] = json.dumps(bad).encode()
            with self.assertRaises(EvidenceError):
                FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)

    def test_duplicate_keys_and_nan_fail_closed(self):
        for body in (b'{"full_name":"Perryong/pokemon-tracker","private":true,"private":false,"visibility":"public"}',
                     b'{"full_name":"Perryong/pokemon-tracker","private":false,"visibility":"public","x":NaN}'):
            http = fixture()
            http.routes[ROOT]['body'] = body
            with self.assertRaises(EvidenceError):
                FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)

    def test_pr_head_movement_during_evidence_acquisition_fails_closed(self):
        http, pr = pr_fixture()
        original = http.request
        count = []
        def moving(method, url, headers, body=None):
            if url == ROOT + '/pulls/28':
                count.append(1)
                if len(count) == 2:
                    http.add('/pulls/28', dict(pr, head={'ref': 'security', 'sha': 'c' * 40}))
            return original(method, url, headers, body)
        http.request = moving
        with self.assertRaises(EvidenceError):
            FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)

    def test_response_size_and_page_budget_fail_closed(self):
        http = fixture()
        http.routes[ROOT]['body'] = b' ' * (2 * 1024 * 1024 + 1)
        with self.assertRaises(EvidenceError):
            FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)
        http = fixture()
        for page in range(1, 22):
            http.add('/issues/27/comments?per_page=100&page=' + str(page),
                     [comment_record(id=page * 100 + n, body='x') for n in range(100)])
        with self.assertRaises(EvidenceError):
            FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)


if __name__ == '__main__':
    unittest.main()
