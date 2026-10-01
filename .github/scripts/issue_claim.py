"""Serialized GitHub issue claims. Dispatch only through issue-claim.yml."""
import json
import os
import re
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPOS = {"ChouBokYann/pokemon-reselling", "Perryong/pokemon-tracker"}
PROJECT = "PVT_kwHOBwH5gM4BlVDy"
MARKER = "<!-- pokemon-coordination/v1 -->\n"
WORKFLOW = ".github/workflows/issue-claim.yml"


class ClaimError(Exception):
    """Public-safe operational error; never include raw API responses."""


def validate_request(r):
    if (r.get("repo") not in REPOS or not re.fullmatch(r"[1-9][0-9]*", str(r.get("issue", "")))
            or not re.fullmatch(r"[A-Za-z0-9._-]{1,80}", r.get("session", ""))
            or r.get("operation") not in {"claim", "release"}
            or not re.fullmatch(r"[1-9][0-9]*", str(r.get("run_id", "")))
            or not re.fullmatch(r"[A-Za-z0-9-]{1,39}", r.get("actor", ""))
            or not isinstance(r.get("override"), bool)):
        raise ClaimError("Invalid request. Use a canonical issue number and a non-secret session identifier.")
    for key in ("reason", "handoff"):
        if not isinstance(r.get(key), str) or len(r[key]) > 3000:
            raise ClaimError("Invalid reason or handoff (maximum 3000 characters).")
    if r["override"] and (r["operation"] != "release" or not r["reason"].strip()):
        raise ClaimError("Override is only for release and requires a reason.")
    if r["operation"] == "release" and not r["handoff"].strip():
        raise ClaimError("Release requires handoff context, checks, remaining work and blockers.")


def evaluate_claim(r, s):
    if s["permission"] not in {"write", "maintain", "admin"}: return "reject"
    active = s.get("active")
    same = active and active["actor"] == r["actor"] and active["session"] == r["session"]
    if r["operation"] == "release":
        if not active: return "reject"
        return "release" if same or (r["override"] and s["permission"] in {"maintain", "admin"}) else "reject"
    if s["state"] != "open" or not s["dependencies_ok"]: return "reject"
    if active:
        if not same or active["event"] == "releasing": return "reject"
        if set(s["assignments"]) - {r["actor"]}: return "reject"
        return "resume"
    return "accept" if s["ready"] and not s["assignments"] else "reject"


def pages(api, path, credential="local"):
    for page in range(1, 1001):
        result = api("GET", f"{path}?per_page=100&page={page}", credential=credential)
        if not isinstance(result, list): raise ClaimError("Unexpected list response; cannot verify state.")
        yield from result
        if len(result) < 100: return
    raise ClaimError("Pagination safety limit reached; maintainer review required.")


def active_claim(api, base, default_branch):
    active = None
    verified_runs = {}
    for comment in pages(api, base + "/comments"):
        body = comment.get("body", "")
        if not body.startswith(MARKER) or comment.get("user", {}).get("login") != "github-actions[bot]": continue
        if comment["user"].get("type") != "Bot": continue
        try: event = json.loads(body[len(MARKER):])
        except (ValueError, TypeError): raise ClaimError("Malformed trusted ledger event; maintainer reconciliation required.")
        if event.get("event") not in {"reserved", "accepted", "releasing", "released"}: continue
        run_id = str(event.get("run_id", ""))
        if not re.fullmatch(r"[1-9][0-9]*", run_id): raise ClaimError("Invalid ledger provenance.")
        if run_id not in verified_runs:
            repo_base = base.split("/issues/")[0]
            verified_runs[run_id] = api("GET", repo_base + "/actions/runs/" + run_id)
        run_info = verified_runs[run_id]
        if (run_info.get("path") != WORKFLOW or run_info.get("head_branch") != default_branch
                or run_info.get("event") != "workflow_dispatch"
                or run_info.get("actor", {}).get("login") != event.get("executor")):
            raise ClaimError("Unverified trusted ledger event; maintainer reconciliation required.")
        if not all(isinstance(event.get(k), str) and event[k] for k in ("actor", "session", "claim_id")):
            raise ClaimError("Incomplete trusted ledger event.")
        if event["event"] == "reserved":
            if active and active["claim_id"] != event["claim_id"]:
                raise ClaimError("Conflicting ledger reservations; maintainer reconciliation required.")
            active = event
        elif active and active["claim_id"] == event["claim_id"]:
            active = None if event["event"] == "released" else event
        else:
            raise ClaimError("Ledger transition without matching reservation.")
    return active


def section(body, name):
    match = re.search(r"^### " + re.escape(name) + r"\s*\n(.*?)(?=^### |\Z)", body or "", re.M | re.S)
    if not match or not match[1].strip(): raise ClaimError("Required dependency/blocker declarations are missing.")
    return match[1].strip()


