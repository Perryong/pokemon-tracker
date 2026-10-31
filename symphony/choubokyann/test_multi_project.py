"""Offline acceptance: alternate scopes reach the gate and workflow unchanged."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import queue_gate as gate
from test_queue_gate import FakeGitHub

HERE = Path(__file__).resolve().parent


def record(repo='Example/alpha', control=71, project=8):
    return dict(repo=repo, actor='ChouBokYann', project_owner='ChouBokYann',
                project_number=project, control_issue=control,
                control_label='alpha-control', queue_label='alpha-queue',
                session='synthetic-session', branch='coordination/setup', excluded_issues=[],
                scope='Synthetic setup only',
                authority_url=f'https://github.com/{repo}/issues/{control}#issuecomment-123')


class ScopedAPI:
    def __init__(self, scope):
        self.scope = scope
        self.base = FakeGitHub()
        self.queries = []

    def __call__(self, query, **variables):
        self.queries.append((query, variables))
        old = dict(variables)
        mapping = {self.scope['control_issue']: 27, 72: 28, 73: 29}
        if 'number' in old:
            old['number'] = mapping[old['number']]
        value = self.base(query, **old)
        def translate(obj):
            if isinstance(obj, list):
                return [translate(x) for x in obj]
            if isinstance(obj, dict):
                return {k: ({27: self.scope['control_issue'], 28: 72, 29: 73}.get(v, v)
                            if k == 'number' and isinstance(v, int) else translate(v)) for k, v in obj.items()}
            if isinstance(obj, str):
                return obj.replace('Perryong/pokemon-tracker', self.scope['repo']).replace(
                    'symphony-choubokyann-coordinator', self.scope['control_label']).replace(
                    'symphony-choubokyann-queue', self.scope['queue_label'])
            return obj
        value = translate(value)
        if 'QueueInventory' in query:
            value['user']['projectV2']['number'] = self.scope['project_number']
        return value


class MultiProjectTests(unittest.TestCase):
    def test_empty_explicit_scope_does_not_fall_back_to_pokemon(self):
        with self.assertRaises(ValueError):
            gate.snapshot(FakeGitHub(), {})

    def test_gate_cli_selects_two_registrations_into_separate_pending_state(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as directory:
            registry = Path(directory, 'projects.json')
            scopes = {'alpha': record(), 'beta': record('Example/beta', 91, 9)}
            registry.write_text(json.dumps({'version': 1, 'projects': scopes}))
            states = []
            for project, scope in scopes.items():
                workspace = Path(directory, project)
                argv = ['queue_gate.py', 'check', '--registry', str(registry),
                        '--project', project, '--workspace', str(workspace)]
                with patch('sys.argv', argv), patch.object(gate, 'GitHub', return_value=ScopedAPI(scope)):
                    self.assertEqual(gate.main(), 0)
                states.append(json.loads((workspace / '.symphony/choubokyann/queue-gate.json').read_text()))
            self.assertNotEqual(states[0]['scope'], states[1]['scope'])
            self.assertNotEqual(states[0]['pending']['snapshot']['fingerprint'], states[1]['pending']['snapshot']['fingerprint'])

    def test_registered_scope_reaches_queries_and_exclusions(self):
        scope = record()
        api = ScopedAPI(scope)
        self.assertEqual(gate.snapshot(api, scope)['issues'], [72])
        inventory = api.queries[0][1]
        self.assertEqual(inventory['owner'], 'Example')
        self.assertEqual(inventory['repo'], 'alpha')
        self.assertEqual(inventory['projectNumber'], 8)
        self.assertEqual(inventory['controlLabel'], 'alpha-control')
        scope['excluded_issues'] = [72]
        with self.assertRaises(gate.GateError):
            gate.snapshot(api, scope)

    def test_state_cannot_be_reused_or_retried_under_another_registration(self):
        first = record()
        second = record('Example/beta', project=9)
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(gate.run('check', directory, ScopedAPI(first), scope=first), 0)
            state = Path(directory, '.symphony/choubokyann/queue-gate.json')
            before = state.read_bytes()
            for command in ('check', 'inspect', 'acknowledge', 'retry'):
                self.assertNotEqual(gate.run(command, directory, ScopedAPI(second), scope=second,
                                            reason='must not release another project'), 0)
                self.assertEqual(state.read_bytes(), before)

    def test_machine_cli_two_selections_share_cap_but_not_volume_or_workflow(self):
        import subprocess
        import sys
        with tempfile.TemporaryDirectory() as directory:
            registry = Path(directory, 'projects.json')
            registry.write_text(json.dumps({'version': 1, 'projects': {
                'alpha': record(), 'beta': record('Example/beta', 91, 9)}}))
            plans = []
            for project in ('alpha', 'beta'):
                result = subprocess.run([sys.executable, str(HERE / 'machine.py'),
                                         '--registry', str(registry), '--project', project],
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                plans.append(json.loads(result.stdout))
            self.assertNotEqual(plans[0]['selected']['volume'], plans[1]['selected']['volume'])
            self.assertNotEqual(plans[0]['workflow'], plans[1]['workflow'])
            for plan in plans:
                selected = plan['selected']
                self.assertEqual(selected['container'], 'symphony-choubokyann')
                self.assertEqual((selected['cpus'], selected['memory'], selected['primary_slots'], selected['child_slots']), (2, '3g', 1, 3))
            self.assertEqual(sorted(p.name for p in Path(directory).iterdir()), ['projects.json'])

    def test_template_renders_two_projects_without_pokemon_ids_or_scheduler_changes(self):
        import machine
        first, second = record(), record('Example/beta', 91, 9)
        for scope in (first, second):
            rendered = machine.render_workflow(scope)
            self.assertIn(scope['repo'], rendered)
            self.assertIn(f"issues/{scope['control_issue']}", rendered)
            self.assertNotIn('Perryong/pokemon-tracker', rendered)
            self.assertNotIn('#27', rendered)
            self.assertNotIn('@@', rendered)
            self.assertIn('max_concurrent_agents: 1', rendered)
            self.assertIn('max_turns: 1', rendered)
            self.assertIn('Live coordinator startup disabled', rendered)
            self.assertNotIn('after_run:', rendered)


if __name__ == '__main__':
    unittest.main()
