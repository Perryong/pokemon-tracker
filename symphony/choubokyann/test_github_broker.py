"""Behavior contract for the trusted host broker; run only in isolated checks.

External GitHub I/O is replaced. Validation, durable state and locking stay real.
Absence of the implementation deliberately fails rather than skipping tests.
"""
import copy
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

try:
    import github_broker
except ModuleNotFoundError as exc:
    if exc.name != 'github_broker':
        raise
    github_broker = None


REPO = 'Perryong/pokemon-tracker'
HEAD = 'a' * 40
BASE = 'b' * 40


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


class FakeTransport:
    """Trusted host's remote boundary, with complete broker snapshot shape."""
    def __init__(self):
        self.current = {
            'repo': REPO, 'visibility': 'public', 'issue': 27,
            'authority_digest': '1' * 64, 'claim_digest': '2' * 64,
            'dependency_digest': '3' * 64, 'review_digest': '4' * 64,
            'checks_digest': '5' * 64,
            'pr': {'number': 28, 'base': 'feature/sales-agent',
                   'base_sha': BASE, 'head_sha': HEAD},
        }
        self.writes = []
        self.fail_write = False
        self.interrupt_write = False
        self.guard_available = True
        self.guard_granted = True
        self.guard_held = False
        self.guard_mutation = None
        self.events = []

    def snapshot(self, repo, issue):
        if (repo, issue) != (REPO, 27):
            raise AssertionError('broker crossed configured remote scope')
        self.events.append(('snapshot', self.guard_held))
        return copy.deepcopy(self.current)

    @contextmanager
    def integration_guard(self, repo, branch, expected_base):
        if (repo, branch, expected_base) != (REPO, 'feature/sales-agent', BASE):
            raise AssertionError('guard scope differs from expected integration revision')
        if not self.guard_available:
            raise RuntimeError('enforceable remote integration guard is unavailable')
        self.events.append(('guard-enter', self.guard_granted))
        self.guard_held = self.guard_granted
        try:
            if self.guard_mutation:
                self.current.update(self.guard_mutation)
            yield self.guard_granted
        finally:
            self.guard_held = False
            self.events.append(('guard-exit', False))

    def perform(self, operation, repo, arguments):
        if operation == 'merge' and not self.guard_held:
            raise AssertionError('merge performed outside enforceable integration guard')
        self.events.append(('perform', self.guard_held))
        self.writes.append((operation, repo, copy.deepcopy(arguments)))
        if self.interrupt_write:
            raise KeyboardInterrupt('host interrupted after intent persisted')
        if self.fail_write:
            raise TimeoutError('remote may have applied write')
        return {'number': 28, 'url': 'https://github.com/Perryong/pokemon-tracker/pull/28',
                'token': 'SENTINEL-MUST-NOT-RETURN', 'stdout': 'untrusted raw output'}