def dependencies_ok(api, repo, number):
    visited, visiting = set(), set()

    def visit(current_repo, current_number, root=False):
        key = (current_repo, current_number)
        if key in visiting: raise ClaimError("Dependency cycle; maintainer resolution required.")
        if key in visited: return
        if len(visited) + len(visiting) >= 200: raise ClaimError("Dependency traversal limit; maintainer review required.")
        visiting.add(key)
        base = f"/repos/{current_repo}/issues/{current_number}"
        issue = api("GET", base, credential="read")
        if not root and (issue.get("state") != "closed" or issue.get("state_reason") != "completed"):
            raise ClaimError("An unresolved dependency blocks this claim.")
        declared = section(issue.get("body"), "Dependencies") if root else "None"
        if root and section(issue.get("body"), "Non-code blockers").lower() not in {"none", "resolved"}:
            raise ClaimError("Non-code blockers must be resolved before claiming.")
        children = list(pages(api, base + "/dependencies/blocked_by", "read"))
        summary = issue.get("issue_dependencies_summary")
        if not isinstance(summary, dict) or summary.get("total_blocked_by") != len(children):
            raise ClaimError("Dependency coverage cannot be verified; check access.")
        links = set()
        for child in children:
            prefix = "https://api.github.com/repos/"
            url = child.get("repository_url", "")
            child_repo = url[len(prefix):] if url.startswith(prefix) else ""
            if child_repo not in REPOS or not isinstance(child.get("number"), int):
                raise ClaimError("Unsupported or inaccessible dependency; maintainer review required.")
            links.add(f"https://github.com/{child_repo}/issues/{child['number']}")
            visit(child_repo, child["number"])
        if root and declared.lower() != "none":
            declared_links = re.findall(r"https://github\.com/[^\s<>]+/issues/[1-9][0-9]*", declared)
            if not declared_links or not set(declared_links).issubset(links):
                raise ClaimError("Declared dependencies must also be native blocked-by relationships.")
        visiting.remove(key); visited.add(key)

    visit(repo, int(number), True)
    return True


def project_item(api, issue_id):
    cursor = None
    while True:
        query = '''query($id:ID!,$cursor:String){node(id:$id){... on Issue{projectItems(first:100,after:$cursor){
          nodes{id project{id} fieldValueByName(name:"Status"){... on ProjectV2ItemFieldSingleSelectValue{
            name field{... on ProjectV2SingleSelectField{id options{id name}}}}}}
          pageInfo{hasNextPage endCursor}}}}}'''
        data = api("POST", "/graphql", {"query": query, "variables": {"id": issue_id, "cursor": cursor}}, "project")
        connection = data["data"]["node"]["projectItems"]
        for item in connection["nodes"]:
            if item["project"]["id"] == PROJECT:
                if not item.get("fieldValueByName"): raise ClaimError("Set the project's Status before claiming.")
                return item
        if not connection["pageInfo"]["hasNextPage"]: raise ClaimError("Issue must be added to the shared Project first.")
        cursor = connection["pageInfo"]["endCursor"]


def set_status(api, item, status):
    field = item["fieldValueByName"]["field"]
    option = next((o["id"] for o in field["options"] if o["name"] == status), None)
    if not option: raise ClaimError("Project status configuration is incomplete.")
    query = '''mutation($project:ID!,$item:ID!,$field:ID!,$value:String!){updateProjectV2ItemFieldValue(
      input:{projectId:$project,itemId:$item,fieldId:$field,value:{singleSelectOptionId:$value}}){projectV2Item{id}}}'''
    api("POST", "/graphql", {"query": query, "variables": {"project": PROJECT, "item": item["id"], "field": field["id"], "value": option}}, "project")


