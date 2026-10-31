"""Boundary specifications. Run only in an approved credential-free boundary.

Written before implementation; no red/green run has been authorized yet.
"""
import importlib.util
import contextlib
import io
import os
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("isolation_probe", Path(__file__).with_name("isolation_probe.py"))
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class ArchiveBoundaryTests(unittest.TestCase):
    def archive(self, name="src/example.py", kind=tarfile.REGTYPE, target="", content=b"pass\n"):
        root = tempfile.TemporaryDirectory()
        self.addCleanup(root.cleanup)
        path = Path(root.name) / "source.tar"
        with tarfile.open(path, "w") as archive:
            item = tarfile.TarInfo(name)
            item.type = kind
            item.linkname = target
            if kind == tarfile.REGTYPE:
                item.size = len(content)
            archive.addfile(item, io.BytesIO(content) if item.size else None)
        return path

    def test_regular_source_is_accepted(self):
        self.assertEqual(probe.validate_archive(self.archive()), 1)

    def test_traversal_absolute_and_windows_paths_are_rejected(self):
        # Removing canonical-path validation would permit writes outside /work/source.
        for name in ("../escape", "/root/auth.json", "a/../../escape", "C:/escape", "a\\escape"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                probe.validate_archive(self.archive(name))

    def test_links_and_special_files_are_rejected(self):
        # Allowing either link kind can expose a path beyond the mounted archive.
        for kind in (tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.CHRTYPE, tarfile.FIFOTYPE):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                probe.validate_archive(self.archive(kind=kind, target="/root/.codex/auth.json"))

    def test_credentials_and_git_metadata_are_rejected(self):
        for name in (".git/config", ".codex/auth.json", "x/.aws/credentials", ".env", "x/.ssh/id_ed25519", "workpad/session.json", ".symphony/workpad.md"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                probe.validate_archive(self.archive(name))

    def test_oversized_archive_is_rejected_before_extraction(self):
        with self.assertRaises(ValueError):
            probe.validate_archive(self.archive(content=b"12345"), max_bytes=4)

    def test_empty_argv_and_shell_string_are_rejected(self):
        for value in ([], "echo unsafe", [""], ["python3", 3], ["echo", "bad\x00arg"]):
            with self.subTest(value=value), self.assertRaises(ValueError):
                probe.validate_argv(value)

    def test_argv_preserves_shell_metacharacters_as_literal_arguments(self):
        self.assertEqual(probe.validate_argv(["echo", "$(touch /tmp/escape); *"]), ["echo", "$(touch /tmp/escape); *"])

    def test_readable_sentinel_causes_failure_without_returning_value(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "sentinel"
            path.write_text("SYNTHETIC-NOT-A-CREDENTIAL")
            self.assertFalse(probe.inaccessible(path))
            self.assertTrue(probe.inaccessible(Path(root) / "absent"))

    def test_boundary_rejects_readable_sentinel_before_repository_execution(self):
        # Removing the boundary's path loop must make this negative control fail.
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "sentinel"
            marker = "SYNTHETIC-NOT-A-CREDENTIAL"
            path.write_text(marker)
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                with self.assertRaisesRegex(RuntimeError, "host-path-0") as raised:
                    probe.boundary_checks({"sentinel_path": str(path), "host_pid": 999999999})
            self.assertNotIn(marker, str(raised.exception) + output.getvalue())
            self.assertNotIn("BOUNDARY_PROBE_PASS", output.getvalue())

    def test_boundary_rejects_inherited_synthetic_parent_environment(self):
        # Removing the environment guard must make this negative control fail.
        with tempfile.TemporaryDirectory() as root:
            with patch.dict(os.environ, {"ISOLATION_PARENT_SENTINEL": "SYNTHETIC-NOT-A-CREDENTIAL"}):
                with self.assertRaisesRegex(RuntimeError, "parent-environment"):
                    probe.boundary_checks({"sentinel_path": str(Path(root) / "absent"), "host_pid": 999999999})

    def test_boundary_rejects_readable_host_sentinel(self):
        # Removing the boundary failure branch must fail this negative control.
        with tempfile.TemporaryDirectory() as root:
            sentinel = Path(root) / "sentinel"
            sentinel.write_text("SYNTHETIC-NOT-A-CREDENTIAL")
            with patch.object(probe.socket, "create_connection", side_effect=OSError), \
                    self.assertRaisesRegex(RuntimeError, "host-path-0"):
                probe.boundary_checks({"sentinel_path": str(sentinel), "host_pid": 987654321})


if __name__ == "__main__":
    unittest.main()