class BrokerContract(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(github_broker, 'github_broker implementation is missing (expected RED)')
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.transport = FakeTransport()
        self.policy = {
            'project': 'pokemon', 'repo': REPO,
            'selected_issues': [8, 9, *range(11, 22), 27],
            'integration_branch': 'feature/sales-agent',
            'parent_session': 'symphony-coordinator-27-20261030',
            # Test-host fixture represents separately verified guard support.
            # Omission or false must leave production merge disabled.
            'merge_enabled': True,
            'receipts': {},
        }

    def broker(self):
        return github_broker.Broker(self.policy, Path(self.directory.name), self.transport)

    def request(self, operation='snapshot', arguments=None, request_id='request-001'):
        return {'version': 1, 'request_id': request_id, 'project': 'pokemon',
                'operation': operation, 'arguments': arguments or {'issue': 27},
                'approval_id': None}

    def approved(self, operation='merge', arguments=None):
        request = self.request(operation, arguments or {
            'issue': 27, 'pr': 28, 'base': 'feature/sales-agent',
            'head_sha': HEAD, 'base_sha': BASE})
        unsigned = copy.deepcopy(request)
        self.policy['receipts']['host-approval-001'] = {
            'request_sha256': digest(unsigned),
            'snapshot_sha256': digest(self.transport.current),
            'parent_session': self.policy['parent_session'],
        }
        request['approval_id'] = 'host-approval-001'
        return request

    def denied(self, request):
        with self.assertRaises(github_broker.BrokerError):
            self.broker().execute(request)
        self.assertEqual([], self.transport.writes)

    def test_snapshot_uses_host_bound_repository_and_selected_issue(self):
        result = self.broker().execute(self.request())
        self.assertEqual('completed', result['status'])
        self.assertEqual(REPO, result['snapshot']['repo'])
        self.assertEqual(27, result['snapshot']['issue'])
        self.assertEqual([], self.transport.writes)

    def test_malformed_envelopes_never_reach_remote_write(self):
        for change in ({'version': True}, {'project': 'other'}, {'request_id': '../escape'},
                       {'operation': 'graphql'}, {'url': 'https://api.github.com/user'},
                       {'command': 'gh auth token'}, {'approved': True}):
            with self.subTest(change=change):
                request = self.request()
                request.update(change)
                self.denied(request)
        self.denied([])

    def test_unsupported_operations_and_argument_overrides_are_refused(self):
        for operation in ('shell', 'graphql', 'http', 'auth', 'force_merge', 'project_edit',
                          'issue_close', 'label', 'workflow_dispatch', 'approve_review'):
            with self.subTest(operation=operation):
                self.denied(self.request(operation))
        for args in ({'issue': 27, 'repo': 'private/secret'},
                     {'issue': 27, 'url': 'https://example.org'},
                     {'issue': 27, 'query': '{viewer{login}}'},
                     {'issue': 27, 'fields': ['token']}, {'issue': True}):
            with self.subTest(args=args):
                self.denied(self.request(arguments=args))

    def test_excluded_market_and_unselected_issues_are_refused(self):
        for issue in (1, 10, 24, 26, *range(31, 42), 999):
            with self.subTest(issue=issue):
                self.denied(self.request(arguments={'issue': issue}))

    def test_private_or_mismatched_live_snapshot_fails_closed(self):
        for key, value in (('visibility', 'private'), ('repo', 'someone/else'), ('issue', 24)):
            with self.subTest(key=key):
                original = copy.deepcopy(self.transport.current)
                self.transport.current[key] = value
                self.denied(self.request())
                self.transport.current = original

    def test_missing_receipt_and_agent_assertions_never_authorize_writes(self):
        self.denied(self.request('comment', {'issue': 27, 'body': 'progress'}))
        request = self.approved()
        request['approval_id'] = 'agent-invented'
        self.denied(request)
        request = self.approved()
        request['arguments']['checks_passed'] = True
        self.denied(request)

    def test_exact_host_receipt_permits_only_its_bound_merge(self):
        request = self.approved()
        result = self.broker().execute(request)
        self.assertEqual('completed', result['status'])
        self.assertEqual([('merge', REPO, request['arguments'])], self.transport.writes)
        self.assertNotIn('SENTINEL', json.dumps(result))
        self.assertNotIn('stdout', json.dumps(result))
        self.assertEqual(('guard-exit', False), self.transport.events[-1])
        self.assertIn(('snapshot', True), self.transport.events)
        self.assertEqual(('snapshot', True), self.transport.events[-3])
        self.assertEqual(('perform', True), self.transport.events[-2])
        self.assertFalse(self.transport.guard_held)

    def test_merge_is_disabled_without_explicit_trusted_host_enablement(self):
        for enabled in (None, False, 'true', 1):
            with self.subTest(enabled=enabled):
                if enabled is None:
                    self.policy.pop('merge_enabled', None)
                else:
                    self.policy['merge_enabled'] = enabled
                self.denied(self.approved())

    def test_agent_request_cannot_enable_merge(self):
        self.policy['merge_enabled'] = False
        request = self.approved()
        request['merge_enabled'] = True
        self.denied(request)

    def test_missing_false_or_unavailable_integration_guard_denies_merge(self):
        original_guard = self.transport.integration_guard
        for condition in ('missing', 'false', 'unavailable'):
            with self.subTest(condition=condition):
                self.transport.integration_guard = original_guard
                self.transport.guard_granted = True
                self.transport.guard_available = True
                if condition == 'missing':
                    self.transport.integration_guard = None
                elif condition == 'false':
                    self.transport.guard_granted = False
                else:
                    self.transport.guard_available = False
                self.denied(self.approved())
                self.assertFalse(self.transport.guard_held)

    def test_evidence_changed_during_guard_acquisition_denies_merge(self):
        request = self.approved()
        self.transport.guard_mutation = {'authority_digest': 'e' * 64}
        self.denied(request)
        self.assertIn(('snapshot', True), self.transport.events)
        self.assertEqual(('guard-exit', False), self.transport.events[-1])
        self.assertFalse(self.transport.guard_held)

    def test_guard_cannot_suppress_refusal_and_fall_through_to_unguarded_merge(self):
        @contextmanager
        def suppressing_guard(repo, branch, expected_base):
            try:
                yield False
            except github_broker.BrokerError:
                # A buggy trusted guard must not turn refused acquisition into
                # a second merge dispatch after the with statement exits.
                pass

        self.transport.integration_guard = suppressing_guard
        self.denied(self.approved())

    def test_fixed_host_ledger_capacity_blocks_new_ids_but_preserves_exact_replay(self):
        first_request = self.request(request_id='capacity-000')
        first_result = self.broker().execute(first_request)
        for index in range(1, 256):
            result = self.broker().execute(self.request(request_id=f'capacity-{index:03d}'))
            self.assertEqual('completed', result['status'])
        self.assertEqual(256, len(list(Path(self.directory.name).glob('*.json'))))
        self.denied(self.request(request_id='capacity-overflow'))
        write = self.approved('comment', {'issue': 27, 'body': 'otherwise authorized'})
        write['request_id'] = 'capacity-write-overflow'
        self.policy['receipts']['host-approval-001']['request_sha256'] = digest(dict(write, approval_id=None))
        self.denied(write)
        self.assertEqual(first_result, self.broker().execute(first_request))
        self.assertEqual(256, len(list(Path(self.directory.name).glob('*.json'))))

    def test_changed_current_evidence_invalidates_host_receipt(self):
        for key in ('authority_digest', 'claim_digest', 'dependency_digest',
                    'review_digest', 'checks_digest'):
            with self.subTest(key=key):
                original = copy.deepcopy(self.transport.current)
                request = self.approved()
                self.transport.current[key] = 'f' * 64
                self.denied(request)
                self.transport.current = original

    def test_stale_head_base_and_wrong_pr_are_refused_even_with_new_receipt(self):
        for key, value in (('head_sha', 'c' * 40), ('base_sha', 'd' * 40),
                           ('base', 'main'), ('base', 'colleague/work'), ('pr', 29)):
            with self.subTest(key=key, value=value):
                args = {'issue': 27, 'pr': 28, 'base': 'feature/sales-agent',
                        'head_sha': HEAD, 'base_sha': BASE}
                args[key] = value
                self.denied(self.approved(arguments=args))

    def test_receipt_does_not_authorize_modified_payload_or_another_session(self):
        request = self.approved('comment', {'issue': 27, 'body': 'reviewed text'})
        request['arguments']['body'] = 'different text'
        self.denied(request)
        request = self.approved()
        self.policy['receipts']['host-approval-001']['parent_session'] = 'other-session'
        self.denied(request)

    def test_completed_request_is_durable_and_not_sent_twice_after_restart(self):
        request = self.approved()
        first = self.broker().execute(request)
        second = self.broker().execute(request)
        self.assertEqual(first, second)
        self.assertEqual(1, len(self.transport.writes))
        changed = copy.deepcopy(request)
        changed['arguments']['pr'] = 29
        with self.assertRaises(github_broker.BrokerError):
            self.broker().execute(changed)
        self.assertEqual(1, len(self.transport.writes))

    def test_unknown_write_is_durable_and_never_automatically_retried(self):
        request = self.approved()
        self.transport.fail_write = True
        first = self.broker().execute(request)
        self.assertEqual('unknown', first['status'])
        second = self.broker().execute(request)
        self.assertEqual(first, second)
        self.assertEqual(1, len(self.transport.writes))
        self.assertFalse(self.transport.guard_held)
        self.assertIn(('guard-exit', False), self.transport.events)

    def test_interrupted_persisted_intent_is_not_retried_after_restart(self):
        request = self.approved()
        self.transport.interrupt_write = True
        with self.assertRaises(KeyboardInterrupt):
            self.broker().execute(request)
        self.assertEqual(1, len(self.transport.writes))
        self.assertFalse(self.transport.guard_held)
        self.transport.interrupt_write = False
        result = self.broker().execute(request)
        self.assertEqual('unknown', result['status'])
        self.assertEqual(1, len(self.transport.writes))

    def test_suppressed_interruption_cannot_fall_through_to_another_write(self):
        @contextmanager
        def suppressing_guard(repo, branch, expected_base):
            self.transport.guard_held = True
            try:
                yield True
            except KeyboardInterrupt:
                pass
            finally:
                self.transport.guard_held = False
        self.transport.integration_guard = suppressing_guard
        self.transport.interrupt_write = True
        request = self.approved()
        with self.assertRaises(github_broker.BrokerError):
            self.broker().execute(request)
        self.assertEqual(1, len(self.transport.writes))
        self.transport.interrupt_write = False
        self.assertEqual('unknown', self.broker().execute(request)['status'])
        self.assertEqual(1, len(self.transport.writes))
        self.assertFalse(self.transport.guard_held)

    def test_new_request_identity_cannot_bypass_unresolved_remote_write(self):
        request = self.approved()
        self.transport.fail_write = True
        self.assertEqual('unknown', self.broker().execute(request)['status'])
        replacement = self.approved()
        replacement['request_id'] = 'attempt-to-bypass-unknown'
        unsigned = dict(replacement, approval_id=None)
        self.policy['receipts']['host-approval-001']['request_sha256'] = digest(unsigned)
        with self.assertRaises(github_broker.BrokerError):
            self.broker().execute(replacement)
        self.assertEqual(1, len(self.transport.writes))

    def test_corrupt_durable_ledger_blocks_replay_and_new_submission(self):
        request = self.approved()
        self.broker().execute(request)
        records = list(Path(self.directory.name).glob('*.json'))
        self.assertEqual(1, len(records), 'one durable top-level JSON ledger per request')
        records[0].write_text('{corrupt host ledger', encoding='utf-8')
        with self.assertRaises(github_broker.BrokerError):
            self.broker().execute(request)
        replacement = self.request(request_id='new-after-corruption')
        with self.assertRaises(github_broker.BrokerError):
            self.broker().execute(replacement)
        self.assertEqual(1, len(self.transport.writes))

    def test_symlinked_durable_ledger_is_never_trusted(self):
        request = self.approved()
        self.broker().execute(request)
        records = list(Path(self.directory.name).glob('*.json'))
        self.assertEqual(1, len(records))
        target = Path(self.directory.name) / 'redirected-ledger'
        records[0].rename(target)
        records[0].symlink_to(target)
        with self.assertRaises(github_broker.BrokerError):
            self.broker().execute(request)
        self.assertEqual(1, len(self.transport.writes))

    def test_existing_parent_lock_blocks_parallel_submission(self):
        (Path(self.directory.name) / 'broker.lock').write_text('another parent\n')
        self.denied(self.approved())

    def test_missing_or_malformed_required_evidence_is_never_approval(self):
        for key in ('authority_digest', 'claim_digest', 'dependency_digest',
                    'review_digest', 'checks_digest'):
            for value in (None, True, 'passed', ''):
                with self.subTest(key=key, value=value):
                    original = copy.deepcopy(self.transport.current)
                    self.transport.current[key] = value
                    self.denied(self.approved())
                    self.transport.current = original

    def test_raw_remote_fields_do_not_escape_snapshot_response(self):
        self.transport.current['token'] = 'SENTINEL-CREDENTIAL'
        self.transport.current['stderr'] = 'raw private runner output'
        result = self.broker().execute(self.request())
        self.assertNotIn('SENTINEL', json.dumps(result))
        self.assertNotIn('stderr', json.dumps(result))

    def test_symlinked_durable_state_root_is_refused(self):
        parent = Path(self.directory.name)
        actual = parent / 'actual'
        actual.mkdir()
        linked = parent / 'linked'
        linked.symlink_to(actual, target_is_directory=True)
        with self.assertRaises(github_broker.BrokerError):
            github_broker.Broker(self.policy, linked, self.transport).execute(self.approved())
        self.assertEqual([], self.transport.writes)

    def test_receipt_cannot_enable_unscoped_pr_or_merge_bypass_fields(self):
        for extra in ({'force': True}, {'admin': True}, {'auto_merge': True},
                      {'delete_branch': True}, {'method': 'rebase'}):
            with self.subTest(extra=extra):
                request = self.approved()
                request['arguments'].update(extra)
                self.denied(request)

    def test_approved_comment_and_pr_creation_are_bound_to_exact_payload(self):
        for operation, arguments in (
                ('comment', {'issue': 27, 'body': 'reviewed public progress'}),
                ('create_pr', {'issue': 27, 'base': 'feature/sales-agent',
                               'head': 'choubokyann/symphony-coordinator',
                               'head_sha': HEAD, 'base_sha': BASE,
                               'title': 'Restricted broker', 'body': 'Refs #27'})):
            with self.subTest(operation=operation):
                self.transport.writes.clear()
                request = self.approved(operation, arguments)
                request['request_id'] = 'request-' + operation.replace('_', '-')
                unsigned = dict(request, approval_id=None)
                self.policy['receipts']['host-approval-001']['request_sha256'] = digest(unsigned)
                result = self.broker().execute(request)
                self.assertEqual('completed', result['status'])
                self.assertEqual([(operation, REPO, arguments)], self.transport.writes)


if __name__ == '__main__':
    unittest.main()
