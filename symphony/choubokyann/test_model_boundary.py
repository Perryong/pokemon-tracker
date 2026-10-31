"""Credential-free isolated Linux root tests; no Codex/model/service is started.

A tiny immutable executable reports actual kernel state after the real launcher.
Removing demotion, FD closure, env scrubbing or path validation must fail here.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

try:
    import model_boundary as boundary
except ImportError:
    boundary = None


class BoundaryAvailabilityTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(boundary, 'fixed model launch boundary is not implemented')
        self.value = dict(executable='/opt/model/codex', executable_sha256='a' * 64,
                          model_home='/home/model', codex_home='/opt/model/home',
                          config_sha256='b' * 64, workspace_root='/work/project')

    def test_accepts_fixed_policy_without_command_overrides(self):
        self.assertEqual(boundary.parse_policy(json.dumps(self.value)), self.value)

    def test_rejects_duplicate_and_unknown_policy_fields(self):
        raw = json.dumps(self.value)
        for text in (raw[:-1] + ',"executable":"/bin/sh"}',
                     json.dumps(dict(self.value, argv=['/bin/sh'])),
                     json.dumps(dict(self.value, uid=0))):
            with self.subTest(text=text), self.assertRaises(boundary.BoundaryError):
                boundary.parse_policy(text)

    def test_rejects_relative_noncanonical_and_nul_paths(self):
        for path in ('relative', '/opt/../bin/codex', '/opt//codex', '/opt/./codex',
                     '/opt/codex/', '/opt/codex\x00ignored', '/', 123, None):
            with self.subTest(path=path), self.assertRaises(boundary.BoundaryError):
                boundary.parse_policy(json.dumps(dict(self.value, executable=path)))

    def test_rejects_missing_fields_wrong_types_and_invalid_hashes(self):
        missing = dict(self.value); missing.pop('workspace_root')
        cases = [[], None, missing, dict(self.value, executable_sha256='A'*64),
                 dict(self.value, config_sha256='b'*63),
                 dict(self.value, config_sha256=True)]
        for value in cases:
            with self.subTest(value=value), self.assertRaises(boundary.BoundaryError):
                boundary.parse_policy(json.dumps(value))

    def test_rejects_oversized_or_malformed_policy(self):
        for raw in ('{', 'null', ' ' * 65537, '{"x": NaN}'):
            with self.subTest(raw=raw[:20]), self.assertRaises(boundary.BoundaryError):
                boundary.parse_policy(raw)


@unittest.skipUnless(sys.platform == 'linux' and os.geteuid() == 0,
                     'requires disposable credential-free Linux root container')
class ModelBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(boundary, 'fixed model launch boundary is not implemented')
        self.root = Path(tempfile.mkdtemp(prefix='model-boundary-', dir='/run'))
        self.root.chmod(0o755)
        self.addCleanup(shutil.rmtree, self.root)
        self.home = self.root / 'home'; self.home.mkdir(mode=0o700)
        os.chown(self.home, 65534, 65534)
        self.codex = self.root / 'codex'; self.codex.mkdir(mode=0o755)
        self.config = self.codex / 'config.toml'
        self.config.write_text('model = "synthetic-only"\n'); self.config.chmod(0o444)
        self.auth = self.codex / 'auth.json'
        self.auth.write_text('{"synthetic_model_auth":true}\n')
        os.chown(self.auth, 65534, 65534); self.auth.chmod(0o600)
        self.workspace = self.root / 'work'; self.workspace.mkdir(mode=0o700)
        os.chown(self.workspace, 65534, 65534)
        self.secret = self.root / 'controller-secret'
        self.secret.write_text('SYNTHETIC_CONTROL_ONLY'); self.secret.chmod(0o600)
        self.executable = self.root / 'appserver-probe'
        # Native ELF permits pinned-FD exec without a leaked shebang FD.
        # Python executes this fixture only after the privilege boundary.
        shutil.copyfile(Path(sys.executable).resolve(), self.executable)
        probe = self.workspace / 'app-server'
        probe.write_text('''import ctypes,json,os,pathlib,sys
parent = PARENT
secret = SECRET
def readable(path):
    try:
        with open(path, 'rb') as source: source.read(1)
        return True
    except OSError: return False
status = dict(line.split(':',1) for line in pathlib.Path('/proc/self/status').read_text().splitlines() if ':' in line)
extra = []
for name in os.listdir('/proc/self/fd'):
    try:
        if int(name)>2: os.fstat(int(name)); extra.append(int(name))
    except OSError: pass
try: os.setuid(0); regained = True
except OSError: regained = False
request = sys.stdin.readline().strip()
print(json.dumps(dict(uid=os.getuid(),gid=os.getgid(),groups=os.getgroups(),
    env=dict(os.environ),argv=['app-server']+sys.argv[1:],request=request,extra_fds=extra,
    no_new_privs=status.get('NoNewPrivs','').strip(),
    caps={k:status[k].strip() for k in ['CapInh','CapPrm','CapEff','CapBnd','CapAmb']},
    secret_readable=readable(secret),parent_env_readable=readable('/proc/%s/environ'%parent),
    parent_fd_readable=readable('/proc/%s/fd/0'%parent),regained=regained,
    cwd=os.getcwd(),auth_readable=readable(os.environ['CODEX_HOME']+'/auth.json'))),flush=True)
'''.replace('PARENT', str(os.getpid())).replace('SECRET', repr(str(self.secret))))
        probe.chmod(0o444)
        self.executable.chmod(0o755)
        self.policy = self.root / 'policy.json'
        self.value = dict(executable=str(self.executable),
                          executable_sha256=hashlib.sha256(self.executable.read_bytes()).hexdigest(),
                          model_home=str(self.home), codex_home=str(self.codex),
                          config_sha256=hashlib.sha256(self.config.read_bytes()).hexdigest(),
                          workspace_root=str(self.workspace))
        self.write_policy()

    def write_policy(self):
        self.policy.write_text(json.dumps(self.value)); self.policy.chmod(0o600)

    def invoke(self, workspace=None, pass_fds=(), stdin=subprocess.PIPE):
        env = dict(os.environ, GH_TOKEN='SYNTHETIC_GH', SYMPHONY_QUEUE_TOKEN='SYNTHETIC_QUEUE',
                   BASH_ENV='/hostile', PYTHONPATH='/hostile', CODEX_HOME='/hostile',
                   HOME='/hostile', GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='core.hooksPath',
                   GIT_CONFIG_VALUE_0='/hostile')
        proc = subprocess.Popen([sys.executable, '-I', str(Path(boundary.__file__).resolve()),
                                 '--policy', str(self.policy), '--workspace',
                                 str(workspace or self.workspace)], stdin=stdin,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                env=env, pass_fds=pass_fds)
        output, error = proc.communicate(b'parent-owned-pipe\n' if stdin == subprocess.PIPE else None,
                                         timeout=10)
        return proc.returncode, output, error

    def assert_rejected(self, **kwargs):
        code, output, _ = self.invoke(**kwargs)
        self.assertNotEqual(code, 0)
        self.assertEqual(output, b'', 'must reject before untrusted executable starts')

    def test_real_kernel_demotes_scrubs_and_preserves_parent_pipe(self):
        fd = os.open(self.secret, os.O_RDONLY); self.addCleanup(os.close, fd)
        code, output, error = self.invoke(pass_fds=(fd,))
        self.assertEqual(code, 0, error.decode(errors='replace'))
        observed = json.loads(output)
        self.assertEqual((observed['uid'], observed['gid'], observed['groups']), (65534, 65534, []))
        self.assertEqual(observed['argv'], ['app-server', '--strict-config'])
        self.assertEqual(observed['request'], 'parent-owned-pipe')
        self.assertEqual(observed['extra_fds'], [])
        self.assertEqual(observed['no_new_privs'], '1')
        self.assertEqual(set(observed['caps'].values()), {'0000000000000000'})
        self.assertFalse(observed['secret_readable'])
        self.assertFalse(observed['parent_env_readable'])
        self.assertFalse(observed['parent_fd_readable'])
        self.assertFalse(observed['regained'])
        self.assertTrue(observed['auth_readable'])
        self.assertEqual(observed['cwd'], str(self.workspace))
        self.assertEqual(observed['env'], dict(HOME=str(self.home), CODEX_HOME=str(self.codex),
                                             PATH='/usr/bin:/bin', LANG='C.UTF-8'))

    def test_rejects_executable_content_change(self):
        self.executable.write_text('#!/bin/sh\necho compromised\n')
        self.assert_rejected()

    def test_rejects_executable_model_write_access(self):
        os.chown(self.executable, 65534, 65534)
        self.assert_rejected()

    def test_rejects_writable_trusted_ancestor(self):
        self.root.chmod(0o777)
        self.assert_rejected()

    def test_rejects_executable_symlink(self):
        target = self.root / 'real'; self.executable.rename(target)
        self.executable.symlink_to(target)
        self.assert_rejected()

    def test_rejects_policy_symlink(self):
        target = self.root / 'real-policy'; self.policy.rename(target)
        self.policy.symlink_to(target)
        self.assert_rejected()

    def test_rejects_model_owned_policy(self):
        os.chown(self.policy, 65534, 65534)
        self.assert_rejected()

    def test_rejects_writable_config_even_with_matching_digest(self):
        self.config.chmod(0o666)
        self.assert_rejected()

    def test_rejects_changed_config(self):
        self.config.write_text('hostile = true\n')
        self.assert_rejected()

    def test_rejects_config_symlink(self):
        target = self.root / 'real-config'; self.config.rename(target)
        self.config.symlink_to(target)
        self.assert_rejected()

    def test_rejects_workspace_escape_or_symlink(self):
        self.assert_rejected(workspace=self.root)
        link = self.workspace / 'link'; link.symlink_to(self.workspace, target_is_directory=True)
        self.assert_rejected(workspace=link)

    def test_rejects_nonpipe_stdin(self):
        with open(self.secret, 'rb') as source:
            self.assert_rejected(stdin=source)

    def test_rejects_unknown_and_duplicate_policy_keys(self):
        self.value['argv'] = ['sh', '-c', 'echo compromised']; self.write_policy()
        self.assert_rejected()
        self.value.pop('argv'); self.write_policy()
        text = self.policy.read_text()
        self.policy.write_text(text[:-1] + ',"executable":"/bin/sh"}')
        self.assert_rejected()

    def test_rejects_setid_executable(self):
        self.executable.chmod(0o4755)
        self.assert_rejected()

    def test_rejects_nonprivate_model_auth(self):
        self.auth.chmod(0o644)
        self.assert_rejected()


if __name__ == '__main__':
    unittest.main()
