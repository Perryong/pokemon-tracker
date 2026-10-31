"""Inactive startup must not touch credentials, tools, containers or models."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import machine
from registry import load_registry

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


class LauncherSecurityTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.marker = self.root / 'executed'
        for command in ('gh', 'docker', 'codex', 'python', 'python3', 'graphify', 'timeout'):
            stub = self.root / command
            stub.write_text('#!/bin/sh\nprintf called > "$CALL_MARKER"\nexit 93\n')
            stub.chmod(0o755)
        self.env = dict(PATH=str(self.root) + ':/usr/bin:/bin', HOME=str(self.root),
                        CALL_MARKER=str(self.marker), GH_TOKEN='SYNTHETIC_GH_SECRET',
                        SYMPHONY_QUEUE_TOKEN='SYNTHETIC_QUEUE_SECRET')

    def assert_refused(self, command):
        result = subprocess.run(command, env=self.env, capture_output=True, text=True, timeout=15)
        self.assertFalse(self.marker.exists(), 'startup executed an external tool')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Live coordinator startup disabled', result.stderr)
        self.assertNotIn('SYNTHETIC_', result.stdout + result.stderr)

    def test_direct_entrypoint_refuses_before_tools_or_credentials(self):
        self.assert_refused(['/bin/sh', str(HERE / 'entrypoint.sh')])

    def test_rendered_and_root_workflows_cannot_launch_model(self):
        scope = load_registry(HERE / 'projects.json')['projects']['pokemon']
        rendered = machine.render_workflow(scope, 'pokemon')
        workflows = [rendered]
        if (ROOT / 'WORKFLOW.md').exists():
            workflows.append((ROOT / 'WORKFLOW.md').read_text())
        for workflow in workflows:
            with self.subTest(workflow=workflow is rendered):
                command = next(line.split('command: ', 1)[1] for line in workflow.splitlines()
                               if line.startswith('  command: '))
                self.assert_refused(['/bin/sh', '-c', command])

    def powershell(self):
        executable = shutil.which('pwsh')
        if not executable:
            self.skipTest('PowerShell 7 required for actual launcher checks')
        return executable

    def test_powershell_live_start_refuses_before_tool_or_credential_access(self):
        self.assert_refused([self.powershell(), '-NoLogo', '-NoProfile', '-File',
                             str(HERE / 'Start-Coordinator.ps1'), '-Project', 'pokemon',
                             '-Registry', str(HERE / 'projects.json')])

    def test_offline_dry_run_keeps_working_after_branch_deletion(self):
        result = subprocess.run([self.powershell(), '-NoLogo', '-NoProfile', '-File',
                                 str(HERE / 'Start-Coordinator.ps1'), '-Project', 'pokemon',
                                 '-Registry', str(HERE / 'projects.json'), '-PythonCommand',
                                 sys.executable, '-DryRun'], env=self.env,
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.marker.exists())
        self.assertEqual(json.loads(result.stdout)['selected']['branch'], 'feature/sales-agent')

    def test_seed_registration_survives_pr_branch_deletion(self):
        scope = load_registry(HERE / 'projects.json')['projects']['pokemon']
        self.assertEqual(scope['branch'], 'feature/sales-agent')


if __name__ == '__main__':
    unittest.main()
