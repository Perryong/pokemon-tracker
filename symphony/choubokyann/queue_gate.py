#!/usr/bin/env python3
"""Read-only evidence gate. A zero check exit permits one coordinator cycle.

Evidence is never claim/readiness authority. A pending cycle survives failure,
interruption and new evidence until explicit acknowledge or deliberate retry.
Connections exceeding 100 entries fail closed instead of using partial evidence.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

from registry import FIELDS, load_registry, select_project, validate_record


def default_scope():
    return load_registry(Path(__file__).with_name("projects.json"))["projects"]["pokemon"]


PAGE = "pageInfo { hasNextPage hasPreviousPage }"
REPOSITORY = "repository { nameWithOwner isPrivate }"
TIMELINE = """timelineItems(first:100) { nodes {
 __typename ... on Node { id }
 ... on IssueComment { body updatedAt }
 ... on CrossReferencedEvent { createdAt source {
   __typename ... on PullRequest { number repository { nameWithOwner isPrivate } }
 } }
} pageInfo { hasNextPage hasPreviousPage } }"""
INVENTORY_QUERY = """query QueueInventory($owner:String!,$repo:String!,$projectOwner:String!,$projectNumber:Int!,$controlLabel:String!,$queueLabel:String!) {
 viewer { login }
 repository(owner:$owner,name:$repo) {
 nameWithOwner isPrivate
 control: issues(first:100,labels:[$controlLabel],states:OPEN) {
 nodes { number } pageInfo { hasNextPage hasPreviousPage } }
 queue: issues(first:100,labels:[$queueLabel],states:[OPEN,CLOSED]) {
 nodes { number } pageInfo { hasNextPage hasPreviousPage } }
 pullRequests(first:100,states:OPEN) {
 nodes { number author { login } } pageInfo { hasNextPage hasPreviousPage } }
 }
 user(login:$projectOwner) { projectV2(number:$projectNumber) { number items(first:100) {
 nodes { content { __typename ... on Issue { number repository { nameWithOwner isPrivate } } }
 fieldValueByName(name:"Status") { ... on ProjectV2ItemFieldSingleSelectValue { name } } }
 pageInfo { hasNextPage hasPreviousPage }
 } } }
}"""
ISSUE_QUERY = """query QueueIssue($number:Int!,$owner:String!,$repo:String!) {
 repository(owner:$owner,name:$repo) { issue(number:$number) {
 id number title body state stateReason updatedAt url """ + REPOSITORY + """
 labels(first:100) { nodes { name } """ + PAGE + """ }
 assignees(first:100) { nodes { login } """ + PAGE + """ }
 blockedBy(first:100) { nodes { number state stateReason updatedAt """ + REPOSITORY + """ } """ + PAGE + """ }
 closedByPullRequestsReferences(first:100) { nodes { number """ + REPOSITORY + """ } """ + PAGE + """ }
 """ + TIMELINE + """ } } }"""
PR_QUERY = """query QueuePullRequest($number:Int!,$owner:String!,$repo:String!) {
 repository(owner:$owner,name:$repo) { pullRequest(number:$number) {
 id number title body state updatedAt headRefOid baseRefOid mergeable reviewDecision isDraft
 """ + REPOSITORY + TIMELINE + """
 reviews(first:100) { nodes { id state body submittedAt updatedAt author { login } } """ + PAGE + """ }
 reviewThreads(first:100) { nodes { id isResolved isOutdated comments(first:100) {
 nodes { id body updatedAt author { login } } """ + PAGE + """ } } """ + PAGE + """ }
 commits(last:1) { nodes { commit { oid statusCheckRollup { state contexts(first:100) {
 nodes { __typename ... on CheckRun { name status conclusion startedAt completedAt detailsUrl }
 ... on StatusContext { context state targetUrl createdAt } } """ + PAGE + """
 } } } } pageInfo { hasNextPage hasPreviousPage } }
 } } }"""


class GateError(Exception):
    """Safe, public error reason; raw GitHub stderr is never shown."""


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def complete(value):
    """Reject every selected truncated or malformed connection."""
    if isinstance(value, dict):
        if "nodes" in value:
            page = value.get("pageInfo")
            if not isinstance(page, dict) or not isinstance(value["nodes"], list):
                raise GateError("malformed connection")
            # commits(last:1) intentionally selects only the current head; its
            # earlier commits are already represented by headRefOid.
            if page.get("hasNextPage") is not False:
                raise GateError("truncated connection")
            if page.get("hasPreviousPage") is not False and not value.get("headOnly", False):
                raise GateError("truncated connection")
        for child in value.values():
            complete(child)
    elif isinstance(value, list):
        for child in value:
            complete(child)


def canonical(value, scope):
    repo = value.get("repository", value)
    if repo.get("nameWithOwner") != scope["repo"] or repo.get("isPrivate") is not False:
        raise GateError("repository scope mismatch")


class GitHub:
    def __init__(self):
        self.deadline = time.monotonic() + 100

    def __call__(self, query, **variables):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise GateError("GitHub read deadline exceeded")
        env = os.environ.copy()
        if env.get("SYMPHONY_QUEUE_TOKEN"):
            env["GH_TOKEN"] = env["SYMPHONY_QUEUE_TOKEN"]
        payload = json.dumps({"query": query, "variables": variables})
        try:
            result = subprocess.run(["gh", "api", "graphql", "--input", "-"],
                                    input=payload, text=True, capture_output=True,
                                    timeout=min(20, remaining), check=False, env=env)
            if result.returncode:
                raise GateError("GitHub read failed")
            response = json.loads(result.stdout)
            if response.get("errors") or not isinstance(response.get("data"), dict):
                raise GateError("GitHub GraphQL read failed")
            return response["data"]
        except (OSError, subprocess.TimeoutExpired, ValueError) as exc:
            raise GateError("GitHub read failed") from exc


def snapshot(api, scope=None):
    scope = default_scope() if scope is None else scope
    validate_record(scope)
    owner, repo = scope["repo"].split("/")
    identity = {"owner": owner, "repo": repo}
    control = scope["control_issue"]
    data = api(INVENTORY_QUERY, **identity, projectOwner=scope["project_owner"],
               projectNumber=scope["project_number"], controlLabel=scope["control_label"],
               queueLabel=scope["queue_label"])
    complete(data)
    if data["viewer"]["login"] != scope["actor"]:
        raise GateError("actor mismatch")
    repository = data["repository"]
    canonical(repository, scope)
    controls = repository["control"]["nodes"]
    if [n["number"] for n in controls] != [control]:
        raise GateError("control label must uniquely select registered control issue")
    project = data["user"]["projectV2"]
    if project["number"] != scope["project_number"]:
        raise GateError("project mismatch")
    statuses = {}
    for item in project["items"]["nodes"]:
        content = item.get("content")
        if not content or content.get("__typename") != "Issue":
            continue
        repo = content.get("repository", {})
        # Filter before digesting or persisting: private/other-repo evidence
        # cannot alter the public canonical queue snapshot.
        if repo.get("nameWithOwner") != scope["repo"] or repo.get("isPrivate") is not False:
            continue
        number = content["number"]
        if number in statuses:
            raise GateError("duplicate canonical project item")
        statuses[number] = (item.get("fieldValueByName") or {}).get("name")
    if statuses.get(control) != "In progress":
        raise GateError("control project status must be In progress")
    numbers = sorted(n["number"] for n in repository["queue"]["nodes"])
    if not numbers or len(numbers) != len(set(numbers)):
        raise GateError("empty or duplicate queue")
    evidence = {"registration": digest(scope)}
    loaded = {}

    def read_pr(number):
        details = api(PR_QUERY, number=number, **identity)["repository"]["pullRequest"]
        canonical(details, scope)
        if details["number"] != number:
            raise GateError("PR identity mismatch")
        # All older commits are represented by the current head hash.
        details["commits"]["headOnly"] = True
        complete(details)
        return digest(details)

    open_prs = {}
    for pr in repository["pullRequests"]["nodes"]:
        if (pr.get("author") or {}).get("login") == scope["actor"]:
            open_prs[str(pr["number"])] = read_pr(pr["number"])
    evidence["open_prs"] = open_prs

    def read_issue(number):
        if number not in loaded:
            obj = api(ISSUE_QUERY, number=number, **identity)["repository"]["issue"]
            complete(obj)
            canonical(obj, scope)
            if obj["number"] != number:
                raise GateError("issue identity mismatch")
            loaded[number] = obj
        return loaded[number]

    for number in [control] + numbers:
        if number in scope["excluded_issues"] or (number == control and number in numbers):
            raise GateError("excluded issue in queue")
        obj = read_issue(number)
        labels = {n["name"] for n in obj["labels"]["nodes"]}
        actors = {n["login"] for n in obj["assignees"]["nodes"]}
        allowed_states = {"OPEN"} if number == control else {"OPEN", "CLOSED"}
        if obj["state"] not in allowed_states or (scope["control_label"] if number == control else scope["queue_label"]) not in labels:
            raise GateError("issue label/state mismatch")
        if actors != {scope["actor"]} and (number == control or actors):
            raise GateError("issue assignee outside coordinator scope")
        if number not in statuses:
            raise GateError("queued issue missing from project")
        dependencies = []
        for dependency in obj["blockedBy"]["nodes"]:
            canonical(dependency, scope)
            dependencies.append(read_issue(dependency["number"]))
        prs = list(obj["closedByPullRequestsReferences"]["nodes"])
        for event in obj["timelineItems"]["nodes"]:
            source = event.get("source")
            if source and source.get("__typename") == "PullRequest":
                prs.append(source)
        pr_evidence = {}
        for pr in prs:
            canonical(pr, scope)
            pr_number = pr["number"]
            if str(pr_number) in pr_evidence:
                continue
            pr_evidence[str(pr_number)] = open_prs.get(str(pr_number)) or read_pr(pr_number)
        evidence[str(number)] = {"issue": digest(obj), "dependencies": digest(dependencies),
                                 "prs": pr_evidence, "status": statuses[number]}
    return {"fingerprint": digest(evidence), "issues": sorted(numbers)}


def save(path, state):
    fd, temporary = tempfile.mkstemp(prefix="queue-gate-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(state, stream, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def run(command, workspace, api=None, reason=None, expected_fingerprint=None, scope=None):
    """Return 0 for permission, 75 for unchanged, 1 for pending, 2 for errors."""
    directory = Path(workspace) / ".symphony/choubokyann"
    try:
        scope = default_scope() if scope is None else scope
        validate_record(scope)
        scope_id = digest(scope)
        directory.mkdir(parents=True, exist_ok=True)
        with (directory / "queue-gate.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            path = directory / "queue-gate.json"
            state = json.loads(path.read_text()) if path.exists() else {"version": 1, "recoveries": [], "scope": scope_id}
            if state.get("scope") != scope_id:
                raise GateError("state registration mismatch; preserve evidence and reconcile")
            if state.get("version") != 1:
                raise GateError("unsupported state")
            if command == "check" and state.get("pending"):
                return 1
            if command == "retry":
                if not reason or not reason.strip() or not state.get("pending"):
                    raise GateError("retry requires pending evidence and a reason")
                state["recoveries"].append({"at": datetime.now(timezone.utc).isoformat(),
                                            "reason": reason.strip(), "pending": state.pop("pending")})
                save(path, state)
                return 0
            if command not in ("check", "acknowledge", "inspect"):
                raise GateError("unknown command")
            if command == "acknowledge" and not state.get("pending"):
                raise GateError("no pending cycle to acknowledge")
            current = snapshot(api or GitHub(), scope)
            if command == "inspect":
                print(json.dumps(current, sort_keys=True))
                return 0
            if command == "acknowledge":
                if expected_fingerprint != current["fingerprint"]:
                    raise GateError("fresh evidence differs from reviewed fingerprint")
                state["acknowledged"] = current
                state.pop("pending")
            else:
                if state.get("acknowledged", {}).get("fingerprint") == current["fingerprint"]:
                    return 75
                state["pending"] = {"at": datetime.now(timezone.utc).isoformat(), "snapshot": current}
            save(path, state)
            return 0
    except (Exception,) as exc:
        # Never echo API payloads, stderr, tokens or arbitrary exception text.
        message = str(exc) if isinstance(exc, GateError) else "gate read/state failure"
        print("queue gate blocked: " + message, file=sys.stderr)
        return 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check", "inspect", "acknowledge", "retry"])
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--reason", help="public-safe recovery reason; retained locally")
    parser.add_argument("--expected-fingerprint", help="freshly inspected and reviewed evidence required for acknowledgement")
    parser.add_argument("--registry", default=os.environ.get("SYMPHONY_REGISTRY"))
    parser.add_argument("--project", default=os.environ.get("SYMPHONY_PROJECT"))
    args = parser.parse_args()
    if not args.registry or not args.project:
        parser.error("explicit --registry and --project (or SYMPHONY_ environment) required")
    try:
        selected = select_project(args.registry, args.project)
        scope = {key: selected[key] for key in FIELDS}
    except (ValueError, OSError, KeyError):
        print("queue gate blocked: invalid project registration", file=sys.stderr)
        return 2
    return run(args.command, args.workspace, reason=args.reason, expected_fingerprint=args.expected_fingerprint, scope=scope)


if __name__ == "__main__":
    sys.exit(main())
