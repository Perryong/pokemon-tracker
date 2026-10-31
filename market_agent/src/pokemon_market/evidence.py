"""Bounded reference observations and descriptive scenarios; assess owns authority."""

import http.client
import ipaddress
import json
import re
import time
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_FLOOR
from statistics import median
from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import AwareDatetime, BeforeValidator, Field, model_validator

from .contracts import (
    Amount,
    Assessment,
    Contract,
    Evidence,
    Listing,
    MarketError,
    Policy,
    ReviewedAssumption,
)
from .valuation import assess

REFERENCE_TIMEOUT_SECONDS = 8
MAX_REFERENCE_BYTES = 1024 * 1024
CARD_ID_PATTERN = r"[a-zA-Z0-9]+(?:[.-][a-zA-Z0-9]+)*-[a-zA-Z0-9.]+"
CardID = Annotated[str, Field(strict=True, max_length=80, pattern=f"^{CARD_ID_PATTERN}$")]
CARDMARKET_METRICS = frozenset((
    "avg", "low", "trend", "avg1", "avg7", "avg30", "avg-holo", "low-holo",
    "trend-holo", "avg1-holo", "avg7-holo", "avg30-holo",
))
TCGPLAYER_METRICS = frozenset(
    ("lowPrice", "midPrice", "highPrice", "marketPrice", "directLowPrice")
)


def _reference_price(value):
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ValueError("reference prices must be numbers")
    value = Decimal(str(value))
    if not value.is_finite() or not 0 <= value <= Decimal("999999999999.99"):
        raise ValueError("reference price out of bounds")
    return value


ReferencePrice = Annotated[Decimal, BeforeValidator(_reference_price)]


def _reference_datetime(value):
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})", value
    ):
        raise ValueError("reference timestamp must be an ISO date with timezone")
    return value


ReferenceDatetime = Annotated[AwareDatetime, BeforeValidator(_reference_datetime)]


class ReferenceCard(Contract):
    id: CardID
    name: Annotated[str, Field(strict=True, min_length=1, max_length=200, pattern=r"\S")]


class ReferenceQuote(Contract):
    provider: Literal["cardmarket", "tcgplayer"]
    currency: Literal["EUR", "USD"]
    variant: Annotated[str, Field(strict=True, min_length=1, max_length=80, pattern=r"\S")]
    updated_at: ReferenceDatetime | None = Field(alias="updatedAt")
    freshness: Literal["current", "stale", "unknown"]
    prices: Annotated[dict[str, ReferencePrice], Field(min_length=1, max_length=12)]

    @model_validator(mode="after")
    def provider_fields(self):
        currency, metrics = (
            ("EUR", CARDMARKET_METRICS)
            if self.provider == "cardmarket"
            else ("USD", TCGPLAYER_METRICS)
        )
        if self.currency != currency or not self.prices.keys() <= metrics:
            raise ValueError("provider currency or metrics mismatch")
        return self


class ReferenceSnapshot(Contract):
    schema_version: Literal[1] = Field(alias="schemaVersion")
    mode: Literal["reference"]
    source: Literal["TCGdex"]
    card: ReferenceCard
    fetched_at: ReferenceDatetime = Field(alias="fetchedAt")
    quotes: Annotated[tuple[ReferenceQuote, ...], Field(max_length=33)]

    @model_validator(mode="before")
    @classmethod
    def strict_schema(cls, value):
        if isinstance(value, dict) and type(value.get("schemaVersion")) is not int:
            raise ValueError("schemaVersion must be an integer")
        return value


