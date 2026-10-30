"""Local contract checks; these do not substitute for a Docker/PowerShell pilot."""
from pathlib import Path
import tomllib
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


class ConfigurationTests(unittest.TestCase):
    def test_repository_execution_is_delegated_to_offline_host_boundary(self):
        for name in ('WORKFLOW.template.md', 'README.md'):
            content = (HERE / name).read_text()
            self.assertIn('Never execute repository-controlled code in the coordinator', content)
            self.assertIn('ISOLATION-PILOT.md', content)
        install = (HERE / 'Install-Coordinator.ps1').read_text()
        for name in ('Invoke-IsolatedChecks.ps1', 'isolation_probe.py',
                     'test_isolated_checks.py', 'ISOLATION-PILOT.md'):
            self.assertIn(name, install)

    def test_isolated_tool_has_separate_mounts_and_bounded_timeout(self):
        start = (HERE / 'Start-Coordinator.ps1').read_text()
        config = tomllib.loads((HERE / 'coordinator.toml').read_text())
        tool = config['mcp_servers']['isolated_checks']
        self.assertEqual(tool['command'], 'python3')
        self.assertEqual(tool['tool_timeout_sec'], 60)
        self.assertIn('/runtime/isolated_tool.py', tool['args'])
        self.assertIn('target=/checks/results,readonly', start)
        self.assertIn('target=/checks/requests', start)
        self.assertNotIn('/var/run/docker.sock', start)

    def test_profiles_select_explicit_models_and_one_child(self):
        coordinator = tomllib.loads((HERE / 'coordinator.toml').read_text())
        worker = tomllib.loads((HERE / 'worker.toml').read_text())
        self.assertEqual(coordinator['model'], 'gpt-6-astra')
        self.assertEqual(worker['model'], 'gpt-6.1-sol')
        self.assertEqual(coordinator['model_reasoning_effort'], 'high')
        self.assertEqual(worker['model_reasoning_effort'], 'high')
        self.assertEqual(coordinator['agents']['max_concurrent_threads_per_session'], 1)
        self.assertEqual(coordinator['agents']['default_subagent_model'], worker['model'])
        self.assertEqual(coordinator['agents']['default_subagent_reasoning_effort'], 'high')
        self.assertFalse(worker['agents']['enabled'])
        for profile in (coordinator, worker):
            self.assertNotIn('profiles', profile)
            self.assertNotIn('max_threads', profile['agents'])
            self.assertEqual(profile['sandbox_mode'], 'workspace-write')

    def test_workflow_only_dispatches_control_label_and_one_turn(self):
        import machine
        from registry import load_registry
        rendered = machine.render_workflow(load_registry(HERE / 'projects.json')['projects']['pokemon'], 'pokemon')
        if (ROOT / 'WORKFLOW.md').exists():
            self.assertEqual((ROOT / 'WORKFLOW.md').read_text(), rendered)
        front = rendered.split('---')[1]
        self.assertIn('required_labels: ["symphony-choubokyann-coordinator"]', front)
        self.assertIn('active_states: [open]', front)
        self.assertIn('max_concurrent_agents: 1', front)
        self.assertIn('max_turns: 1', front)
        self.assertIn('command: codex app-server', front)
        self.assertNotIn('after_run:', front)
        self.assertNotIn('acknowledge', front)
        self.assertIn('queue_gate.py check', front)

    def test_launcher_preserves_existing_instance_and_uses_environment_credentials(self):
        start = (HERE / 'Start-Coordinator.ps1').read_text()
        stop = (HERE / 'Stop-Coordinator.ps1').read_text()
        self.assertIn("'container', 'ls', '-a'", start)
        self.assertIn('already exists', start)
        self.assertIn("'--env', 'GH_TOKEN'", start)
        self.assertIn("'--env', 'SYMPHONY_QUEUE_TOKEN'", start)
        self.assertIn('127.0.0.1:', start)
        self.assertIn('seccomp=unconfined', start)
        self.assertIn('/root/.codex/config.toml,readonly', start)
        self.assertIn('/root/.codex/auth.json,readonly', start)
        self.assertIn('WaitForExit', (HERE / 'Process.ps1').read_text())
        self.assertNotIn('--privileged', start)
        self.assertNotIn('danger-full-access', start)
        self.assertNotIn("'rm'", start)
        self.assertNotIn("'-v'", stop)
        self.assertNotIn('volume rm', stop)

    def test_installation_and_launcher_use_registered_runtime_and_visible_logs(self):
        start = (HERE / 'Start-Coordinator.ps1').read_text()
        install = (HERE / 'Install-Coordinator.ps1').read_text()
        entry = (HERE / 'entrypoint.sh').read_text()
        self.assertIn(".symphony/choubokyann", install)
        self.assertIn('Installation already exists', install)
        self.assertIn('$($selected.volume)', start)
        self.assertIn('$selected.repo', start)
        self.assertIn('$selected.branch', start)
        self.assertIn('Show-Logs.ps1', start)
        self.assertIn('SYMPHONY_REGISTRY', start)
        self.assertIn('SYMPHONY_PROJECT', start)
        self.assertLess(start.index('if ($DryRun)'), start.index('Resolve-Path'))
        self.assertIn('/runtime/machine.py', entry)
        self.assertIn('/work/runtime/WORKFLOW.md', entry)
        self.assertNotIn('Perryong/pokemon-tracker', start)

    def test_machine_slot_and_resources_do_not_multiply_per_project(self):
        start = (HERE / 'Start-Coordinator.ps1').read_text()
        stop = (HERE / 'Stop-Coordinator.ps1').read_text()
        self.assertIn("$name = 'symphony-choubokyann'", start)
        self.assertIn("$name = 'symphony-choubokyann'", stop)
        self.assertIn("'--cpus', '2'", start)
        self.assertIn("'--memory', '3g'", start)
        self.assertIn('Unregistered repository', start)


if __name__ == '__main__':
    unittest.main()
