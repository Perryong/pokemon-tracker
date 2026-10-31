"""Evidence completeness regressions. Run only in the isolated trusted runner."""
import json
import unittest

from github_evidence import EvidenceError, FixedEvidenceTransport
from test_github_evidence import REPO, ROOT, fixture, issue, pr_fixture as basic_pr_fixture


CREATED = '2026-10-30T10:00:00Z'
UPDATED = '2026-10-31T10:00:00Z'


def rest_comment(**extra):
    return dict({'id': 6539577837, 'body': 'Retained ownership decision',
                 'user': {'login': 'operator'}, 'created_at': CREATED,
                 'updated_at': UPDATED}, **extra)


def review_record(**extra):
    return dict({'id': 5000000001, 'body': 'Independent finding',
                 'state': 'CHANGES_REQUESTED', 'user': {'login': 'reviewer'},
                 'submitted_at': CREATED}, **extra)


def thread_comment(**extra):
    return dict({'id': 'PRRC_1', 'body': 'Independent thread finding',
                 'author': {'login': 'reviewer'}, 'createdAt': CREATED,
                 'updatedAt': UPDATED}, **extra)


def add_thread_comment(http, record):
    http.routes['https://api.github.com/graphql']['body'] = json.dumps({
        'data': {'repository': {'pullRequest': {'reviewThreads': {
            'nodes': [{'id': 'PRRT_1', 'isResolved': False,
                       'comments': {'nodes': [record], 'pageInfo': {
                           'hasNextPage': False, 'endCursor': None}}}],
            'pageInfo': {'hasNextPage': False, 'endCursor': None}}}}}}).encode()


def pr_fixture():
    http, pr = basic_pr_fixture()
    http.add('/pulls/28/reviews?per_page=100&page=1', [review_record()])
    add_thread_comment(http, thread_comment())
    return http, pr


def dependency_routes(http, n, blocked_by=()):
    http.add('/issues/' + str(n), dict(issue(n), body='Acceptance for ' + str(n)))
    http.add('/issues/' + str(n) + '/comments?per_page=100&page=1',
             [rest_comment(id=10000 + n, body='Owner decision for ' + str(n))])
    http.add('/issues/' + str(n) + '/timeline?per_page=100&page=1',
             [{'id': 20000 + n, 'event': 'closed'}])
    http.add('/issues/' + str(n) + '/dependencies/blocked_by?per_page=100&page=1',
             [issue(other) for other in blocked_by])


