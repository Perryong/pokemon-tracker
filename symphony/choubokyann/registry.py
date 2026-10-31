#!/usr/bin/env python3
"""Explicit project registration; selecting a record never activates a runtime.

The local schema carries public scope and approval references, never credentials.
Registration is an operator action, not repository discovery or approval itself.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import re
import sys
import tempfile

ID = re.compile(r"[a-z][a-z0-9-]{0,39}\Z")
LOGIN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?\Z")
REPO = re.compile(r"([A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?)/([A-Za-z0-9_][A-Za-z0-9_.-]{0,99})\Z")
SAFE_NAME = re.compile(r"[a-z][a-z0-9-]{0,99}\Z")
BRANCH = re.compile(r"[A-Za-z0-9][A-Za-z0-9_./-]{0,199}\Z")
SCOPE = re.compile(r"[A-Za-z0-9][A-Za-z0-9 .,;:/()_+-]{0,499}\Z")
FIELDS = {"repo", "actor", "project_owner", "project_number", "control_issue",
          "control_label", "queue_label", "session", "branch", "excluded_issues",
          "scope", "authority_url"}


class RegistryError(ValueError):
    """A public-safe registry error without untrusted input in its message."""


def matches(pattern, value):
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def positive(value):
    return type(value) is int and value > 0


def validate_record(record):
    """Validate an unaugmented record, also usable by the queue gate."""
    if not isinstance(record, dict) or set(record) != FIELDS:
        raise RegistryError("registration fields are missing or unknown")
    if not matches(REPO, record["repo"]) or ".." in record["repo"]:
        raise RegistryError("invalid repository")
    if record["actor"] != "ChouBokYann":
        raise RegistryError("registration actor does not match this personal machine")
    if not matches(LOGIN, record["project_owner"]):
        raise RegistryError("invalid project owner")
    if not positive(record["project_number"]) or not positive(record["control_issue"]):
        raise RegistryError("project and control issue numbers must be positive integers")
    for field in ("control_label", "queue_label", "session"):
        if not matches(SAFE_NAME, record[field]):
            raise RegistryError("invalid label or session identifier")
    if record["control_label"] == record["queue_label"]:
        raise RegistryError("control and queue labels must differ")
    branch = record["branch"]
    if (not matches(BRANCH, branch) or ".." in branch or "//" in branch
            or branch.endswith(("/", "."))
            or any(part.startswith(".") or part.endswith((".", ".lock")) for part in branch.split("/"))):
        raise RegistryError("invalid control branch")
    excluded = record["excluded_issues"]
    if (not isinstance(excluded, list) or any(not positive(n) for n in excluded)
            or len(set(excluded)) != len(excluded) or record["control_issue"] in excluded):
        raise RegistryError("invalid excluded issues")
    if not matches(SCOPE, record["scope"]) or record["scope"] != record["scope"].strip():
        raise RegistryError("scope must be nonempty plain text")
    authority = rf"https://github\.com/{re.escape(record['repo'])}/issues/{record['control_issue']}#issuecomment-[1-9][0-9]*\Z"
    if not matches(re.compile(authority), record["authority_url"]):
        raise RegistryError("authority must reference the canonical control issue comment")
    return copy.deepcopy(record)


def validate_registry(value):
    if (not isinstance(value, dict) or set(value) != {"version", "projects"}
            or type(value["version"]) is not int or value["version"] != 1
            or not isinstance(value["projects"], dict)):
        raise RegistryError("unsupported registry structure")
    seen = set()
    for project_id, record in value["projects"].items():
        if not matches(ID, project_id):
            raise RegistryError("invalid project identifier")
        validate_record(record)
        canonical = record["repo"].lower()
        if canonical in seen:
            raise RegistryError("duplicate repository registration")
        seen.add(canonical)
    return copy.deepcopy(value)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise RegistryError("duplicate JSON field")
        result[key] = value
    return result


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise RegistryError("invalid JSON document") from exc


def load_registry(path):
    return validate_registry(read_json(path))


def select_project(path, project_id):
    registry = load_registry(path)
    if not matches(ID, project_id) or project_id not in registry["projects"]:
        raise RegistryError("project is not explicitly registered")
    record = registry["projects"][project_id]
    return dict(record, id=project_id, volume=f"symphony-choubokyann-{project_id}-work",
                workspace="/work/coordinator", container="symphony-choubokyann",
                cpus=2, memory="3g", primary_slots=1, child_slots=3)


def register_project(path, project_id, record):
    """Add one reviewed record atomically, failing closed on competing writes.

    A leftover .lock after process termination needs deliberate operator recovery.
    This lock coordinates this CLI only; manual file editors bypass it.
    """
    path = Path(path)
    if not matches(ID, project_id):
        raise RegistryError("invalid project identifier")
    validate_record(record)
    if path.is_symlink():
        raise RegistryError("registration cannot replace a symbolic link")
    lock_path = path.with_name(path.name + ".lock")
    try:
        descriptor = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise RegistryError("registry is locked; reconcile the existing write before retrying") from exc
    temporary = None
    try:
        os.close(descriptor)
        registry = load_registry(path)
        if project_id in registry["projects"]:
            raise RegistryError("project identifier is already registered")
        registry["projects"][project_id] = validate_record(record)
        validate_registry(registry)
        descriptor, temporary = tempfile.mkstemp(prefix=".registry-", dir=path.parent)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(registry, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            os.unlink(temporary)
        os.unlink(lock_path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "select", "register"):
        command = commands.add_parser(name)
        command.add_argument("--registry", type=Path, required=True)
        if name != "validate":
            command.add_argument("--project", required=True)
        if name == "register":
            command.add_argument("--record", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "select":
            print(json.dumps(select_project(args.registry, args.project), sort_keys=True))
        elif args.command == "register":
            register_project(args.registry, args.project, read_json(args.record))
            print("Project registered; runtime activation is a separate operator action.")
        else:
            registry = load_registry(args.registry)
            print(f"Registry valid: {len(registry['projects'])} explicit project registration(s).")
        return 0
    except (ValueError, OSError) as exc:
        reason = str(exc) if isinstance(exc, RegistryError) else "registry read/write failed"
        print("registry blocked: " + reason, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
