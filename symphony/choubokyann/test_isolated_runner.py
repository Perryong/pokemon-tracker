"""Run only after copying trusted scripts into the clean host boundary."""
import json
import copy
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import isolated_runner as runner


def request(**changes):
    value = dict(version=1, job_id="sample-1", project="pokemon",
                 commit="a" * 40, suite="coordinator")
    value.update(changes)
    return value


class ContractTests(unittest.TestCase):
    def test_strict_contract_and_cross_project(self):
        runner.validate_request(request(), "pokemon", "sample-1.json")
        for change in ({"project": "elsewhere"}, {"argv": ["sh"]},
                       {"job_id": "../escape"}, {"version": True},
                       {"commit": "A" * 40}, {"suite": "shell"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                runner.validate_request(request(**change), "pokemon", "sample-1.json")
        with self.assertRaises(ValueError):
            runner.validate_request(request(), "pokemon", "other.json")

    def test_correlation_is_canonical(self):
        value = request()
        self.assertEqual(runner.request_digest(value),
                         runner.request_digest(dict(reversed(list(value.items())))))
        self.assertNotEqual(runner.request_digest(value),
                            runner.request_digest(request(commit="b" * 40)))


class AcquisitionTests(unittest.TestCase):
    def test_missing_exact_commit_is_fetched_from_registered_public_origin(self):
        config = dict(repository='/seed', origin='https://github.com/Example/alpha.git')
        calls = []
        def execute(args, **kwargs):
            calls.append(args)
            if 'get-url' in args: return config['origin']
            if 'rev-parse' in args:
                if sum('rev-parse' in a for a in calls) == 1: raise RuntimeError('missing')
                return 'a'*40
            return ''
        with patch.object(runner, 'command', side_effect=execute):
            runner.ensure_commit(config, 'a'*40)
        fetch = next(a for a in calls if 'fetch' in a)
        self.assertEqual(fetch[-2:], [config['origin'], 'a'*40])
        self.assertIn('--no-recurse-submodules', fetch)
        self.assertIn('credential.helper=', fetch)

    def test_registered_project_request_is_not_hardcoded_to_pokemon(self):
        runner.validate_request(request(project='alpha'), 'alpha', 'sample-1.json')
        with self.assertRaises(ValueError):
            runner.validate_request(request(project='beta'), 'alpha', 'sample-1.json')


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.config = {"project": "pokemon", "image": "sha256:" + "a" * 64,
                       **{key: str(root / key) for key in
                          ("repository", "requests", "results", "state")}}
        for key in ("repository", "requests", "results", "state"):
            Path(self.config[key]).mkdir(mode=0o700)
        self.calls = []
        self.result = dict(status="completed", archive_sha256="b" * 64,
                           exit_code=0, output="untrusted", cleanup=True, error="")
        self.host = runner.HostRunner(self.config, execute=self.execute)

    def execute(self, value):
        self.calls.append(value)
        return dict(self.result)

    def submit(self, value):
        (Path(self.config["requests"]) / "sample-1.json").write_text(json.dumps(value))

    def test_private_ledger_wins_over_forged_result_and_duplicate(self):
        self.submit(request())
        forged = Path(self.config["results"]) / "sample-1.json"
        forged.write_text('{"status":"completed"}')
        first = self.host.process_once()
        forged.write_text("tampered")
        second = self.host.process_once()
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(first, second)
        self.assertEqual(json.loads(forged.read_text()), first)
        self.assertEqual(first["request_sha256"], runner.request_digest(request()))

    def test_changed_request_rejected_and_running_never_retried(self):
        self.submit(request())
        self.host.process_once()
        self.submit(request(commit="b" * 40))
        with self.assertRaises(ValueError):
            self.host.process_once()
        self.assertEqual(len(self.calls), 1)
        record = Path(self.config["state"]) / "sample-1.json"
        record.write_text(json.dumps({"phase": "running", "request_sha256":
                                      runner.request_digest(request(commit="b" * 40))}))
        with self.assertRaises(RuntimeError):
            self.host.process_once()
        self.assertEqual(len(self.calls), 1)

    def test_cleanup_failure_blocks_other_jobs(self):
        self.result.update(status="timeout", cleanup=False, exit_code=None)
        self.submit(request())
        self.assertFalse(self.host.process_once()["cleanup"])
        with self.assertRaises(RuntimeError):
            self.host.process_once()
        self.assertEqual(len(self.calls), 1)

    def test_unknown_failure_is_redacted_and_requires_reconciliation(self):
        self.submit(request())
        self.host.execute = lambda value: (_ for _ in ()).throw(RuntimeError("SECRET"))
        result = self.host.process_once()
        self.assertEqual(result["status"], "blocked")
        self.assertNotIn("SECRET", json.dumps(result))
        self.assertFalse(result["cleanup"])

    def test_output_truncated(self):
        self.result["output"] = "x" * 50000
        self.submit(request())
        self.assertEqual(len(self.host.process_once()["output"]), 32768)

    def test_orphan_running_marker_blocks_every_new_request(self):
        atomic = Path(self.config["state"]) / "removed-job.json"
        atomic.write_text(json.dumps({"phase": "running", "request_sha256": "a" * 64}))
        self.submit(request())
        with self.assertRaises(RuntimeError):
            self.host.process_once()
        self.assertEqual(self.calls, [])

    def test_symlink_request_never_followed(self):
        if not hasattr(Path, "symlink_to"):
            self.skipTest("symlinks unavailable")
        target = Path(self.temp.name) / "outside.json"
        target.write_text(json.dumps(request()))
        try:
            (Path(self.config["requests"]) / "sample-1.json").symlink_to(target)
        except OSError:
            self.skipTest("symlink creation unavailable")
        with self.assertRaises(ValueError):
            self.host.process_once()
        self.assertEqual(self.calls, [])

    def test_fifo_request_is_rejected_before_blocking_open(self):
        if not hasattr(os, "mkfifo"):
            self.skipTest("FIFO unavailable")
        os.mkfifo(Path(self.config["requests"]) / "sample-1.json")
        with self.assertRaises(ValueError):
            self.host.process_once()
        self.assertEqual(self.calls, [])


class BoundaryTests(unittest.TestCase):
    def fixture(self):
        image = "sha256:" + "a" * 64
        boundary = runner.DockerBoundary({"image": image})
        value = {"Image": image, "Config": {
            "User": "65534:65534", "Entrypoint": ["python3"], "Cmd": runner.COMMAND[1:],
            "Env": runner.ENV, "Labels": {"isolation.run": "run"}, "Healthcheck": {"Test": ["NONE"]}},
            "HostConfig": {"NanoCpus": 2000000000, "Memory": runner.MEMORY,
                "MemorySwap": runner.MEMORY, "PidsLimit": 128, "NetworkMode": "none",
                "PidMode": "", "IpcMode": "private", "ReadonlyRootfs": True,
                "Privileged": False, "CapDrop": ["ALL"], "SecurityOpt": ["no-new-privileges=true"],
                "Tmpfs": {"/tmp": "rw,nosuid,nodev,size=128m,mode=1777", "/work": "rw,nosuid,nodev,size=1g,mode=1777"},
                "Mounts": [{"Type": "bind", "Source": "/host/stage", "Target": "/input", "ReadOnly": True}]},
            "Mounts": [{"Type": "bind", "Source": "/docker/normalized/stage", "Destination": "/input", "RW": False}]}
        return boundary, value

    def test_effective_boundary_allows_host_path_normalization(self):
        boundary, value = self.fixture()
        boundary.inspect = lambda identity: value
        boundary.verify_created("id", "/host/stage", "run")

    def test_effective_boundary_refuses_resource_network_mount_and_env_changes(self):
        boundary, value = self.fixture()
        for area, key, changed in (("HostConfig", "NanoCpus", 4000000000),
                                   ("HostConfig", "NetworkMode", "host"),
                                   ("HostConfig", "PidMode", "host"),
                                   ("Config", "Env", runner.ENV + ["SECRET=bad"]),
                                   ("Config", "Entrypoint", ["sh"])):
            mutation = copy.deepcopy(value)
            mutation[area][key] = changed
            boundary.inspect = lambda identity: mutation
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                boundary.verify_created("id", "/host/stage", "run")
        for changed in ({"Source": "/other"}, {"ReadOnly": False}):
            mutation = copy.deepcopy(value)
            mutation["HostConfig"]["Mounts"][0].update(changed)
            boundary.inspect = lambda identity: mutation
            with self.subTest(changed=changed), self.assertRaises(RuntimeError):
                boundary.verify_created("id", "/host/stage", "run")

    def test_coordinator_budget_checked_before_start(self):
        boundary = runner.DockerBoundary({"project":"pokemon", "image": "sha256:" + "a" * 64})
        boundary.tool = lambda args, **kwargs: "symphony-choubokyann" if args[-1] == "{{.Names}}" else ""
        boundary.inspect = lambda identity: {"State": {"Running": True},
            "HostConfig": {"NanoCpus": 4000000000, "Memory": runner.MEMORY, "MemorySwap": runner.MEMORY}}
        with self.assertRaises(RuntimeError):
            boundary.prerequisites()

    def test_unrelated_host_services_do_not_block_scoped_budget(self):
        image = 'sha256:' + 'a' * 64
        boundary = runner.DockerBoundary(dict(project='pokemon', image=image, requests='/checks-requests',
                    results='/checks-results', state='/private-state'))
        mounts = [dict(Type='bind', Source='/checks-requests', Target='/checks/requests', ReadOnly=False),
                  dict(Type='bind', Source='/checks-results', Target='/checks/results', ReadOnly=True)]
        active = dict(Config={'Labels':{'symphony.project':'pokemon'}}, State={'Running':True}, HostConfig=dict(NanoCpus=2000000000,
                    Memory=runner.MEMORY, MemorySwap=runner.MEMORY, Mounts=mounts),
                    Mounts=[dict(Type='bind', Source=m['Source'], Destination=m['Target'], RW=not m['ReadOnly']) for m in mounts])
        boundary.inspect = lambda name: active if name == 'symphony-choubokyann' else dict(Id=image, Config={'Env':runner.ENV})
        def tool(args, **kwargs):
            if args[0] == 'info': return json.dumps(['name=seccomp,profile=builtin'])
            if '--format' in args: return 'unrelated-database\nsymphony-choubokyann'
            return ''
        boundary.tool = tool
        boundary.prerequisites()

    def test_timeout_result_survives_expired_job_deadline(self):
        boundary = runner.DockerBoundary({'image':'sha256:'+'a'*64})
        def tool(args, **kwargs):
            if args[0] == 'wait' or (args[0] == 'logs' and not kwargs.get('cleanup')):
                raise TimeoutError('deadline expired')
            return 'timed out output' if args[0] == 'logs' else ''
        boundary.tool = tool
        code, output, status = boundary.run_created('c'*64)
        self.assertEqual((code, status), (None, 'timeout'))
        self.assertEqual(output, 'timed out output')

    def test_create_has_fixed_bounds_and_no_caller_command(self):
        args = runner.create_arguments("sha256:" + "a" * 64, "/trusted/stage", "run")
        self.assertEqual(args[args.index("--cpus") + 1], "2")
        self.assertEqual(args[args.index("--memory") + 1], "3g")
        self.assertIn("none", args)
        self.assertNotIn("--privileged", args)
        self.assertIn("/input/probe.py", " ".join(args))

    def test_timeout_always_removes_and_verifies(self):
        boundary = runner.DockerBoundary.__new__(runner.DockerBoundary)
        calls = []
        def tool(args, **kwargs):
            calls.append(args)
            if args[0] == "wait":
                raise TimeoutError("timeout")
            return "" if args[0] != "logs" else "untrusted"
        boundary.tool = tool
        code, output, status = boundary.run_created("c" * 64)
        self.assertIsNone(code)
        self.assertEqual(status, "timeout")
        self.assertEqual(output, "untrusted")
        self.assertTrue(boundary.cleanup("c" * 64))
        self.assertIn(["rm", "--force", "c" * 64], calls)
        self.assertIn(["container", "ls", "-aq", "--filter", "name=^/symphony-choubokyann-checks$"], calls)

    def test_failed_removal_does_not_claim_cleanup(self):
        boundary = runner.DockerBoundary.__new__(runner.DockerBoundary)
        boundary.tool = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError())
        self.assertFalse(boundary.cleanup("c" * 64))

    def test_nonzero_exit_is_failed_and_output_is_bounded(self):
        boundary = runner.DockerBoundary.__new__(runner.DockerBoundary)
        boundary.tool = lambda args, **kwargs: "17" if args[0] == "wait" else "z" * 40000
        code, output, status = boundary.run_created("c" * 64)
        self.assertEqual((code, status), (17, "failed"))
        self.assertEqual(len(output), 32768)


if __name__ == "__main__":
    unittest.main()
