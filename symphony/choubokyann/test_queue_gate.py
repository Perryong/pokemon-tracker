"""Queue gate behavior; GitHub transport is replaced by public-shaped fixtures."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("queue_gate", Path(__file__).with_name("queue_gate.py"))
gate = importlib.util.module_from_spec(SPEC) if SPEC else None
if SPEC and SPEC.loader and Path(SPEC.origin).exists():
    SPEC.loader.exec_module(gate)


def connection(nodes):
    return {"nodes": nodes, "pageInfo": {"hasNextPage": False, "hasPreviousPage": False}}


def issue(number, label, assignees=()):
    return {"number": number, "id": f"I{number}", "title": "PUBLIC TITLE", "body": "PUBLIC BODY",
            "state": "OPEN", "updatedAt": "2026-10-30T00:00:00Z", "url": f"https://github.com/Perryong/pokemon-tracker/issues/{number}",
            "repository": {"nameWithOwner": "Perryong/pokemon-tracker", "isPrivate": False},
            "labels": connection([{"name": label}]), "assignees": connection([{"login": x} for x in assignees]),
            "timelineItems": connection([]), "blockedBy": connection([]), "closedByPullRequestsReferences": connection([])}


class FakeGitHub:
    def __init__(self):
        self.control = issue(27, "symphony-choubokyann-coordinator", ["ChouBokYann"])
        self.queue = issue(28, "symphony-choubokyann-queue")
        self.pr = None
        self.open_prs = []
        self.dependency = issue(29, "dependency")
        self.project = connection([self.item(27, "In progress"), self.item(28, "Ready")])

    @staticmethod
    def item(number, status, repo="Perryong/pokemon-tracker", private=False):
        return {"content": {"__typename": "Issue", "number": number,
                            "repository": {"nameWithOwner": repo, "isPrivate": private}},
                "fieldValueByName": {"name": status}}

    def __call__(self, query, **variables):
        if "QueueInventory" in query:
            return {"viewer": {"login": "ChouBokYann"},
                    "repository": {"nameWithOwner": "Perryong/pokemon-tracker", "isPrivate": False,
                                   "control": connection([{"number": 27}]), "queue": connection([{"number": 28}]), "pullRequests": connection(self.open_prs)},
                    "user": {"projectV2": {"number": 1, "items": copy.deepcopy(self.project)}}}
        if "QueueIssue" in query:
            return {"repository": {"issue": copy.deepcopy({27: self.control, 28: self.queue, 29: self.dependency}[variables["number"]])}}
        if "QueuePullRequest" in query:
            return {"repository": {"pullRequest": copy.deepcopy(self.pr)}}
        raise AssertionError("unexpected query")


class QueueGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace = Path(self.temp.name)
        self.api = FakeGitHub()

    def run_gate(self, command, reason=None):
        expected = None
        if command == "acknowledge":
            try:
                expected = gate.snapshot(self.api)["fingerprint"]
            except Exception:
                expected = "unavailable"
        return gate.run(command, self.workspace, self.api, reason=reason, expected_fingerprint=expected)

    def state(self):
        return json.loads((self.workspace / ".symphony/choubokyann/queue-gate.json").read_text())

    def test_pending_blocks_even_when_evidence_changes_until_explicit_retry(self):
        self.assertEqual(self.run_gate("check"), 0)
        pending = self.state()["pending"]
        self.api.queue["body"] = "changed"
        self.assertNotEqual(self.run_gate("check"), 0)
        self.assertEqual(self.state()["pending"], pending)
        self.assertNotEqual(self.run_gate("retry"), 0)
        self.assertEqual(self.run_gate("retry", "operator inspected interrupted cycle"), 0)
        self.assertEqual(self.state()["recoveries"][0]["pending"], pending)
        self.assertEqual(self.run_gate("check"), 0)

    def test_acknowledge_rereads_so_own_comment_does_not_wake_model(self):
        self.assertEqual(self.run_gate("check"), 0)
        self.api.control["timelineItems"]["nodes"].append({"id": "own-comment", "body": "progress"})
        self.assertEqual(self.run_gate("acknowledge"), 0)
        self.assertNotEqual(self.run_gate("check"), 0)
        self.api.queue["timelineItems"]["nodes"].append({"id": "claim-event", "body": "claim"})
        self.assertEqual(self.run_gate("check"), 0)

    def test_wrong_scope_or_missing_control_project_status_fails_closed(self):
        for mutate in [lambda: self.api.control["assignees"]["nodes"].clear(),
                       lambda: self.api.queue["assignees"]["nodes"].append({"login": "Perryong"}),
                       lambda: self.api.project["nodes"][0]["fieldValueByName"].update(name="Ready"),
                       lambda: self.api.queue.update(number=24)]:
            with self.subTest(mutate=mutate):
                self.api = FakeGitHub()
                mutate()
                self.assertNotEqual(self.run_gate("check"), 0)

    def test_truncation_and_api_failure_do_not_acknowledge(self):
        self.assertEqual(self.run_gate("check"), 0)
        pending = self.state()["pending"]
        self.api.queue["timelineItems"]["pageInfo"]["hasNextPage"] = True
        self.assertNotEqual(self.run_gate("acknowledge"), 0)
        self.assertEqual(self.state()["pending"], pending)
        self.api = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("secret response"))
        self.assertNotEqual(self.run_gate("acknowledge"), 0)
        self.assertEqual(self.state()["pending"], pending)

    def test_state_excludes_content_and_private_other_repository_project_items(self):
        self.api.project["nodes"].append(FakeGitHub.item(80, "PRIVATE STATUS", "private/secret", True))
        self.assertEqual(self.run_gate("check"), 0)
        text = json.dumps(self.state())
        for secret in ["PUBLIC TITLE", "PUBLIC BODY", "private/secret", "PRIVATE STATUS"]:
            self.assertNotIn(secret, text)
        self.assertEqual(self.run_gate("acknowledge"), 0)
        self.api.project["nodes"][-1]["fieldValueByName"]["name"] = "OTHER PRIVATE STATUS"
        self.assertNotEqual(self.run_gate("check"), 0)

    def test_project_dependency_and_linked_pr_changes_wake_gate(self):
        for change in ["project", "dependency", "pr"]:
            with self.subTest(change=change):
                self.workspace = Path(self.temp.name) / change
                self.api = FakeGitHub()
                self.assertEqual(self.run_gate("check"), 0)
                self.assertEqual(self.run_gate("acknowledge"), 0)
                if change == "project":
                    self.api.project["nodes"][1]["fieldValueByName"]["name"] = "Blocked"
                elif change == "dependency":
                    self.api.queue["blockedBy"]["nodes"].append(issue(29, "dependency"))
                else:
                    self.api.queue["timelineItems"]["nodes"].append({"id": "link", "source": {"__typename": "PullRequest", "number": 30, "repository": {"nameWithOwner": "Perryong/pokemon-tracker", "isPrivate": False}}})
                    self.api.pr = {"number": 30, "headRefOid": "abc", "timelineItems": connection([]), "reviews": connection([]), "commits": connection([]), "repository": {"nameWithOwner": "Perryong/pokemon-tracker", "isPrivate": False}}
                self.assertEqual(self.run_gate("check"), 0)
                self.assertEqual(self.run_gate("acknowledge"), 0)

    def test_unlinked_open_pr_head_checks_reviews_and_timeline_changes_wake_gate(self):
        self.api.open_prs = [{"number": 30, "author": {"login": "ChouBokYann"}}]
        self.api.pr = {"number": 30, "headRefOid": "abc", "timelineItems": connection([]),
                       "reviews": connection([]), "commits": connection([]),
                       "repository": {"nameWithOwner": "Perryong/pokemon-tracker", "isPrivate": False}}
        self.assertEqual(self.run_gate("check"), 0)
        self.assertEqual(self.run_gate("acknowledge"), 0)
        for field, value in [("headRefOid", "def"), ("reviews", connection([{"id": "R1", "state": "APPROVED"}])),
                             ("timelineItems", connection([{"id": "E1"}])),
                             ("commits", connection([{"commit": {"oid": "def", "statusCheckRollup": {"state": "SUCCESS"}}}]))]:
            self.api.pr[field] = value
            self.assertEqual(self.run_gate("check"), 0)
            self.assertEqual(self.run_gate("acknowledge"), 0)

    def test_transport_timeout_errors_and_token_are_sanitized(self):
        import contextlib
        import io
        import subprocess
        secret = "should-never-be-printed"
        with patch.dict("os.environ", {"SYMPHONY_QUEUE_TOKEN": secret}):
            with patch.object(gate.subprocess, "run", side_effect=subprocess.TimeoutExpired("gh", 20)):
                with self.assertRaises(gate.GateError):
                    gate.GitHub()("query { viewer { login } }")
            captured = {}
            def github_process(args, **kwargs):
                captured.update(kwargs)
                return subprocess.CompletedProcess(args, 0, json.dumps({"data": {"viewer": {"login": "ChouBokYann"}}}))
            with patch.object(gate.subprocess, "run", side_effect=github_process):
                self.assertEqual(gate.GitHub()("query { viewer { login } }")["viewer"]["login"], "ChouBokYann")
            self.assertEqual(captured["env"]["GH_TOKEN"], secret)
            self.assertLessEqual(captured["timeout"], 20)
            self.assertNotIn(secret, captured["input"])
        with patch.object(gate.subprocess, "run", return_value=subprocess.CompletedProcess(["gh"], 1, secret, secret)):
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                self.assertNotEqual(gate.run("check", self.workspace), 0)
            self.assertNotIn(secret, stderr.getvalue())

    def test_unrelated_colleague_pr_changes_do_not_wake_gate(self):
        self.api.open_prs = [{"number": 40, "author": {"login": "Perryong"}}]
        self.assertEqual(self.run_gate("check"), 0)
        self.assertEqual(self.run_gate("acknowledge"), 0)
        self.api.open_prs.append({"number": 41, "author": {"login": "Perryong"}})
        self.assertNotEqual(self.run_gate("check"), 0)

    def test_wrong_viewer_and_unique_control_inventory_fail_closed(self):
        original = self.api
        for change in ["actor", "control", "repo", "label"]:
            with self.subTest(change=change):
                def changed_api(query, **variables):
                    value = original(query, **variables)
                    if "QueueInventory" in query:
                        if change == "actor":
                            value["viewer"]["login"] = "Perryong"
                        elif change == "control":
                            value["repository"]["control"]["nodes"].append({"number": 99})
                        elif change == "repo":
                            value["repository"]["nameWithOwner"] = "other/repo"
                    elif "QueueIssue" in query and change == "label":
                        value["repository"]["issue"]["labels"]["nodes"] = []
                    return value
                self.assertNotEqual(gate.run("check", self.workspace, changed_api), 0)

    def test_api_selects_dependency_closure_reason_and_review_thread_resolution(self):
        self.api.queue["blockedBy"]["nodes"] = [self.api.dependency]
        self.api.dependency.update(state="CLOSED", stateReason="COMPLETED")
        self.api.open_prs = [{"number": 30, "author": {"login": "ChouBokYann"}}]
        self.api.pr = {"number": 30, "headRefOid": "abc", "timelineItems": connection([]),
                       "reviews": connection([]), "reviewThreads": connection([{"isResolved": False,
                       "isOutdated": False, "comments": connection([{"id": "C1", "body": "review", "updatedAt": "today"}])}]),
                       "commits": connection([]), "repository": {"nameWithOwner": "Perryong/pokemon-tracker", "isPrivate": False}}
        original = self.api
        def api(query, **variables):
            response = original(query, **variables)
            if "QueueIssue" in query and "stateReason" not in query:
                response["repository"]["issue"].pop("stateReason", None)
            if "QueuePullRequest" in query and "reviewThreads" not in query:
                response["repository"]["pullRequest"].pop("reviewThreads", None)
            return response
        self.api = api
        self.assertEqual(self.run_gate("check"), 0)
        self.assertEqual(self.run_gate("acknowledge"), 0)
        original.dependency["stateReason"] = "NOT_PLANNED"
        self.assertEqual(self.run_gate("check"), 0)
        self.assertEqual(self.run_gate("acknowledge"), 0)
        original.pr["reviewThreads"]["nodes"][0]["isResolved"] = True
        self.assertEqual(self.run_gate("check"), 0)

    def test_acknowledge_rejects_unreviewed_racing_changes_and_inspect_does_not_mutate(self):
        import contextlib
        import io
        self.assertEqual(self.run_gate("check"), 0)
        before = self.state()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(self.run_gate("inspect"), 0)
        observed = json.loads(output.getvalue())["fingerprint"]
        self.assertEqual(self.state(), before)
        self.api.queue["body"] = "new human requirement"
        self.assertNotEqual(gate.run("acknowledge", self.workspace, self.api,
                                     expected_fingerprint=observed), 0)
        self.assertEqual(self.state(), before)
        self.assertNotEqual(gate.run("acknowledge", self.workspace, self.api), 0)
        self.assertEqual(self.run_gate("acknowledge"), 0)

    def test_closed_queued_work_remains_visible_for_acceptance_review(self):
        self.assertEqual(self.run_gate("check"), 0)
        self.assertEqual(self.run_gate("acknowledge"), 0)
        self.api.queue.update(state="CLOSED", stateReason="NOT_PLANNED")
        self.assertEqual(self.run_gate("check"), 0)
        self.assertEqual(self.run_gate("acknowledge"), 0)
        self.assertNotEqual(self.run_gate("check"), 0)
        self.assertIn('states:[OPEN,CLOSED]', gate.INVENTORY_QUERY)


if __name__ == "__main__":
    unittest.main()
