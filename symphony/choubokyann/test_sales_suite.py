"""Fixed recipe contracts; execute only through the isolated coordinator suite."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

probe = load('isolation_probe')
adapter = load('isolated_tool')
runner = load('isolated_runner')

def outcome(scenario):
    count = {'eligible': 2, 'out-of-policy': 1, 'expired': 0, 'opt-out': 1, 'material-facts': 1}[scenario]
    reason = {'out-of-policy': 'price_out_of_mandate', 'expired': 'expired_mandate',
              'opt-out': 'seller_opt_out', 'material-facts': 'reassessment_required'}.get(scenario)
    return dict(scenario=scenario, harness='deepagents.create_deep_agent', marketplace='deterministic_simulation',
                model_transport='scripted_offline_fixture', outbound=[{}] * count, rounds=count,
                opted_out=scenario == 'opt-out',
                proposal={'status': 'awaiting_operator_approval', 'amount_minor': 4500, 'currency': 'SGD',
                          'dispatchable': False} if scenario == 'eligible' else None,
                reassessment={'kind': 'market_reassessment_request', 'transport': 'local_fixture_unauthenticated',
                              'requires_replacement_mandate': True, 'facts': {'condition': 'creased'}} if scenario == 'material-facts' else None,
                tool_results=([{'status': 'sent'}, {'status': 'sent'}, {'status': 'awaiting_operator_approval'}]
                              if scenario == 'eligible' else
                              ([{'status': 'rejected', 'reason': reason}] * 3 if scenario == 'expired' else
                               [{'status': 'sent'}, {'status': 'rejected', 'reason': reason}, {'status': 'rejected', 'reason': reason}])))

class SalesSuiteTests(unittest.TestCase):
    def test_named_suite_is_allowed_by_adapter_and_runner(self):
        with tempfile.TemporaryDirectory() as root:
            tool = adapter.CheckTool(root, root, 'pokemon')
            args = dict(job_id='sales-test', commit='a' * 40, suite='sales-agent')
            request = tool.request(args)
            runner.validate_request(request, 'pokemon', 'sales-test.json')
            self.assertIn('sales-agent', adapter.SCHEMA['properties']['suite']['enum'])
            for suite in ('shell', 'sales-agent;echo bad', '', None, []):
                with self.subTest(suite=suite), self.assertRaises(ValueError):
                    tool.request(dict(args, suite=suite))
                with self.subTest(suite=suite), self.assertRaises(ValueError):
                    runner.validate_request(dict(request, suite=suite), 'pokemon', 'sales-test.json')

    def test_all_five_documented_outcomes_pass(self):
        for scenario in ('eligible', 'out-of-policy', 'expired', 'opt-out', 'material-facts'):
            probe.validate_sales_demo(scenario, outcome(scenario))

    def test_plausible_but_wrong_results_fail(self):
        mutations = [('eligible', 'proposal', {'status': 'awaiting_operator_approval', 'amount_minor': 4501, 'currency': 'SGD', 'dispatchable': False}),
                     ('eligible', 'proposal', {'status': 'awaiting_operator_approval', 'amount_minor': 4500, 'currency': 'SGD', 'dispatchable': True}),
                     ('expired', 'outbound', [{}]), ('opt-out', 'opted_out', False),
                     ('material-facts', 'reassessment', None), ('out-of-policy', 'tool_results', []),
                     ('eligible', 'harness', 'fake'), ('eligible', 'model_transport', 'live')]
        for scenario, key, value in mutations:
            data = outcome(scenario)
            data[key] = value
            with self.subTest(scenario=scenario, key=key), self.assertRaises(ValueError):
                probe.validate_sales_demo(scenario, data)
        for value in (None, [], {}, 'not-json'):
            with self.assertRaises(ValueError):
                probe.validate_sales_demo('eligible', value)

    def test_fixed_recipe_and_parsed_demos(self):
        calls = []
        def invoke(argv, **kwargs):
            calls.append((argv, kwargs))
            output = json.dumps(outcome(argv[-1])) if '--scenario' in argv else ''
            return subprocess.CompletedProcess(argv, 0, stdout=output)
        with patch.object(probe.subprocess, 'run', side_effect=invoke):
            self.assertEqual(probe.run_suite(Path('/work/source'), {'suite': 'sales-agent'}), 0)
        self.assertEqual(len(calls), 7)
        self.assertEqual(calls[0][0][1:], ['-m', 'pip', 'check'])
        self.assertEqual(calls[1][0][1:], ['-m', 'pytest', '-q', '-p', 'no:cacheprovider'])
        for argv, kwargs in calls:
            self.assertEqual(kwargs['cwd'], Path('/work/source/sales_agent'))
            self.assertEqual(kwargs['env']['PYTHONPATH'], '/work/source/sales_agent/src')
            self.assertNotIn('install', argv)

    def test_nonzero_and_bad_demo_output_fail_without_fallback(self):
        for result in (subprocess.CompletedProcess([], 1, stdout='{}'), subprocess.CompletedProcess([], 0, stdout='{}')):
            with self.subTest(result=result), patch.object(probe.subprocess, 'run', return_value=result):
                with self.assertRaises((ValueError, RuntimeError)):
                    probe.run_suite(Path('/work/source'), {'suite': 'sales-agent'})

    def test_named_suite_rejects_command_injection_and_unknown_suite(self):
        for job in ({'suite': 'sales-agent', 'argv': ['echo', 'bad']}, {'suite': 'shell'}):
            with patch.object(probe.subprocess, 'run') as run, self.assertRaises(ValueError):
                probe.run_suite(Path('/work/source'), job)
            run.assert_not_called()

    def test_coordinator_recipe_is_preserved(self):
        with patch.object(probe.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)) as run:
            self.assertEqual(probe.run_suite(Path('/work/source'), {'suite': 'coordinator'}), 0)
        self.assertEqual(len(run.call_args_list), 2)
        self.assertIn('symphony/choubokyann', run.call_args_list[0].args[0])
        self.assertIn('.github/scripts', run.call_args_list[1].args[0])

if __name__ == '__main__':
    unittest.main()
