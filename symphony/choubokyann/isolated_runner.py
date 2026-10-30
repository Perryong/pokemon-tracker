"""Trusted HOST transport. Install with its reviewed probe outside any checkout.

Requests and container output are untrusted data. No repository Python is
imported here. Image content auditing is a gateway prerequisite; inspect checks
configuration only. Run with Python -I from the reviewed installation.
"""
import argparse
from contextlib import contextmanager
import hashlib
import importlib.util
import itertools
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile
import threading
import time
import uuid
import urllib.request

NAME = "symphony-choubokyann-checks"
ENV = ["PATH=/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin", "LANG=C.UTF-8"]
MEMORY = 3 * 1024 ** 3
COMMAND = ["python3", "-I", "/input/probe.py", "--run", "/input/job.json"]


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def request_digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def validate_request(value, project, filename):
    keys = {"version", "job_id", "project", "commit", "suite"}
    if (not isinstance(value, dict) or set(value) != keys
            or type(value["version"]) is not int or value["version"] != 1
            or not isinstance(value["job_id"], str)
            or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", value["job_id"])
            or filename != value["job_id"] + ".json"
            or not isinstance(project, str) or not re.fullmatch(r"[a-z][a-z0-9-]{0,39}", project) or value["project"] != project
            or not isinstance(value["commit"], str)
            or not re.fullmatch(r"[0-9a-f]{40}", value["commit"])
            or value["suite"] not in ("coordinator", "sales-agent")):
        raise ValueError("Request does not match the fixed contract")


def read_json(path, limit=1048576):
    before = path.lstat()
    if (not stat.S_ISREG(before.st_mode) or path.is_symlink()
            or getattr(before, "st_file_attributes", 0) & 0x400):
        raise ValueError("Unsafe or oversized JSON file")
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    with os.fdopen(fd, "rb") as stream:
        metadata = os.fstat(stream.fileno())
        if (not stat.S_ISREG(metadata.st_mode) or metadata.st_size > limit
                or (before.st_ino, before.st_dev) != (metadata.st_ino, metadata.st_dev)):
            raise ValueError("Unsafe or oversized JSON file")
        content = stream.read(limit + 1)
    if len(content) > limit:
        raise ValueError("Unsafe or oversized JSON file")
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result
    return json.loads(content.decode("utf-8"), object_pairs_hook=pairs)


def atomic_json(path, value):
    fd, temporary = tempfile.mkstemp(prefix=".runner-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(canonical(value))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        if os.name != "nt":
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def machine_lock():
    # Fixed per-host-user location, independent of caller-controlled transport.
    path = Path.home() / ".symphony-isolated-runner.lock"
    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "r+b") as stream:
        if os.name == "nt":
            import msvcrt
            stream.write(b"0")
            stream.flush()
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            if os.name == "nt":
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


def command(args, timeout=30, max_output=1048576, output_file=None):
    """Drain output with a fixed memory bound; never print tool exceptions."""
    env = {key: os.environ[key] for key in ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP")
           if key in os.environ}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
               GIT_TERMINAL_PROMPT="0", GIT_NO_REPLACE_OBJECTS="1")
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               env=env, cwd=tempfile.gettempdir())
    chunks, size, overflow, read_failed = [], [0], [False], [False]
    destination = open(output_file, "xb") if output_file is not None else None
    def drain():
        try:
            while True:
                block = process.stdout.read(4096)
                if not block:
                    return
                available = max_output - size[0]
                if available > 0:
                    if destination is None:
                        chunks.append(block[:available])
                    else:
                        destination.write(block[:available])
                    size[0] += min(available, len(block))
                if destination is not None and len(block) > available:
                    overflow[0] = True
                    process.kill()
                    return
        except Exception:
            read_failed[0] = True
            process.kill()
    reader = threading.Thread(target=drain, daemon=True)
    reader.start()
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)
        raise TimeoutError("Host operation timed out") from None
    finally:
        reader.join(timeout=10)
        process.stdout.close()
        if destination is not None:
            destination.close()
    if reader.is_alive() or process.returncode or overflow[0] or read_failed[0]:
        raise RuntimeError("Host operation failed")
    return b"".join(chunks).decode("utf-8", errors="replace").strip()


