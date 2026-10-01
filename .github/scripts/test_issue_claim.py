"""Run without credentials: python -m unittest discover -s .github/scripts."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location("issue_claim", Path(__file__).with_name("issue_claim.py"))
c = importlib.util.module_from_spec(SPEC)
if SPEC.loader and Path(SPEC.origin).exists():
    SPEC.loader.exec_module(c)


def request(**changes):
    return dict(repo="ChouBokYann/pokemon-reselling", issue="1", operation="claim",
                actor="alice", session="agent-1", run_id="100", run_attempt="1",
                override=False, reason="", handoff="", **changes)


class Claims(unittest.TestCase):
    def test_decisions(self):
        self.assertTrue(hasattr(c, "evaluate_claim"), "claim evaluator is not implemented")
        r = request()
        good = dict(permission="write", state="open", ready=True, dependencies_ok=True,
                    assignments=[], active=None)
        self.assertEqual(c.evaluate_claim(r, good), "accept")
        for change in [dict(permission="read"), dict(state="closed"), dict(ready=False),
                       dict(dependencies_ok=False), dict(assignments=["bob"]),
                       dict(active=dict(actor="alice", session="agent-2", event="reserved"))]:
            with self.subTest(change=change):
                self.assertEqual(c.evaluate_claim(r, dict(good, **change)), "reject")
        active = dict(actor="alice", session="agent-1", event="accepted", claim_id="100")
        self.assertEqual(c.evaluate_claim(r, dict(good, active=active, assignments=["alice"], ready=False)), "resume")

    def test_invalid_inputs(self):
        self.assertTrue(hasattr(c, "validate_request"), "input validation is not implemented")
        for issue in ["01", " 1", "-1", "0", "1/../../", "1.0"]:
            r = request(); r["issue"] = issue
            with self.assertRaises(c.ClaimError): c.validate_request(r)
        for session in ["", "$(echo bad)", "x" * 81]:
            r = request(); r["session"] = session
            with self.assertRaises(c.ClaimError): c.validate_request(r)

    def test_release_closed_issue_and_session_guard(self):
        self.assertTrue(hasattr(c, "evaluate_claim"))
        r = request(); r.update(operation="release", handoff="Tests passed; work complete.")
        snap = dict(permission="write", state="closed", assignments=["alice"],
                    active=dict(actor="alice", session="agent-1", event="accepted"))
        self.assertEqual(c.evaluate_claim(r, snap), "release")
        r["session"] = "agent-2"
        self.assertEqual(c.evaluate_claim(r, snap), "reject")
        r.update(override=True, reason="Owner has confirmed abandonment")
        self.assertEqual(c.evaluate_claim(r, snap), "reject")
        snap["permission"] = "admin"
        self.assertEqual(c.evaluate_claim(r, snap), "release")

    def test_reservation_interruption_and_retry(self):
        self.assertTrue(hasattr(c, "run"), "claim runner is not implemented")
        api = FakeAPI(); api.fail_assignment = True
        with self.assertRaises(c.ClaimError): c.run(request(), api)
        self.assertEqual(api.events()[-1]["event"], "reserved")
        other = request(); other["session"] = "agent-2"
        with self.assertRaises(c.ClaimError): c.run(other, api)
        api.fail_assignment = False
        result = c.run(request(), api)
        self.assertEqual(result["outcome"], "accepted")
        self.assertEqual(c.run(request(), api)["claim_id"], result["claim_id"])
        self.assertEqual(sum(e["event"] == "accepted" for e in api.events()), 1)

    def test_project_failure_and_forgery(self):
        self.assertTrue(hasattr(c, "run"))
        api = FakeAPI(); api.fail_update = True
        result = c.run(request(), api)
        self.assertEqual(result["project_sync"], "pending")
        api.comments.append(dict(id=1000, user=dict(login="mallory", type="User"),
                                 body=c.MARKER + json.dumps(dict(event="released", claim_id="100", run_id="100"))))
        other = request(); other["session"] = "agent-2"
        with self.assertRaises(c.ClaimError): c.run(other, api)
        self.assertEqual(api.issue["assignees"], [dict(login="alice")])

    def test_unauthorized_and_dependencies_fail_closed(self):
        self.assertTrue(hasattr(c, "run"))
        for mode in ["read", "open", "not_planned", "inaccessible", "cycle", "undeclared"]:
            api = FakeAPI()
            if mode == "read": api.permission = "read"
            else: api.dependency_mode = mode
            with self.subTest(mode=mode), self.assertRaises(c.ClaimError): c.run(request(), api)
            self.assertEqual(api.comments, [])
        api = FakeAPI(); api.dependency_mode = "completed"
        self.assertEqual(c.run(request(), api)["outcome"], "accepted")

    def test_pagination_and_release_recovery(self):
        self.assertTrue(hasattr(c, "run"))
        api = FakeAPI()
        api.comments = [dict(id=i, user=dict(login="human", type="User"), body="Progress") for i in range(100)]
        c.run(request(), api)
        other = request(); other["session"] = "agent-2"
        with self.assertRaises(c.ClaimError): c.run(other, api)
        release = request(); release.update(operation="release", handoff="Branch saved; tests passed; no blockers.")
        api.fail_removal = True
        with self.assertRaises(c.ClaimError): c.run(release, api)
        with self.assertRaises(c.ClaimError): c.run(other, api)
        api.fail_removal = False
        self.assertEqual(c.run(release, api)["outcome"], "released")
        self.assertEqual(c.run(other, api)["outcome"], "accepted")

    def test_resume_honors_new_block_and_run_provenance(self):
        api = FakeAPI(); c.run(request(), api)
        api.status = "Blocked"
        with self.assertRaises(c.ClaimError): c.run(request(), api)
        api.status = "In progress"; api.bad_run = True
        with self.assertRaises(c.ClaimError): c.run(request(), api)

    def test_unknown_comment_write_retains_reservation(self):
        api = FakeAPI(); api.unknown_comment = True
        with self.assertRaises(c.ClaimError): c.run(request(), api)
        other = request(); other["session"] = "agent-2"
        with self.assertRaises(c.ClaimError): c.run(other, api)
        api.unknown_comment = False
        self.assertEqual(c.run(request(), api)["outcome"], "accepted")


class FakeAPI:
    """Only GitHub I/O is faked; real protocol, traversal and recovery execute."""
    def __init__(self):
        self.comments = []; self.permission = "write"; self.status = "Ready"
        self.fail_assignment = self.fail_removal = self.fail_update = False
        self.unknown_comment = self.bad_run = False
        self.dependency_mode = None
        self.issue = dict(number=1, node_id="I_1", state="open", state_reason=None,
                          body="### Dependencies\n\nNone\n\n### Non-code blockers\n\nNone",
                          assignees=[], issue_dependencies_summary=dict(blocked_by=0, total_blocked_by=0))

    def events(self):
        return [json.loads(x["body"][len(c.MARKER):]) for x in self.comments
                if x["body"].startswith(c.MARKER) and x["user"]["type"] == "Bot"]

    def __call__(self, method, path, payload=None, credential="local"):
        if path == "/graphql":
            if "mutation" in payload["query"]:
                if self.fail_update: raise c.ClaimError("Project update unavailable")
                self.status = payload["variables"]["value"]
                return {"data": {"updateProjectV2ItemFieldValue": {"projectV2Item": {"id": "ITEM"}}}}
            return {"data": {"node": {"projectItems": {"nodes": [{"id": "ITEM", "project": {"id": c.PROJECT},
                "fieldValueByName": {"name": self.status, "field": {"id": "STATUS", "options":
                    [{"id": s, "name": s} for s in ["Backlog", "Ready", "In progress", "Blocked", "In review", "Done"]]}}}],
                "pageInfo": {"hasNextPage": False, "endCursor": None}}}}}
        if "/collaborators/" in path: return {"permission": self.permission}
        if path.endswith("/actions/runs/100"):
            return dict(path=".github/workflows/issue-claim.yml", head_branch="untrusted" if self.bad_run else "main", event="workflow_dispatch",
                        actor=dict(login="alice"), triggering_actor=dict(login="alice"))
        if path == "/repos/ChouBokYann/pokemon-reselling": return dict(default_branch="main")
        if "/comments" in path:
            if method == "POST":
                item = dict(id=len(self.comments)+1, user=dict(login="github-actions[bot]", type="Bot"), body=payload["body"])
                self.comments.append(item)
                if self.unknown_comment: raise c.ClaimError("Write outcome unknown")
                return item
            page = int(path.split("page=")[-1]); return self.comments[(page-1)*100:page*100]
        if "/dependencies/blocked_by" in path:
            if self.dependency_mode and not "/issues/2/" in path:
                if self.dependency_mode == "inaccessible": raise c.ClaimError("Dependency inaccessible")
                return [dict(number=2, repository_url="https://api.github.com/repos/ChouBokYann/pokemon-reselling")]
            if self.dependency_mode == "cycle": return [dict(number=1, repository_url="https://api.github.com/repos/ChouBokYann/pokemon-reselling")]
            return []
        if path.endswith("/issues/2"):
            dep = copy.deepcopy(self.issue); dep.update(number=2, state="closed", state_reason="completed")
            if self.dependency_mode == "open": dep["state"] = "open"
            if self.dependency_mode == "not_planned": dep["state_reason"] = "not_planned"
            return dep
        if path.endswith("/assignees"):
            if method == "POST":
                if self.fail_assignment: raise c.ClaimError("Assignment outcome unknown")
                self.issue["assignees"] = [dict(login=x) for x in payload["assignees"]]
            else:
                if self.fail_removal: raise c.ClaimError("Removal outcome unknown")
                self.issue["assignees"] = []
            return self.issue
        if path.endswith("/issues/1"):
            result = copy.deepcopy(self.issue)
            if self.dependency_mode:
                result["issue_dependencies_summary"]["total_blocked_by"] = 1
                result["issue_dependencies_summary"]["blocked_by"] = 0 if self.dependency_mode == "completed" else 1
            if self.dependency_mode == "undeclared": result["body"] = "Missing blocker declarations"
            return result
        raise AssertionError((method, path))


if __name__ == "__main__":
    unittest.main()

