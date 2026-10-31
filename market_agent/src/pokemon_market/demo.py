"""Fixed-time synthetic demonstrations, including when using an optional live model."""

from datetime import datetime, timezone
from importlib.resources import files
from .contracts import Artifact, FixtureBundle, InventoryBundle, MarketError, Request
from .controlled import ControlledModel
from .harness import run_agent
from .session import MarketSession

SCENARIOS = (
    "qualified",
    "questions-only",
    "identity-review",
    "stale-evidence",
    "reassessment",
    "inventory",
)
DEMO_TIME = datetime(2026, 10, 30, 4, tzinfo=timezone.utc)


def load_bundle() -> FixtureBundle:
    return FixtureBundle.model_validate_json(
        files("pokemon_market").joinpath("fixtures/qualified.json").read_text()
    )


def run_scenario(name: str, *, model=None) -> Artifact:
    if name not in SCENARIOS:
        raise MarketError("unknown_scenario")
    data = load_bundle().model_dump(mode="json")
    if name == "questions-only":
        data["listings"][0]["condition"] = None
    if name == "identity-review":
        data["listings"][0]["card"]["language"] = "ja"
    if name == "stale-evidence":
        for e in data["evidence"]:
            e["observed_at"] = "2026-10-01T04:00:00Z"
    inventory = InventoryBundle.model_validate_json(
        files("pokemon_market").joinpath("fixtures/inventory.json").read_text()
    )
    session = MarketSession(
        FixtureBundle.model_validate(data), clock=lambda: DEMO_TIME, inventory=inventory
    )
    request = Request(
        request_id=f"demo-{name}",
        operation="assess_opportunity",
        correlation_id="listing-1",
        policy_version="policy-1",
        assessment_version=0,
        conversation_version=0,
        expires_at="2026-10-30T04:15:00Z",
        evidence_ids=["e1", "e2"],
    )
    if name == "inventory":
        request = Request.model_validate(
            request.model_dump(mode="json")
            | {"operation": "assess_owned_unit", "correlation_id": "available"}
        )
    if name == "reassessment":
        first = run_agent(session, model or ControlledModel(), request)
        request = Request.model_validate(
            request.model_dump(mode="json")
            | dict(
                request_id="demo-changed",
                operation="reassess_opportunity",
                assessment_version=first.assessment.version,
                changes={"condition": "damaged"},
            )
        )
    return run_agent(session, model or ControlledModel(), request)
