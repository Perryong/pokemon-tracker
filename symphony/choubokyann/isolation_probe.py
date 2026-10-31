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


SALES_SCENARIOS = ('eligible', 'out-of-policy', 'expired', 'opt-out', 'material-facts')


def validate_sales_demo(scenario, value):
    """Validate effects and policy outcomes, never trust exit zero or model prose."""
    if scenario not in SALES_SCENARIOS or not isinstance(value, dict):
        raise ValueError('Invalid Sales demo result')
    count = dict(zip(SALES_SCENARIOS, (2, 1, 0, 1, 1)))[scenario]
    if (value.get('scenario') != scenario or value.get('harness') != 'deepagents.create_deep_agent'
            or value.get('marketplace') != 'deterministic_simulation'
            or value.get('model_transport') != 'scripted_offline_fixture'
            or not isinstance(value.get('outbound'), list) or len(value['outbound']) != count
            or type(value.get('rounds')) is not int or value['rounds'] != count
            or value.get('opted_out') is not (scenario == 'opt-out')):
        raise ValueError('Sales demo identity or effects mismatch')
    results = value.get('tool_results')
    if not isinstance(results, list) or len(results) != 3 or any(not isinstance(r, dict) for r in results):
        raise ValueError('Sales demo tool results missing')
    if scenario == 'eligible':
        proposal = value.get('proposal')
        if (not isinstance(proposal, dict) or proposal.get('status') != 'awaiting_operator_approval'
                or type(proposal.get('amount_minor')) is not int or proposal['amount_minor'] != 4500
                or proposal.get('currency') != 'SGD' or proposal.get('dispatchable') is not False
                or [r.get('status') for r in results] != ['sent', 'sent', 'awaiting_operator_approval']):
            raise ValueError('Sales proposal is not the expected approval-only artifact')
    else:
        reason = {'out-of-policy': 'price_out_of_mandate', 'expired': 'expired_mandate',
                  'opt-out': 'seller_opt_out', 'material-facts': 'reassessment_required'}[scenario]
        denied = results if scenario == 'expired' else results[1:]
        if (value.get('proposal') is not None
                or any(r.get('status') != 'rejected' or r.get('reason') != reason for r in denied)
                or (scenario != 'expired' and results[0].get('status') != 'sent')):
            raise ValueError('Sales demo did not enforce the expected denial')
    reassessment = value.get('reassessment')
    if scenario == 'material-facts':
        if (not isinstance(reassessment, dict) or reassessment.get('kind') != 'market_reassessment_request'
                or reassessment.get('transport') != 'local_fixture_unauthenticated'
                or reassessment.get('requires_replacement_mandate') is not True
                or reassessment.get('facts') != {'condition': 'creased'}):
            raise ValueError('Sales reassessment mismatch')
    elif reassessment is not None:
        raise ValueError('Unexpected Sales reassessment')


def run_suite(source, job):
    suite = job.get('suite', 'coordinator')
    if suite not in ('coordinator', 'sales-agent') or ('suite' in job and 'argv' in job):
        raise ValueError('Invalid fixed suite')
    if suite == 'sales-agent':
        directory = source / 'sales_agent'
        env = dict(os.environ, PYTHONPATH=str(directory / 'src'),
                   PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', LANGSMITH_TRACING='false', LANGCHAIN_TRACING_V2='false')
        commands = [[sys.executable, '-m', 'pip', 'check'],
                    [sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider']]
        for index, command in enumerate(commands):
            print('SALES_CHECK_START %s' % index, flush=True)
            result = subprocess.run(command, cwd=directory, env=env, check=False, timeout=120)
            if result.returncode:
                raise RuntimeError('Sales dependency or pytest check failed')
            print('SALES_CHECK_PASS %s' % index, flush=True)
        for scenario in SALES_SCENARIOS:
            result = subprocess.run([sys.executable, '-m', 'pokemon_sales', '--scenario', scenario],
                                    cwd=directory, env=env, check=False, timeout=45,
                                    capture_output=True, text=True)
            if result.returncode:
                raise RuntimeError('Sales demo command failed')
            validate_sales_demo(scenario, json.loads(result.stdout))
            print('SALES_DEMO_PASS %s' % scenario, flush=True)
        return 0
    # argv is retained for the historical host-only manual pilot, never accepted
    # alongside a named suite or through the native request contract.
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


def run(job_path):
    job = json.loads(Path(job_path).read_text())
    boundary_checks(job)
    archive = Path('/input/source.tar')
    validate_archive(archive)
    source = Path('/work/source')
    source.mkdir()
    with tarfile.open(archive, 'r:') as stream:
        # All links, special files and noncanonical names were rejected above.
        stream.extractall(source, filter='data')
    return run_suite(source, job)


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