def create_arguments(image, stage, run_id):
    return ["create", "--name", NAME, "--label", "isolation.run=" + run_id,
            "--restart", "no", "--no-healthcheck", "--cpus", "2", "--memory", "3g",
            "--memory-swap", "3g", "--pids-limit", "128", "--network", "none",
            "--ipc", "private", "--user", "65534:65534", "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges=true", "--read-only",
            "--tmpfs", "/tmp:rw,nosuid,nodev,size=128m,mode=1777",
            "--tmpfs", "/work:rw,nosuid,nodev,size=1g,mode=1777",
            "--log-driver", "local", "--log-opt", "max-size=1m", "--log-opt", "max-file=1",
            "--log-opt", "compress=false",
            "--mount", "type=bind,source=" + stage + ",target=/input,readonly",
            "--entrypoint", "python3", image, "-I", "/input/probe.py", "--run", "/input/job.json"]


def ensure_commit(config, commit):
    git = ["git", "--no-replace-objects", "-C", config["repository"],
           "-c", "core.hooksPath=" + os.devnull, "-c", "credential.helper=",
           "-c", "http.extraHeader=", "-c", "protocol.allow=never", "-c", "protocol.https.allow=always"]
    if command(git + ["remote", "get-url", "origin"]) != config["origin"]:
        raise RuntimeError("Repository origin is not registered")
    try:
        found = command(git + ["rev-parse", "--verify", commit + "^{commit}"])
    except RuntimeError:
        found = None
    if found != commit:
        command(git + ["fetch", "--no-tags", "--no-write-fetch-head", "--no-recurse-submodules", config["origin"], commit], timeout=60)
        found = command(git + ["rev-parse", "--verify", commit + "^{commit}"])
    if found != commit:
        raise RuntimeError("Exact commit unavailable after fetch")
    return git