def run(r, api):
    validate_request(r)
    repo_base = "/repos/" + r["repo"]
    permission = api("GET", repo_base + "/collaborators/" + r["actor"] + "/permission")["permission"]
    if permission not in {"write", "maintain", "admin"}: raise ClaimError("Repository write permission is required.")
    default_branch = api("GET", repo_base)["default_branch"]
    base = repo_base + "/issues/" + r["issue"]
    issue = api("GET", base)
    if "pull_request" in issue: raise ClaimError("Claims apply to issues, not pull requests.")
    active = active_claim(api, base, default_branch)
    item = None
    if r["operation"] == "claim":
        dependencies_ok(api, r["repo"], r["issue"])
        item = project_item(api, issue["node_id"])
        if active and item["fieldValueByName"]["name"] not in {"Ready", "In progress", "In review"}:
            raise ClaimError("Existing work is no longer ready; resolve its Project status before resuming.")
    snapshot = dict(permission=permission, state=issue["state"], active=active,
                    assignments=[x["login"] for x in issue["assignees"]], dependencies_ok=True,
                    ready=bool(item and item["fieldValueByName"]["name"] == "Ready"))
    decision = evaluate_claim(r, snapshot)
    if decision == "reject": raise ClaimError("Claim rejected: ownership, issue state or readiness conflict. Inspect the ledger.")
    claim = dict(active) if active else dict(actor=r["actor"], session=r["session"], claim_id=r["run_id"])

    def event(kind):
        value = dict(claim, event=kind, executor=r["actor"], run_id=r["run_id"], run_attempt=r["run_attempt"],
                     utc=datetime.now(timezone.utc).isoformat())
        if kind in {"reserved", "accepted"}: value["dependencies"] = "verified"
        if kind in {"releasing", "released"}: value.update(reason=r["reason"], handoff=r["handoff"])
        api("POST", base + "/comments", {"body": MARKER + json.dumps(value, sort_keys=True)})

    if decision == "accept": event("reserved")
    if decision in {"accept", "resume"}:
        if not active or active["event"] != "accepted":
            api("POST", base + "/assignees", {"assignees": [r["actor"]]})
            event("accepted")
        current = api("GET", base)
        verified = active_claim(api, base, default_branch)
        if (not verified or verified["claim_id"] != claim["claim_id"] or verified["event"] != "accepted"
                or [a["login"] for a in current["assignees"]] != [r["actor"]]):
            raise ClaimError("Ownership verification failed; reservation remains until reconciliation.")
        status, outcome = "In progress", "accepted"
    else:
        if set(snapshot["assignments"]) - {claim["actor"]}:
            raise ClaimError("Unexpected assignees; reconcile manually before release.")
        if active["event"] != "releasing": event("releasing")
        api("DELETE", base + "/assignees", {"assignees": [claim["actor"]]})
        if api("GET", base)["assignees"]: raise ClaimError("Assignment removal not verified; release remains pending.")
        event("released")
        if active_claim(api, base, default_branch): raise ClaimError("Release not verified; reconcile ledger.")
        outcome = "released"
        status = "Blocked"
        if issue["state"] == "open":
            try: dependencies_ok(api, r["repo"], r["issue"]); status = "Ready"
            except ClaimError: pass
        elif issue.get("state_reason") == "completed" and r["handoff"].startswith("Completed:"):
            status = "Done"
    sync = "updated"
    try:
        item = item or project_item(api, issue["node_id"])
        set_status(api, item, status)
    except (ClaimError, KeyError, TypeError):
        sync = "pending"
    return dict(outcome=outcome, claim_id=claim["claim_id"], project_sync=sync, status=status)


def github_api(method, path, payload=None, credential="local"):
    names = {"local": "GH_TOKEN", "read": "COORDINATION_READ_TOKEN", "project": "COORDINATION_PROJECT_TOKEN"}
    token = os.environ.get(names[credential])
    if not token: raise ClaimError("Required coordination credential is not configured.")
    if not path.startswith("/") or path.startswith("//"): raise ClaimError("Invalid API path.")
    data = None if payload is None else json.dumps(payload).encode()
    req = Request("https://api.github.com" + path, data=data, method=method, headers={
        "Authorization": "Bearer " + token, "Accept": "application/vnd.github+json",
        "Content-Type": "application/json", "X-GitHub-Api-Version": "2022-11-28"})
    try:
        with urlopen(req, timeout=30) as response:
            body = response.read()
            result = json.loads(body) if body else None
    except (HTTPError, URLError, TimeoutError, ValueError):
        raise ClaimError("GitHub request failed or its outcome is unknown. Inspect state before retrying.") from None
    if isinstance(result, dict) and result.get("errors"):
        raise ClaimError("GitHub GraphQL request failed; check configuration/access.")
    return result


def main():
    r = dict(repo=os.environ.get("GITHUB_REPOSITORY", ""), issue=os.environ.get("INPUT_ISSUE", ""),
             operation=os.environ.get("INPUT_OPERATION", ""), actor=os.environ.get("GITHUB_ACTOR", ""),
             session=os.environ.get("INPUT_SESSION", ""), run_id=os.environ.get("GITHUB_RUN_ID", ""),
             run_attempt=os.environ.get("GITHUB_RUN_ATTEMPT", "1"), override=os.environ.get("INPUT_OVERRIDE") == "true",
             reason=os.environ.get("INPUT_REASON", ""), handoff=os.environ.get("INPUT_HANDOFF", ""))
    try:
        if os.environ.get("GITHUB_TRIGGERING_ACTOR") != r["actor"]:
            raise ClaimError("Re-runs must be initiated by the original actor.")
        validate_request(r)
        default = github_api("GET", "/repos/" + r["repo"])["default_branch"]
        if os.environ.get("GITHUB_REF") != "refs/heads/" + default:
            raise ClaimError("Dispatch only from the default branch.")
        permission = github_api("GET", "/repos/" + r["repo"] + "/collaborators/" + r["actor"] + "/permission")["permission"]
        if permission not in {"write", "maintain", "admin"}:
            raise ClaimError("Repository write permission is required.")
        if "--authorize" in sys.argv:
            print("Request and caller authorized."); return 0
        result = run(r, github_api)
        print(json.dumps(result))
        if result["project_sync"] == "pending":
            print("::warning::Ownership transition recorded; Project status needs repair. See AGENTS.md.")
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with open(summary, "a", encoding="utf-8") as file: file.write("\n```json\n" + json.dumps(result) + "\n```\n")
    except ClaimError as error:
        print(str(error), file=sys.stderr); return 1
    except (KeyError, TypeError, ValueError):
        print("Unexpected state; no success acknowledgement. Inspect ledger before retrying.", file=sys.stderr); return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