class CompletenessTests(unittest.TestCase):
    def test_provenance_timestamps_reject_invalid_offsets(self):
        for suffix in ('+00:60', '+00:99', '-00:99', '+24:00'):
            for target in ('created_at', 'updated_at', 'submitted_at', 'createdAt', 'updatedAt'):
                with self.subTest(suffix=suffix, field=target):
                    http, _ = pr_fixture()
                    value = '2026-10-30T10:00:00' + suffix
                    if target in ('created_at', 'updated_at'):
                        http.add('/issues/27/comments?per_page=100&page=1',
                                 [rest_comment(**{target: value})])
                    elif target == 'submitted_at':
                        http.add('/pulls/28/reviews?per_page=100&page=1',
                                 [review_record(submitted_at=value)])
                    else:
                        add_thread_comment(http, thread_comment(**{target: value}))
                    with self.assertRaises(EvidenceError):
                        FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)

    def test_valid_timezone_offset_is_preserved(self):
        http = fixture()
        value = '2026-10-30T10:00:00+05:30'
        http.add('/issues/27/comments?per_page=100&page=1',
                 [rest_comment(created_at=value, updated_at=value)])
        result = FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)
        self.assertEqual(result['comments'][0]['created_at'], value)
        self.assertEqual(result['comments'][0]['updated_at'], value)

    def test_check_large_database_id_is_preserved(self):
        # Database identifiers are not issue numbers and exceed one billion.
        http, _ = pr_fixture()
        http.add('/commits/' + 'a' * 40 + '/check-runs?per_page=100&page=1',
                 {'total_count': 1, 'check_runs': [{'id': 91000000001,
                  'name': 'offline', 'status': 'completed', 'conclusion': 'success',
                  'head_sha': 'a' * 40}]})
        pr = FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)['pull_requests'][0]
        self.assertEqual(pr['checks'][0]['id'], 91000000001)

    def test_status_large_database_id_is_preserved(self):
        http, _ = pr_fixture()
        http.add('/commits/' + 'a' * 40 + '/statuses?per_page=100&page=1',
                 [{'id': 92000000001, 'state': 'success', 'context': 'offline'}])
        pr = FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)['pull_requests'][0]
        self.assertEqual(pr['statuses'][0]['id'], 92000000001)

    def test_check_database_id_requires_positive_integer(self):
        for invalid in (True, False, 0, -1, '91000000001'):
            with self.subTest(identifier=invalid):
                http, _ = pr_fixture()
                http.add('/commits/' + 'a' * 40 + '/check-runs?per_page=100&page=1',
                         {'total_count': 1, 'check_runs': [{'id': invalid,
                          'name': 'offline', 'status': 'completed', 'conclusion': 'success',
                          'head_sha': 'a' * 40}]})
                with self.assertRaises(EvidenceError):
                    FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)

    def test_status_database_id_requires_positive_integer(self):
        for invalid in (True, False, 0, -1, '92000000001'):
            with self.subTest(identifier=invalid):
                http, _ = pr_fixture()
                http.add('/commits/' + 'a' * 40 + '/statuses?per_page=100&page=1',
                         [{'id': invalid, 'state': 'success', 'context': 'offline'}])
                with self.assertRaises(EvidenceError):
                    FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)

    def test_rest_comments_require_complete_record_provenance(self):
        for number in (27, 28):
            for key, invalids in {
                'id': (None, False, 0, -1, '6539577837'),
                'user': ({}, {'login': None}, {'login': ''}, {'login': False}, 'operator'),
                'created_at': (None, False, 1, '', 'not-a-date'),
                'updated_at': (None, False, 1, '', 'not-a-date'),
            }.items():
                for value in ('MISSING', *invalids):
                    with self.subTest(issue=number, field=key, value=value):
                        http, _ = pr_fixture() if number == 28 else (fixture(), None)
                        raw = rest_comment()
                        if value == 'MISSING':
                            del raw[key]
                        else:
                            raw[key] = value
                        http.add('/issues/' + str(number) + '/comments?per_page=100&page=1', [raw])
                        with self.assertRaises(EvidenceError):
                            FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)

    def test_reviews_require_record_identity_and_submission_provenance(self):
        for key, invalids in {
            'id': (None, False, 0, -1, '5000000001'),
            'user': ({}, {'login': None}, {'login': ''}, {'login': False}, 'reviewer'),
            'submitted_at': (None, False, 1, '', 'not-a-date'),
        }.items():
            for value in ('MISSING', *invalids):
                with self.subTest(field=key, value=value):
                    http, _ = pr_fixture()
                    raw = review_record()
                    if value == 'MISSING':
                        del raw[key]
                    else:
                        raw[key] = value
                    http.add('/pulls/28/reviews?per_page=100&page=1', [raw])
                    with self.assertRaises(EvidenceError):
                        FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)

    def test_pending_review_nullable_submission_time_retains_pending_state(self):
        # GitHub has not submitted a pending review, so its ordering timestamp
        # legitimately remains null; retaining PENDING prevents approval use.
        http, _ = pr_fixture()
        http.add('/pulls/28/reviews?per_page=100&page=1',
                 [review_record(state='PENDING', submitted_at=None)])
        review = FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)['pull_requests'][0]['reviews'][0]
        self.assertEqual(review['state'], 'PENDING')
        self.assertIn('submitted_at', review)
        self.assertIsNone(review['submitted_at'])

    def test_pending_review_still_requires_explicit_submission_field(self):
        http, _ = pr_fixture()
        raw = review_record(state='PENDING', submitted_at=None)
        del raw['submitted_at']
        http.add('/pulls/28/reviews?per_page=100&page=1', [raw])
        with self.assertRaises(EvidenceError):
            FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)

    def test_thread_comments_require_record_identity_and_ordering_provenance(self):
        for key, invalids in {
            'id': (None, False, 1, ''),
            'author': ({}, {'login': None}, {'login': ''}, {'login': False}, 'reviewer'),
            'createdAt': (None, False, 1, '', 'not-a-date'),
            'updatedAt': (None, False, 1, '', 'not-a-date'),
        }.items():
            for value in ('MISSING', *invalids):
                with self.subTest(field=key, value=value):
                    http, _ = pr_fixture()
                    raw = thread_comment()
                    if value == 'MISSING':
                        del raw[key]
                    else:
                        raw[key] = value
                    add_thread_comment(http, raw)
                    with self.assertRaises(EvidenceError):
                        FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)

    def test_valid_provenance_is_retained_for_manual_ownership_decisions(self):
        http, _ = pr_fixture()
        http.add('/issues/27/comments?per_page=100&page=1', [rest_comment()])
        result = FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)
        self.assertEqual(result['comments'][0]['id'], 6539577837)
        self.assertEqual(result['comments'][0]['user'], {'login': 'operator'})
        self.assertEqual(result['comments'][0]['created_at'], CREATED)
        self.assertEqual(result['comments'][0]['updated_at'], UPDATED)
        pr = result['pull_requests'][0]
        self.assertEqual(pr['reviews'][0]['id'], 5000000001)
        self.assertEqual(pr['reviews'][0]['user'], {'login': 'reviewer'})
        self.assertEqual(pr['reviews'][0]['submitted_at'], CREATED)
        record = pr['review_threads'][0]['comments'][0]
        self.assertEqual(record['id'], 'PRRC_1')
        self.assertEqual(record['author'], {'login': 'reviewer'})
        self.assertEqual(record['createdAt'], CREATED)
        self.assertEqual(record['updatedAt'], UPDATED)

    def test_deleted_authors_remain_explicitly_null_and_do_not_gain_identity(self):
        # Evidence projection cannot grant ownership. Preserve a deleted user's
        # explicit null so a consumer cannot mistake it for an accepted actor.
        http, _ = pr_fixture()
        http.add('/issues/27/comments?per_page=100&page=1', [rest_comment(user=None)])
        http.add('/pulls/28/reviews?per_page=100&page=1', [review_record(user=None)])
        add_thread_comment(http, thread_comment(author=None))
        result = FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)
        self.assertIn('user', result['comments'][0])
        self.assertIsNone(result['comments'][0]['user'])
        pr = result['pull_requests'][0]
        self.assertIn('user', pr['reviews'][0])
        self.assertIsNone(pr['reviews'][0]['user'])
        self.assertIn('author', pr['review_threads'][0]['comments'][0])
        self.assertIsNone(pr['review_threads'][0]['comments'][0]['author'])

    def test_missing_or_malformed_ownership_comment_body_refuses(self):
        missing_body = rest_comment(id=4)
        del missing_body['body']
        for raw in (missing_body, rest_comment(id=4, body={}), rest_comment(id=4, body=False)):
            with self.subTest(comment=raw):
                http = fixture()
                http.add('/issues/27/comments?per_page=100&page=1', [raw])
                with self.assertRaises(EvidenceError):
                    FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)

    def test_required_issue_fields_have_endpoint_specific_types(self):
        for name, value in (('body', {}), ('title', False), ('state', []), ('state', 'unknown')):
            with self.subTest(field=name, value=value):
                http = fixture()
                raw = issue()
                raw[name] = value
                http.add('/issues/27', raw)
                with self.assertRaises(EvidenceError):
                    FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)

    def test_nullable_issue_body_is_preserved(self):
        http = fixture()
        http.add('/issues/27', dict(issue(), body=None))
        self.assertIsNone(FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)['issue_record']['body'])

    def test_missing_or_malformed_review_state_and_body_refuse(self):
        missing_state = review_record(id=5, body='Finding')
        del missing_state['state']
        missing_body = review_record(id=5, state='APPROVED')
        del missing_body['body']
        for review in (missing_state, missing_body,
                       review_record(id=5, state=False, body='Finding'),
                       review_record(id=5, state='invented', body='Finding'),
                       review_record(id=5, state='COMMENTED', body={})):
            with self.subTest(review=review):
                http, _ = pr_fixture()
                http.add('/pulls/28/reviews?per_page=100&page=1', [review])
                with self.assertRaises(EvidenceError):
                    FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)

    def test_check_requires_status_conclusion_and_exact_queried_head(self):
        complete = {'id': 6, 'name': 'offline', 'status': 'completed',
                    'conclusion': 'success', 'head_sha': 'a' * 40}
        cases = []
        for missing in ('status', 'conclusion', 'head_sha'):
            raw = dict(complete)
            del raw[missing]
            cases.append(raw)
        for key, value in (('status', False), ('status', 'invented'), ('conclusion', {}),
                           ('conclusion', 'invented'), ('head_sha', 'c' * 40), ('head_sha', False)):
            cases.append(dict(complete, **{key: value}))
        for raw in cases:
            with self.subTest(check=raw):
                http, _ = pr_fixture()
                http.add('/commits/' + 'a' * 40 + '/check-runs?per_page=100&page=1',
                         {'total_count': 1, 'check_runs': [raw]})
                with self.assertRaises(EvidenceError):
                    FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)

    def test_pending_check_nullable_conclusion_is_preserved(self):
        http, _ = pr_fixture()
        http.add('/commits/' + 'a' * 40 + '/check-runs?per_page=100&page=1',
                 {'total_count': 1, 'check_runs': [{'id': 6, 'name': 'offline',
                   'status': 'in_progress', 'conclusion': None, 'head_sha': 'a' * 40}]})
        check = FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)['pull_requests'][0]['checks'][0]
        self.assertIsNone(check['conclusion'])
        self.assertEqual(check['status'], 'in_progress')

    def test_missing_required_issue_fields_refuses_incomplete_contract(self):
        for missing in ('number', 'title', 'body', 'state', 'html_url'):
            with self.subTest(missing=missing):
                http = fixture()
                raw = issue()
                del raw[missing]
                http.add('/issues/27', raw)
                with self.assertRaises(EvidenceError):
                    FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)

    def test_missing_dependency_body_refuses_entire_snapshot(self):
        http = fixture()
        http.add('/issues/27/dependencies/blocked_by?per_page=100&page=1', [issue(8)])
        dependency_routes(http, 8)
        raw = issue(8)
        del raw['body']
        http.add('/issues/8', raw)
        with self.assertRaises(EvidenceError):
            FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)

    def test_pr_ordinary_comments_and_timeline_preserve_operator_blockers(self):
        http, _ = pr_fixture()
        http.add('/issues/28/comments?per_page=100&page=1',
                 [rest_comment(id=31, body='Operator: stop integration; blocker remains')])
        http.add('/issues/28/timeline?per_page=100&page=1',
                 [{'id': 32, 'event': 'labeled', 'label': {'id': 7, 'name': 'blocked'}}])
        result = FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)
        pr = result['pull_requests'][0]
        self.assertEqual(pr['comments'][0]['body'], 'Operator: stop integration; blocker remains')
        self.assertEqual(pr['timeline'][0]['label']['name'], 'blocked')
        self.assertEqual(pr['issue_record']['body'], 'Complete acceptance text')

    def test_inaccessible_pr_conversation_refuses_entire_snapshot(self):
        http, _ = pr_fixture()
        http.add('/issues/28/comments?per_page=100&page=1', {'message': 'SECRET'}, status=403)
        with self.assertRaises(EvidenceError) as caught:
            FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)
        self.assertNotIn('SECRET', str(caught.exception))

    def test_nested_prerequisite_edges_and_full_issue_history_are_retained(self):
        http = fixture()
        http.add('/issues/27/dependencies/blocked_by?per_page=100&page=1', [issue(8)])
        dependency_routes(http, 8, [9])
        dependency_routes(http, 9)
        result = FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)
        self.assertEqual(result['blocked_by'], [8])
        dependencies = {entry['issue']: entry for entry in result['dependencies']}
        self.assertEqual(set(dependencies), {8, 9})
        self.assertEqual(dependencies[8]['blocked_by'], [9])
        self.assertEqual(dependencies[9]['blocked_by'], [])
        self.assertEqual(dependencies[9]['issue_record']['body'], 'Acceptance for 9')
        self.assertEqual(dependencies[9]['comments'][0]['body'], 'Owner decision for 9')
        self.assertEqual(dependencies[9]['timeline'][0]['event'], 'closed')

    def test_shared_prerequisite_is_deduplicated_without_losing_edges(self):
        http = fixture()
        http.add('/issues/27/dependencies/blocked_by?per_page=100&page=1', [issue(8), issue(9)])
        dependency_routes(http, 8, [11])
        dependency_routes(http, 9, [11])
        dependency_routes(http, 11)
        result = FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)
        dependencies = {entry['issue']: entry for entry in result['dependencies']}
        self.assertEqual(len(result['dependencies']), 3)
        self.assertEqual(dependencies[8]['blocked_by'], [11])
        self.assertEqual(dependencies[9]['blocked_by'], [11])

    def test_dependency_cycle_fails_closed(self):
        http = fixture()
        http.add('/issues/27/dependencies/blocked_by?per_page=100&page=1', [issue(8)])
        dependency_routes(http, 8, [9])
        dependency_routes(http, 9, [8])
        with self.assertRaises(EvidenceError):
            FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)

    def test_nested_private_prerequisite_fails_without_private_disclosure(self):
        http = fixture()
        http.add('/issues/27/dependencies/blocked_by?per_page=100&page=1', [issue(8)])
        dependency_routes(http, 8)
        http.add('/issues/8/dependencies/blocked_by?per_page=100&page=1',
                 [dict(issue(9), html_url='https://github.com/private/SECRET/issues/9')])
        with self.assertRaises(EvidenceError) as caught:
            FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)
        self.assertNotIn('SECRET', str(caught.exception))
        self.assertFalse(any('private' in call[1] for call in http.calls))

    def test_dependency_graph_budget_fails_without_partial_snapshot(self):
        http = fixture()
        http.add('/issues/27/dependencies/blocked_by?per_page=100&page=1', [issue(100)])
        for n in range(100, 166):
            dependency_routes(http, n, [n + 1] if n < 165 else [])
        with self.assertRaises(EvidenceError):
            FixedEvidenceTransport(http, [27]).snapshot(REPO, 27)


if __name__ == '__main__':
    unittest.main()
