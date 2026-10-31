import pytest
from pydantic import ValidationError
from pokemon_market.contracts import FixtureBundle, Request


def test_roundtrip(bundle):
    assert FixtureBundle.model_validate_json(bundle.model_dump_json()) == bundle


@pytest.mark.parametrize(
    "value", [1, True, 1.1, "NaN", "Infinity", "1e2", "1.001", "-1", " 1.00", "9" * 40]
)
def test_bad_money(raw, value):
    raw["policy"]["required_profit"] = value
    with pytest.raises(ValidationError):
        FixtureBundle.model_validate(raw)


@pytest.mark.parametrize(
    "key,value", [("version", True), ("minimum_observed_sales", 0), ("extra", "x")]
)
def test_policy_boundary(raw, key, value):
    raw["policy"][key] = value
    with pytest.raises(ValidationError):
        FixtureBundle.model_validate(raw)


def test_naive_time(raw):
    raw["evidence"][0]["observed_at"] = "2026-10-29T04:00:00"
    with pytest.raises(ValidationError):
        FixtureBundle.model_validate(raw)


def test_duplicate_record(raw):
    raw["evidence"].append(raw["evidence"][0])
    with pytest.raises(ValidationError):
        FixtureBundle.model_validate(raw)


def test_missing_policy_limit(raw):
    del raw["policy"]["per_item_limit"]
    with pytest.raises(ValidationError):
        FixtureBundle.model_validate(raw)


def test_incomplete_and_bundle_preserved(raw):
    raw["listings"][0]["card"] = None
    raw["listings"][0]["quantity"] = 2
    assert FixtureBundle.model_validate(raw).listings[0].quantity == 2


def test_request_invalid_schema(qualified_request):
    data = qualified_request.model_dump(mode="json")
    data["schema_version"] = "2"
    with pytest.raises(ValidationError):
        Request.model_validate(data)


def test_changes_are_typed_and_reassessment_only(qualified_request):
    data = qualified_request.model_dump(mode="json")
    data["changes"] = {"policy": "override"}
    with pytest.raises(ValidationError):
        Request.model_validate(data)


def test_exposure_baseline(raw):
    raw["existing_soft_exposure"] = "201.00"
    with pytest.raises(ValidationError):
        FixtureBundle.model_validate(raw)


def test_raw_cannot_have_grade(raw):
    raw["policy"]["allowed_cards"][0]["grade"] = "10"
    with pytest.raises(ValidationError):
        FixtureBundle.model_validate(raw)