def registered_origin(registry_path, project):
    # Trusted installed registry module, never the source candidate's module.
    path = Path(__file__).resolve().with_name("registry.py")
    spec = importlib.util.spec_from_file_location("trusted_registry", path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    record = module.select_project(registry_path, project)
    # Unauthenticated metadata read: private/inaccessible repos fail closed.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    request = urllib.request.Request("https://api.github.com/repos/" + record["repo"], headers={"Accept":"application/vnd.github+json", "User-Agent":"isolated-check-host"})
    with opener.open(request, timeout=20) as response:
        body = response.read(65537)
    if len(body) > 65536:
        raise ValueError("Repository metadata exceeds bound")
    metadata = json.loads(body)
    if metadata.get("private") is not False or metadata.get("full_name") != record["repo"]:
        raise ValueError("Repository must be canonical and public")
    return "https://github.com/" + record["repo"] + ".git"


class DockerBoundary:
    def __init__(self, config):
        self.config = config

    def tool(self, args, **kwargs):
        cleanup = kwargs.pop("cleanup", False)
        if not cleanup and hasattr(self, "job_deadline"):
            remaining = self.job_deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Bounded host job expired")
            kwargs["timeout"] = min(kwargs.get("timeout", 30), remaining)
        endpoint = "npipe:////./pipe/docker_engine" if os.name == "nt" else "unix:///var/run/docker.sock"
        return command(["docker", "--host", endpoint] + args, **kwargs)

    def inspect(self, target):
        value = json.loads(self.tool(["inspect", target]))
        if len(value) != 1:
            raise RuntimeError("Unexpected inspect result")
        return value[0]

    def prerequisites(self):
        if self.tool(["container", "ls", "-aq", "--filter", "name=^/" + NAME + "$"]):
            raise RuntimeError("Test slot occupied; reconcile on host")
        active = self.inspect("symphony-choubokyann")
        host = active["HostConfig"]
        if active.get("Config", {}).get("Labels", {}).get("symphony.project") != self.config["project"]:
            raise RuntimeError("Active coordinator project differs from host registration")
        if (not active["State"]["Running"] or host["NanoCpus"] != 2000000000
                or host["Memory"] != MEMORY or host["MemorySwap"] != MEMORY):
            raise RuntimeError("Coordinator must be running at the fixed 2 CPU/3 GiB budget")
        declared, effective = host.get("Mounts") or [], active.get("Mounts") or []
        for key, target, writable in (("requests", "/checks/requests", True), ("results", "/checks/results", False)):
            expected = [m for m in declared if m.get("Target") == target]
            actual = [m for m in effective if m.get("Destination") == target]
            if (len(expected) != 1 or expected[0].get("Type") != "bind"
                    or expected[0].get("Source") != self.config[key]
                    or bool(expected[0].get("ReadOnly")) == writable
                    or len(actual) != 1 or actual[0].get("Type") != "bind"
                    or actual[0].get("RW") is not writable):
                raise RuntimeError("Coordinator transport mount mismatch")
        if any(m.get("Type") == "npipe" or "docker.sock" in m.get("Source", "")
               or "docker.sock" in m.get("Destination", "") for m in effective):
            raise RuntimeError("Coordinator must not mount a Docker socket")
        private = Path(self.config["state"])
        for mount in declared:
            if mount.get("Type") != "bind":
                continue
            source = Path(mount["Source"])
            if source == private or source in private.parents:
                raise RuntimeError("Host ledger must not be mounted into the coordinator")
            if os.name != "nt" and any(source == socket or source in socket.parents
                                      for socket in (Path("/var/run/docker.sock"), Path("/run/docker.sock"))):
                raise RuntimeError("Coordinator mount could expose the Docker socket")
        if "name=seccomp,profile=builtin" not in json.loads(self.tool(["info", "--format", "{{json .SecurityOptions}}"] )):
            raise RuntimeError("Builtin seccomp is required")
        image = self.inspect(self.config["image"])
        cfg = image["Config"]
        if (image["Id"] != self.config["image"] or any(cfg.get(k) for k in ("Volumes", "Entrypoint", "Cmd", "OnBuild"))
                or sorted(cfg.get("Env") or []) != sorted(ENV)):
            raise RuntimeError("Image identity or configuration mismatch")

    def verify_created(self, identity, stage, run_id):
        value = self.inspect(identity)
        h, c = value["HostConfig"], value["Config"]
        expected = {"NanoCpus": 2000000000, "Memory": MEMORY, "MemorySwap": MEMORY,
                    "PidsLimit": 128, "NetworkMode": "none", "PidMode": "", "IpcMode": "private",
                    "ReadonlyRootfs": True, "Privileged": False}
        mounts = value.get("Mounts", [])
        binds = [m for m in mounts if m["Type"] == "bind"]
        requested = h.get("Mounts") or []
        if (any(h.get(k) != v for k, v in expected.items())
                or c.get("User") != "65534:65534" or value.get("Image") != self.config["image"]
                or c.get("Entrypoint") != ["python3"] or c.get("Cmd") != COMMAND[1:]
                or sorted(c.get("Env") or []) != sorted(ENV)
                or c.get("Labels", {}).get("isolation.run") != run_id
                or any(h.get(k) for k in ("CapAdd", "Devices", "DeviceRequests", "PortBindings", "Binds"))
                or h.get("CapDrop") != ["ALL"]
                or h.get("SecurityOpt") != ["no-new-privileges=true"]
                or c.get("Healthcheck", {}).get("Test") != ["NONE"]
                or h.get("Tmpfs") != {"/tmp": "rw,nosuid,nodev,size=128m,mode=1777", "/work": "rw,nosuid,nodev,size=1g,mode=1777"}
                or len(requested) != 1 or requested[0].get("Type") != "bind"
                or requested[0].get("Source") != stage or requested[0].get("Target") != "/input"
                or requested[0].get("ReadOnly") is not True
                or len(binds) != 1
                or binds[0].get("Destination") != "/input" or binds[0].get("RW") is not False
                or any(m["Type"] not in ("bind", "tmpfs") for m in mounts)
                or any(m["Type"] == "tmpfs" and m["Destination"] not in ("/tmp", "/work") for m in mounts)):
            raise RuntimeError("Effective container boundary mismatch")

    def run_created(self, identity):
        self.tool(["start", identity])
        try:
            code = self.tool(["wait", identity], timeout=300)
            if not re.fullmatch(r"\d+", code):
                raise RuntimeError("Invalid exit code")
            code, status = int(code), "completed" if int(code) == 0 else "failed"
        except TimeoutError:
            code, status = None, "timeout"
        output = self.tool(["logs", "--tail", "1000", identity], max_output=32768, cleanup=True)
        return code, output[:32768], status

    def cleanup(self, identity):
        try:
            self.tool(["rm", "--force", identity], cleanup=True)
            return not self.tool(["container", "ls", "-aq", "--filter", "name=^/" + NAME + "$"], cleanup=True)
        except Exception:
            return False

    def __call__(self, request):
        result = dict(status="blocked", archive_sha256=None, exit_code=None,
                      output="", cleanup=True, error="Host prerequisite or boundary check failed")
        identity, attempted, directory = None, False, None
        run_id = uuid.uuid4().hex
        self.job_deadline = min(time.monotonic() + 300, getattr(self, "service_deadline", float("inf")))
        old_sentinel = os.environ.get("ISOLATION_PARENT_SENTINEL")
        os.environ["ISOLATION_PARENT_SENTINEL"] = "SYNTHETIC-NOT-A-CREDENTIAL"
        try:
            self.prerequisites()
            git = ensure_commit(self.config, request["commit"])
            directory = tempfile.TemporaryDirectory(prefix="isolated-host-")
            stage = Path(directory.name) / "input"
            stage.mkdir(mode=0o755)
            sentinel = Path(directory.name) / "outside-sentinel"
            sentinel.write_text("SYNTHETIC-NOT-A-CREDENTIAL")
            archive = stage / "source.tar"
            command(git + ["archive", "--format=tar", request["commit"]],
                    output_file=archive, max_output=256 * 1024 * 1024)
            # Only the installed sibling probe is imported, never checkout paths.
            probe = Path(__file__).resolve().with_name("isolation_probe.py")
            spec = importlib.util.spec_from_file_location("trusted_isolation_probe", probe)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.validate_archive(archive)
            with archive.open("rb") as stream:
                result["archive_sha256"] = hashlib.file_digest(stream, "sha256").hexdigest()
            shutil.copyfile(probe, stage / "probe.py")
            atomic_json(stage / "job.json", {"sentinel_path": str(sentinel), "host_pid": os.getpid(),
                                            "suite": request["suite"]})
            for path in stage.iterdir():
                path.chmod(0o644)
            if "," in str(stage):
                raise RuntimeError("Unsupported staging path")
            attempted = True
            identity = self.tool(create_arguments(self.config["image"], str(stage), run_id))
            if not re.fullmatch(r"[a-f0-9]{64}", identity):
                identity = None
                raise RuntimeError("Uncertain create")
            self.verify_created(identity, str(stage), run_id)
            result["exit_code"], result["output"], result["status"] = self.run_created(identity)
            result["error"] = ""
        except TimeoutError:
            result.update(status="timeout", error="Bounded host job expired")
        except Exception:
            pass  # Deliberately redact tool stderr, exception payloads and host paths.
        finally:
            if attempted and identity is None:
                try:
                    owned = json.loads(self.tool(["inspect", NAME], cleanup=True))[0]
                    if owned["Config"].get("Labels", {}).get("isolation.run") == run_id:
                        identity = owned["Id"]
                except Exception:
                    pass
            if attempted:
                result["cleanup"] = bool(identity and self.cleanup(identity))
                if not result["cleanup"]:
                    result.update(status="blocked", error="Cleanup uncertain; reconcile on host")
            if directory is not None:
                try:
                    directory.cleanup()
                except OSError:
                    result.update(status="blocked", cleanup=False, error="Staging cleanup uncertain; reconcile on host")
            if old_sentinel is None:
                os.environ.pop("ISOLATION_PARENT_SENTINEL", None)
            else:
                os.environ["ISOLATION_PARENT_SENTINEL"] = old_sentinel
        return result


class HostRunner:
    def __init__(self, config, execute=None):
        self.config = config
        self.execute = execute or DockerBoundary(config)

    def process_once(self):
        c = self.config
        state = Path(c["state"])
        if (state / "blocked.json").exists():
            raise RuntimeError("Host cleanup reconciliation required")
        for previous in state.glob("*.json"):
            if read_json(previous).get("phase") == "running":
                raise RuntimeError("Uncertain previous job; host reconciliation required")
        candidates = list(itertools.islice(Path(c["requests"]).glob("*.json"), 257))
        if len(candidates) > 256:
            raise RuntimeError("Request transport exceeds the bounded queue limit")
        for path in sorted(candidates):
            value = read_json(path, 4096)
            validate_request(value, c["project"], path.name)
            digest = request_digest(value)
            ledger = state / path.name
            if ledger.exists():
                record = read_json(ledger)
                if record["request_sha256"] != digest:
                    raise ValueError("Job ID already belongs to another request")
                if record["phase"] != "finished":
                    raise RuntimeError("Uncertain previous job; host reconciliation required")
                atomic_json(Path(c["results"]) / path.name, record["result"])
                continue
            atomic_json(ledger, {"phase": "running", "request_sha256": digest})
            result = {**value, "request_sha256": digest, "image": c["image"]}
            try:
                result.update(self.execute(value))
            except Exception:
                result.update(status="blocked", archive_sha256=None, exit_code=None,
                              output="", cleanup=False, error="Host execution uncertain; reconcile on host")
            result["output"] = result["output"][:32768]
            if not result["cleanup"]:
                atomic_json(state / "blocked.json", {"job_id": value["job_id"]})
            atomic_json(ledger, {"phase": "finished", "request_sha256": digest, "result": result})
            atomic_json(Path(c["results"]) / path.name, result)
            return result
        # Existing finished requests are republished from private state, never rerun.
        return record["result"] if "record" in locals() else None


def load_config(path):
    c = read_json(path)
    if (set(c) != {"project", "registry", "repository", "image", "requests", "results", "state"}
            or not isinstance(c["project"], str) or not isinstance(c["image"], str)
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", c["image"])):
        raise ValueError("Invalid host configuration")
    registry = Path(c["registry"])
    if not registry.is_absolute() or registry.is_symlink():
        raise ValueError("Registry must be a trusted absolute file")
    c["origin"] = registered_origin(registry, c["project"])
    paths = []
    for key in ("repository", "requests", "results", "state"):
        p = Path(c[key])
        if not p.is_absolute() or p.is_symlink() or not p.is_dir():
            raise ValueError("Host paths must be existing absolute directories")
        c[key] = str(p.resolve())
        paths.append(p.resolve())
    if any(a == b or a in b.parents or b in a.parents for i, a in enumerate(paths) for b in paths[i + 1:]):
        raise ValueError("Host directories must be separate")
    installed = Path(__file__).resolve()
    if any(p == installed.parent or p in installed.parents for p in paths):
        raise ValueError("Trusted scripts must be installed separately from repository and transport")
    if os.name != "nt":
        stat = Path(c["state"]).stat()
        if stat.st_uid != os.getuid() or stat.st_mode & 0o077:
            raise ValueError("State must be host-owned and private")
    # Windows ACL isolation and coordinator's read-only result mount are required
    # installation checks; pathlib cannot attest Windows ACLs or mount topology.
    return c


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--once", action="store_true")
    modes.add_argument("--serve", action="store_true")
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        with machine_lock():
            runner = HostRunner(config)
            while True:
                runner.process_once()
                if args.once:
                    return 0
                time.sleep(1)
    except Exception:
        print("ISOLATED_HOST_RUNNER_BLOCKED")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
