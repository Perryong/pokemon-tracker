"""Local contract checks; these do not substitute for a Docker/PowerShell pilot."""
from pathlib import Path
import tomllib
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


class ConfigurationTests(unittest.TestCase):
    def test_only_restricted_check_tools_are_preapproved(self):
        config = tomllib.loads((HERE / 'coordinator.toml').read_text())
        self.assertEqual(config['approval_policy'], 'never')
        servers = config['mcp_servers']
        self.assertEqual(set(servers), {'isolated_checks'})
        tool = servers['isolated_checks']
        self.assertEqual(set(tool.get('enabled_tools', [])), {'run_checks', 'check_status'})
        self.assertNotIn('default_tools_approval_mode', tool)
        self.assertEqual(tool.get('tools'), {
            'run_checks': {'approval_mode': 'approve'},
            'check_status': {'approval_mode': 'approve'},
        })

    def test_repository_execution_is_delegated_to_offline_host_boundary(self):
        for name in ('WORKFLOW.template.md', 'README.md'):
            content = (HERE / name).read_text()
            self.assertIn('Never execute repository-controlled code in the coordinator', content)
            self.assertIn('ISOLATION-PILOT.md', content)
        install = (HERE / 'Install-Coordinator.ps1').read_text()
        for name in ('Invoke-IsolatedChecks.ps1', 'isolation_probe.py',
                     'test_isolated_checks.py', 'ISOLATION-PILOT.md'):
            self.assertIn(name, install)

    def test_isolated_tool_has_bounded_timeout_and_no_credentials(self):
        config = tomllib.loads((HERE / 'coordinator.toml').read_text())
        tool = config['mcp_servers']['isolated_checks']
        self.assertEqual(tool['command'], 'python3')
        self.assertEqual(tool['tool_timeout_sec'], 60)
        self.assertIn('/runtime/isolated_tool.py', tool['args'])
        self.assertEqual(tool.get('env_vars'), ['SYMPHONY_PROJECT'])
        self.assertFalse(tool.get('env'))

    def test_profiles_select_explicit_models_and_three_children(self):
        coordinator = tomllib.loads((HERE / 'coordinator.toml').read_text())
        worker = tomllib.loads((HERE / 'worker.toml').read_text())
        self.assertEqual(coordinator['model'], 'gpt-6-astra')
        self.assertEqual(worker['model'], 'gpt-6.1-sol')
        self.assertEqual(coordinator['model_reasoning_effort'], 'high')
        self.assertEqual(worker['model_reasoning_effort'], 'high')
        self.assertEqual(coordinator['agents']['max_concurrent_threads_per_session'], 3)
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
        self.assertNotIn('command: codex app-server', front)
        self.assertIn('Live coordinator startup disabled', front)
        self.assertNotIn('after_run:', front)
        self.assertNotIn('acknowledge', front)
        self.assertNotIn('queue_gate.py check', front)

    def test_stop_preserves_existing_volumes(self):
        stop = (HERE / 'Stop-Coordinator.ps1').read_text()
        self.assertNotIn("'-v'", stop)
        self.assertNotIn('volume rm', stop)
        self.assertIn("$name = 'symphony-choubokyann'", stop)

    def test_installer_includes_security_gate_and_regression_checks(self):
        install = (HERE / 'Install-Coordinator.ps1').read_text()
        self.assertIn(".symphony/choubokyann", install)
        self.assertIn('Installation already exists', install)
        for name in ('Start-Coordinator.ps1', 'entrypoint.sh', 'SECURITY-BROKER.md',
                     'test_launcher_security.py'):
            self.assertIn(name, install)


if __name__ == '__main__':
    unittest.main()