def _json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def load_reference(card_id: str, *, base_url: str, now: datetime) -> ReferenceSnapshot:
    """Read the fixed loopback route; now is the injected request-start clock."""
    if now.tzinfo is None or now.utcoffset() is None:
        raise MarketError("naive_clock")
    if (
        not isinstance(card_id, str)
        or len(card_id) > 80
        or not re.fullmatch(CARD_ID_PATTERN, card_id)
    ):
        raise MarketError("invalid_card_id")
    try:
        if not isinstance(base_url, str) or any(ord(c) <= 32 for c in base_url):
            raise ValueError("invalid URL")
        url = urlsplit(base_url)
        if (
            url.scheme != "http"
            or not ipaddress.ip_address(url.hostname).is_loopback
            or url.username is not None
            or url.password is not None
            or url.path not in ("", "/")
            or url.query
            or url.fragment
        ):
            raise ValueError("untrusted URL")
        port = url.port if url.port is not None else 80
        if port == 0:
            raise ValueError("invalid port")
    except (ValueError, TypeError):
        raise MarketError("untrusted_reference_backend") from None

    connection = http.client.HTTPConnection(
        url.hostname, port, timeout=REFERENCE_TIMEOUT_SECONDS
    )
    started = time.monotonic()
    try:
        connection.request(
            "GET", f"/api/market/cards/{card_id}",
            headers={"Accept": "application/json", "Accept-Encoding": "identity"},
        )
        with connection.getresponse() as response:
            if response.status != 200:
                raise MarketError("reference_unavailable")
            length = response.getheader("Content-Length")
            if length is not None and not 0 <= int(length) <= MAX_REFERENCE_BYTES:
                raise ValueError("oversized body")
            if (
                response.getheader("Content-Type", "").split(";")[0].strip().lower()
                != "application/json"
                or response.getheader("Content-Encoding", "identity").lower() != "identity"
            ):
                raise ValueError("invalid response type")
            body = bytearray()
            while True:
                if time.monotonic() - started >= REFERENCE_TIMEOUT_SECONDS:
                    raise TimeoutError()
                chunk = response.read1(min(65536, MAX_REFERENCE_BYTES + 1 - len(body)))
                body.extend(chunk)
                if len(body) > MAX_REFERENCE_BYTES:
                    raise ValueError("oversized body")
                if not chunk:
                    break
            if length is not None and len(body) != int(length):
                raise ValueError("truncated body")
            snapshot = ReferenceSnapshot.model_validate(
                json.loads(body, parse_float=Decimal, object_pairs_hook=_json_object)
            )
    except TimeoutError:
        raise MarketError("reference_timeout") from None
    except (ValueError, RecursionError, InvalidOperation, http.client.HTTPException):
        raise MarketError("invalid_reference") from None
    except OSError:
        raise MarketError("reference_unavailable") from None
    finally:
        connection.close()

    elapsed = time.monotonic() - started
    if not 0 <= elapsed < REFERENCE_TIMEOUT_SECONDS:
        raise MarketError("reference_timeout")
    completed_at = now + timedelta(seconds=elapsed)
    if snapshot.card.id != card_id:
        raise MarketError("reference_identity_mismatch")
    age = (completed_at - snapshot.fetched_at).total_seconds()
    if age < 0:
        raise MarketError("future_reference")
    if age > 3600:
        raise MarketError("stale_reference")
    for quote in snapshot.quotes:
        if quote.updated_at is None:
            freshness = "unknown"
        else:
            if quote.updated_at > snapshot.fetched_at or quote.updated_at > completed_at:
                raise MarketError("future_reference")
            freshness = (
                "stale" if (completed_at - quote.updated_at).total_seconds() > 48 * 3600 else "current"
            )
        if quote.freshness != freshness:
            raise MarketError("invalid_reference_freshness")
    return snapshot


class ValuationScenario(Contract):
    gross_resale: Amount
    net_resale: Amount
    economic_ceiling: Amount


class ValuationScenarios(Contract):
    mode: Literal["simulation"] = "simulation"
    status: Literal["available", "unavailable"]
    currency: Literal["SGD"] = "SGD"
    method: Literal["observed_sales", "reviewed_assumption"] | None = None
    rounding: Literal["ROUND_FLOOR"] = "ROUND_FLOOR"
    assessment: Assessment
    conservative: ValuationScenario | None = None
    base: ValuationScenario | None = None
    upside: ValuationScenario | None = None
    evidence_ids: tuple[str, ...] = ()
    excluded_evidence_ids: tuple[str, ...] = ()
    duplicate_evidence_ids: tuple[str, ...] = ()


def valuation_scenarios(
    listing: Listing,
    evidence: tuple[Evidence, ...],
    assumptions: tuple[ReviewedAssumption, ...],
    policy: Policy,
    now: datetime,
) -> ValuationScenarios:
    """Describe min/median/max comparable observations without raising authority."""
    if any(not isinstance(item, Evidence) for item in evidence):
        raise MarketError("invalid_evidence")
    assessment = assess(listing, evidence, assumptions, policy, now)
    eligible = {}
    excluded, duplicates = [], []
    for item in sorted(evidence, key=lambda e: e.id):
        if not (
            item.card == listing.card
            and item.condition == listing.condition
            and item.currency == "SGD"
            and item.basis == "completed_sale"
            and item.completed
            and 0 <= (now - item.observed_at).total_seconds() <= policy.max_evidence_age_seconds
        ):
            excluded.append(item.id)
        elif (item.source, item.transaction_id) in eligible:
            duplicates.append(item.id)
        else:
            eligible[item.source, item.transaction_id] = item
    metadata = dict(
        assessment=assessment, evidence_ids=tuple(item.id for item in eligible.values()),
        excluded_evidence_ids=tuple(excluded), duplicate_evidence_ids=tuple(duplicates),
    )
    if assessment.gross_resale is None:
        return ValuationScenarios(status="unavailable", **metadata)
    if assessment.assumption:
        values = [assessment.assumption.gross_amount] * 3
        method = "reviewed_assumption"
    else:
        observations = sorted(item.gross_amount for item in eligible.values())
        values = [observations[0], median(observations), observations[-1]]
        method = "observed_sales"
    scenarios = []
    for gross in values:
        net = gross - assessment.selling_costs
        ceiling = net - assessment.required_profit - assessment.acquisition_costs
        scenarios.append(ValuationScenario(
            gross_resale=gross.quantize(Decimal("0.01"), rounding=ROUND_FLOOR),
            net_resale=net.quantize(Decimal("0.01"), rounding=ROUND_FLOOR),
            economic_ceiling=ceiling.quantize(Decimal("0.01"), rounding=ROUND_FLOOR),
        ))
    return ValuationScenarios(
        status="available", method=method, conservative=scenarios[0],
        base=scenarios[1], upside=scenarios[2], **metadata,
    )
