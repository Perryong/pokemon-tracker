"""Registration contract: scope isolation, validation and durable explicit writes."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent


def record(repo="Example/one", control=9):
    return {"repo": repo, "actor": "ChouBokYann", "project_owner": "ChouBokYann",
            "project_number": 1, "control_issue": control,
            "control_label": "example-coordinator", "queue_label": "example-queue",
            "session": "example-session-20261030", "branch": "example/coordinator",
            "excluded_issues": [2, 3], "scope": "Example operator UI and setup",
            "authority_url": f"https://github.com/{repo}/issues/{control}#issuecomment-123"}


class RegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("project_registry", HERE / "registry.py")
        cls.registry = importlib.util.module_from_spec(spec)
        if (HERE / "registry.py").exists():
            spec.loader.exec_module(cls.registry)
        else:
            cls.registry = None

    def setUp(self):
        self.assertIsNotNone(self.registry, "explicit project registry is not implemented")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "projects.json"
        self.document = {"version": 1, "projects": {"one": record()}}
        self.write(self.document)

    def write(self, document):
        self.path.write_text(json.dumps(document), encoding="utf-8")

    def cli(self, *args):
        return subprocess.run([sys.executable, str(HERE / "registry.py"), *args],
                              text=True, capture_output=True, check=False)

    def test_two_projects_select_isolated_storage_with_one_global_slot(self):
        self.document["projects"]["two"] = record("Example/two", 10)
        self.write(self.document)
        one = self.registry.select_project(self.path, "one")
        two = self.registry.select_project(self.path, "two")
        self.assertEqual(one["repo"], "Example/one")
        self.assertEqual(two["repo"], "Example/two")
        self.assertEqual(one["volume"], "symphony-choubokyann-one-work")
        self.assertEqual(two["volume"], "symphony-choubokyann-two-work")
        for chosen in (one, two):
            self.assertEqual(chosen["container"], "symphony-choubokyann")
            self.assertEqual(chosen["workspace"], "/work/coordinator")
            self.assertEqual((chosen["cpus"], chosen["memory"]), (2, "3g"))
            self.assertEqual((chosen["primary_slots"], chosen["child_slots"]), (1, 1))
        self.assertNotIn("volume", self.registry.load_registry(self.path)["projects"]["one"])

    def test_record_validator_rejects_unknown_unsafe_or_mismatched_scope(self):
        invalid = [("token", "secret"), ("actor", "Perryong"), ("repo", "../repo"),
                   ("repo", "Example/repo;whoami"), ("project_owner", "../owner"),
                   ("project_number", True), ("project_number", 0), ("control_issue", -1),
                   ("control_label", "same\nlabel"), ("queue_label", "example-coordinator"),
                   ("session", "../escape"), ("session", "$(command)"),
                   ("branch", "branch..escape"), ("branch", "-option"),
                   ("branch", "dir/.hidden"), ("branch", "branch.lock"),
                   ("branch", "dir./branch"),
                   ("branch", "foo@{bar}"), ("branch", "foo;command"),
                   ("excluded_issues", [True]), ("excluded_issues", [2, 2]),
                   ("excluded_issues", [9]), ("scope", ""), ("scope", "text\ninstructions"),
                   ("scope", "{{ secrets }}"), ("authority_url", "https://evil.test/123"),
                   ("authority_url", "https://github.com/Example/one/issues/8#issuecomment-123")]
        for field, value in invalid:
            with self.subTest(field=field, value=value):
                candidate = record()
                candidate[field] = value
                with self.assertRaises(ValueError):
                    self.registry.validate_record(candidate)
        missing = record()
        del missing["scope"]
        with self.assertRaises(ValueError):
            self.registry.validate_record(missing)
        self.assertEqual(self.registry.validate_record(record()), record())

    def test_registry_rejects_unknown_duplicate_or_invalid_identifiers(self):
        bad = [[], {"version": True, "projects": {}}, {"version": 2, "projects": {}},
               {"version": 1, "projects": {}, "credentials": "secret"},
               {"version": 1, "projects": {"../escape": record()}},
               {"version": 1, "projects": {"Bad": record()}},
               {"version": 1, "projects": {"one": record(), "two": record("example/ONE")}}]
        for document in bad:
            with self.subTest(document=document):
                self.write(document)
                with self.assertRaises(ValueError):
                    self.registry.load_registry(self.path)
        self.path.write_text('{"version":1,"version":1,"projects":{}}')
        with self.assertRaises(ValueError):
            self.registry.load_registry(self.path)
        self.write(self.document)
        for project in ("missing", "../escape"):
            with self.assertRaises(ValueError):
                self.registry.select_project(self.path, project)

    def test_registration_persists_new_id_and_cli_selection_without_activation(self):
        candidate = Path(self.temp.name) / "record.json"
        candidate.write_text(json.dumps(record("Example/two", 10)))
        result = self.cli("register", "--registry", str(self.path), "--project", "two", "--record", str(candidate))
        self.assertEqual(result.returncode, 0, result.stderr)
        loaded = self.registry.load_registry(self.path)
        self.assertEqual(set(loaded["projects"]), {"one", "two"})
        result = self.cli("select", "--registry", str(self.path), "--project", "two")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["volume"], "symphony-choubokyann-two-work")
        result = self.cli("validate", "--registry", str(self.path))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("authority_url", result.stdout)
        self.assertEqual(sorted(p.name for p in Path(self.temp.name).iterdir()), ["projects.json", "record.json"])

    def test_rejected_registration_and_failed_atomic_replace_preserve_original(self):
        before = self.path.read_bytes()
        for project, value in (("one", record("Example/two", 10)), ("two", record()),
                               ("../escape", record("Example/two", 10))):
            with self.subTest(project=project):
                with self.assertRaises(ValueError):
                    self.registry.register_project(self.path, project, value)
                self.assertEqual(self.path.read_bytes(), before)
        with mock.patch.object(self.registry.os, "replace", side_effect=OSError("disk failure")):
            with self.assertRaises(OSError):
                self.registry.register_project(self.path, "two", record("Example/two", 10))
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual([p.name for p in Path(self.temp.name).iterdir()], ["projects.json"])

    def test_lock_and_symbolic_link_rejections_preserve_existing_state(self):
        before = self.path.read_bytes()
        lock = self.path.with_name("projects.json.lock")
        lock.write_text("pending writer")
        with self.assertRaises(ValueError):
            self.registry.register_project(self.path, "two", record("Example/two", 10))
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(lock.read_text(), "pending writer")
        lock.unlink()
        alias = self.path.with_name("alias.json")
        try:
            alias.symlink_to(self.path)
        except OSError:
            self.skipTest("host does not permit symlink creation; lock assertions passed")
        with self.assertRaises(ValueError):
            self.registry.register_project(alias, "two", record("Example/two", 10))
        self.assertTrue(alias.is_symlink())
        self.assertEqual(self.path.read_bytes(), before)

    def test_invalid_cli_read_does_not_echo_untrusted_document(self):
        self.path.write_text('{"token":"DO-NOT-ECHO"}')
        result = self.cli("validate", "--registry", str(self.path))
        self.assertEqual(result.returncode, 2)
        self.assertNotIn("DO-NOT-ECHO", result.stdout + result.stderr)

    def test_seed_only_enrolls_pokemon(self):
        loaded = self.registry.load_registry(HERE / "projects.json")
        self.assertEqual(list(loaded["projects"]), ["pokemon"])
        pokemon = self.registry.select_project(HERE / "projects.json", "pokemon")
        self.assertEqual(pokemon["repo"], "Perryong/pokemon-tracker")
        self.assertEqual(pokemon["control_issue"], 27)
        self.assertEqual(pokemon["excluded_issues"], [24, 26])
        self.assertEqual(pokemon["authority_url"], "https://github.com/Perryong/pokemon-tracker/issues/27#issuecomment-6523188095")


if __name__ == "__main__":
    unittest.main()
