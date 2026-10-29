import json
import subprocess
import sys
import pytest


def run(*args, cwd=None):
    return subprocess.run(
        [sys.executable, "-m", "pokemon_market", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=20,
    )


@pytest.mark.parametrize(
    "name,decision",
    [
        ("qualified", "qualified"),
        ("questions-only", "questions_only"),
        ("identity-review", "review"),
        ("stale-evidence", "questions_only"),
        ("reassessment", "rejected"),
    ],
)
def test_demo(name, decision, tmp_path):
    result = run("demo", "--scenario", name, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["mode"] == "simulation" and data["assessment"]["decision"] == decision
    if name == "qualified":
        assert (
            data["mandate"]["ceiling"] == "80.00"
            and data["mandate"]["exposure"] == "85.00"
        )
    assert result.stderr == ""


def test_inventory_demo():
    r = run("demo", "--scenario", "inventory")
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["inventory"]["realized_profit"] == "5.00"
    assert data["inventory"]["pending_outcomes"] == ["pending"]


def test_invalid_scenario():
    r = run("demo", "--scenario", "unknown")
    assert r.returncode == 2 and not r.stdout and "Traceback" not in r.stderr


def test_live_model_needs_key(monkeypatch, capsys):
    from pokemon_market.__main__ import main

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert main(["demo", "--model", "openai:chosen-model"]) == 2
    captured = capsys.readouterr()
    assert not captured.out and "missing_model_key" in captured.err


def test_only_explicit_supported_provider(capsys):
    from pokemon_market.__main__ import main

    assert main(["demo", "--model", "unknown:model"]) == 2
    assert "unsupported_model" in capsys.readouterr().err
