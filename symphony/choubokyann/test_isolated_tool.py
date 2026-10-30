"""Run only in credential-free check container. Written before adapter source."""
import hashlib
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest

try:
    from isolated_tool import CheckTool, ToolError, dispatch, digest
except ImportError:
    CheckTool = None


class ToolTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(CheckTool, 'isolated check tool not implemented')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.requests = self.root / 'requests'; self.requests.mkdir()
        self.results = self.root / 'results'; self.results.mkdir()
        self.tool = CheckTool(self.requests, self.results, 'pokemon')
        self.args = dict(job_id='trial-1', commit='a' * 40, suite='coordinator')

    def result(self, **changes):
        req = json.loads((self.requests / 'trial-1.json').read_text())
        value = dict(req, request_sha256=digest(req), status='completed',
                     image='sha256:' + 'b' * 64, archive_sha256='c' * 64,
                     exit_code=0, output='untrusted test output', cleanup=True, error=None)
        value.update(changes)
        (self.results / 'trial-1.json').write_text(json.dumps(value))

    def test_submit_is_durable_and_idempotent(self):
        first = self.tool.submit(self.args)
        self.assertEqual(first['status'], 'pending')
        before = (self.requests / 'trial-1.json').read_bytes()
        self.assertEqual(self.tool.submit(self.args), first)
        self.assertEqual(before, (self.requests / 'trial-1.json').read_bytes())
        self.assertFalse((self.root / 'queue-gate.json').exists())

    def test_conflicting_id_rejected(self):
        self.tool.submit(self.args)
        with self.assertRaises(ToolError):
            self.tool.submit(dict(self.args, commit='d' * 40))

    def test_no_paths_commands_or_project_override(self):
        for args in [dict(self.args, job_id='../escape'), dict(self.args, command='sh'),
                     dict(self.args, project='other'), dict(self.args, suite='shell'),
                     dict(self.args, commit='main')]:
            with self.subTest(args=args), self.assertRaises(ToolError):
                self.tool.submit(args)

    def test_correlated_result_returned_as_untrusted(self):
        self.tool.submit(self.args); self.result()
        result = self.tool.status(self.args)
        self.assertEqual(result['status'], 'completed')
        self.assertTrue(result['output_is_untrusted'])
        self.assertEqual(result['commit'], 'a' * 40)

    def test_mismatched_result_and_false_success_rejected(self):
        self.tool.submit(self.args)
        for changes in [dict(commit='e'*40), dict(request_sha256='f'*64),
                        dict(cleanup=False), dict(exit_code=2), dict(project='other'),
                        dict(output='x'*32769), dict(image='latest')]:
            self.result(**changes)
            with self.subTest(changes=list(changes)), self.assertRaises(ToolError):
                self.tool.status(self.args)

    def test_failed_result_preserved_without_retry(self):
        self.tool.submit(self.args); self.result(status='failed', exit_code=1)
        self.assertEqual(self.tool.submit(self.args)['status'], 'failed')
        self.assertEqual(self.tool.status(self.args)['exit_code'], 1)

    def test_symlink_requests_and_results_rejected(self):
        target = self.root / 'foreign'; target.write_text('{}')
        (self.requests / 'trial-1.json').symlink_to(target)
        with self.assertRaises(ToolError): self.tool.submit(self.args)
        (self.requests / 'trial-1.json').unlink()
        self.tool.submit(self.args)
        (self.results / 'trial-1.json').symlink_to(target)
        with self.assertRaises(ToolError): self.tool.status(self.args)

    def test_mcp_initialize_list_and_tool_error(self):
        response = dispatch(self.tool, {'jsonrpc':'2.0','id':1,'method':'initialize',
                                       'params':{'protocolVersion':'2024-11-05'}})
        self.assertEqual(response['result']['protocolVersion'], '2024-11-05')
        listed = dispatch(self.tool, {'jsonrpc':'2.0','id':2,'method':'tools/list'})
        self.assertEqual({t['name'] for t in listed['result']['tools']}, {'run_checks','check_status'})
        reply = dispatch(self.tool, {'jsonrpc':'2.0','id':3,'method':'tools/call',
                      'params':{'name':'run_checks','arguments':dict(self.args, commit='main')}})
        self.assertTrue(reply['result']['isError'])

    def test_stdio_protocol_real_process(self):
        messages = [dict(jsonrpc='2.0', id=1, method='initialize', params={'protocolVersion':'2025-06-18'}),
                    dict(jsonrpc='2.0', method='notifications/initialized'),
                    dict(jsonrpc='2.0', id=2, method='tools/list')]
        completed = subprocess.run([sys.executable, '-I', str(Path(__file__).with_name('isolated_tool.py')),
                      '--requests', str(self.requests), '--results', str(self.results), '--project', 'pokemon'],
                      input=''.join(json.dumps(m) + '\n' for m in messages), text=True,
                      capture_output=True, timeout=5)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        responses = [json.loads(line) for line in completed.stdout.splitlines()]
        self.assertEqual([r['id'] for r in responses], [1, 2])
        self.assertEqual(len(responses[1]['result']['tools']), 2)

    def test_wait_timeout_returns_pending_without_deleting(self):
        self.tool.submit(self.args)
        self.assertEqual(self.tool.wait(self.args, seconds=0)['status'], 'pending')
        self.assertTrue((self.requests / 'trial-1.json').exists())

if __name__ == '__main__': unittest.main()
