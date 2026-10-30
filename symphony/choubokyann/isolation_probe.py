"""Reviewed boundary helper, copied separately from the untrusted commit.

Host use parses tar headers only. Container use extracts and runs untrusted code.
Never import repository modules before boundary checks have succeeded.
"""
import argparse
import json
import os
from pathlib import Path, PurePosixPath
import socket
import subprocess
import sys
import tarfile


def validate_archive(path, max_bytes=256 * 1024 * 1024):
    forbidden = {".git", ".codex", ".aws", ".ssh", ".env", "auth.json", "workpad", ".workpad", ".symphony"}
    total = count = 0
    seen = set()
    with tarfile.open(path, "r:") as archive:
        for item in archive:
            name = item.name.rstrip("/")
            parts = PurePosixPath(name).parts
            if (not name or name.startswith("/") or "\\" in name or ":" in name
                    or PurePosixPath(name).as_posix() != name or item.size < 0
                    or any(part in ("..", ".") for part in name.split("/"))
                    or any(part.lower() in forbidden for part in parts)
                    or name in seen or not (item.isfile() or item.isdir())):
                raise ValueError("Archive contains an unsafe path or entry type")
            seen.add(name)
            total += item.size
            count += 1
            if total > max_bytes or count > 50000:
                raise ValueError("Archive exceeds bounded staging limits")
    if not count:
        raise ValueError("Empty source archive")
    return count


def validate_argv(value):
    if (not isinstance(value, list) or not value
            or any(not isinstance(arg, str) or not arg or "\0" in arg for arg in value)):
        raise ValueError("Command must be a nonempty JSON string array")
    return value


def inaccessible(path):
    try:
        with open(path, "rb") as stream:
            stream.read(1)
        return False
    except (OSError, ValueError):
        return True


def boundary_checks(job):
    failures = []
    if os.getuid() == 0:
        failures.append("nonroot")
    if "ISOLATION_PARENT_SENTINEL" in os.environ:
        failures.append("parent-environment")
    paths = [job["sentinel_path"], "/proc/1/root" + job["sentinel_path"],
             "/proc/%s/environ" % job["host_pid"],
             "/proc/%s/root%s" % (job["host_pid"], job["sentinel_path"]),
             "/root/.codex/auth.json", "/root/.config/gh/hosts.yml",
             "/config/coordinator.toml", "/var/run/docker.sock", "/run/docker.sock",
             "/root/.aws/credentials", "/root/.ssh/id_ed25519"]
    for index, path in enumerate(paths):
        if not inaccessible(path):
            failures.append("host-path-%s" % index)
    # No published service, host bridge, or external network may be reachable.
    for address in ("1.1.1.1", "172.17.0.1", "host.docker.internal"):
        try:
            with socket.create_connection((address, 443), timeout=1):
                failures.append("network")
        except OSError:
            pass
    if Path("/var/run/docker.sock").exists() or Path("/run/docker.sock").exists():
        failures.append("docker-socket")
    if failures:
        raise RuntimeError("Boundary probe failed: " + ",".join(failures))
    print("BOUNDARY_PROBE_PASS synthetic checks only", flush=True)


def run(job_path):
    job = json.loads(Path(job_path).read_text())
    boundary_checks(job)
    archive = Path("/input/source.tar")
    validate_archive(archive)
    source = Path("/work/source")
    source.mkdir()
    with tarfile.open(archive, "r:") as stream:
        # All links, special files and noncanonical names were rejected above.
        stream.extractall(source, filter="data")
    commands = [validate_argv(job["argv"])] if job.get("argv") else [
        [sys.executable, "-m", "unittest", "discover", "-s", "symphony/choubokyann", "-p", "test_*.py"],
        [sys.executable, "-m", "unittest", "discover", "-s", ".github/scripts", "-p", "test_issue_claim.py"],
    ]
    # No install fallback: missing imports/tools are hard failures, offline.
    for index, command in enumerate(commands):
        print("CHECK_START %s" % index, flush=True)
        result = subprocess.run(command, cwd=source, env=dict(os.environ), check=False)
        if result.returncode:
            print("CHECK_FAIL %s exit=%s" % (index, result.returncode), flush=True)
            return 1
        print("CHECK_PASS %s" % index, flush=True)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--validate")
    group.add_argument("--run")
    args = parser.parse_args()
    try:
        if args.validate:
            validate_archive(args.validate)
        else:
            sys.exit(run(args.run))
    except Exception:
        # Do not print paths, values or unexpected exception payloads.
        print("ISOLATION_CHECK_FAILED", file=sys.stderr)
        sys.exit(1)
