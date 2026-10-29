"""Serialized, in-memory simulated authority. No connector or payment access."""

import json
from datetime import datetime
from decimal import Decimal
from threading import RLock
from typing import Callable
from uuid import NAMESPACE_URL, uuid5
from .contracts import (
    Artifact,
    FixtureBundle,
    InventoryBundle,
    Listing,
    Mandate,
    MarketError,
    Request,
)
from .valuation import assess
from .inventory import inspection_current, summarize_inventory


class MarketSession:
    def __init__(
        self,
        bundle: FixtureBundle,
        *,
        clock: Callable[[], datetime],
        inventory: InventoryBundle | None = None,
    ):
        self.bundle = FixtureBundle.model_validate_json(bundle.model_dump_json())
        self.clock = clock
        if clock().tzinfo is None:
            raise MarketError("naive_clock")
        if bundle.policy.created_at > clock():
            raise MarketError("future_policy")
        self.inventory = (
            InventoryBundle.model_validate_json(inventory.model_dump_json())
            if inventory
            else InventoryBundle(units=(), outcomes=())
        )
        self._lock = RLock()
        self._listings = {r.id: r for r in self.bundle.listings}
        self._evidence = {r.id: r for r in self.bundle.evidence}
        self._assessments = {}
        self._mandates = {}
        self._requests = {}
        self._conversation = {}
        self._rounds = {}
        self._dirty = set()

    def _id(self, text):
        return uuid5(NAMESPACE_URL, self.bundle.session_id + ":" + text).hex

    def read_listing(self, listing_id: str) -> Listing:
        with self._lock:
            if listing_id not in self._listings:
                raise MarketError("record_not_found")
            return self._listings[listing_id]

    def read_evidence(self, evidence_ids: tuple[str, ...]):
        with self._lock:
            if any(i not in self._evidence for i in evidence_ids):
                raise MarketError("record_not_found")
            return tuple(self._evidence[i] for i in evidence_ids)

    def _expire(self):
        for mid, m in tuple(self._mandates.items()):
            if m.status == "active" and self.clock() >= m.expires_at:
                self._mandates[mid] = m.model_copy(update={"status": "expired"})

    @property
    def reserved_exposure(self) -> Decimal:
        with self._lock:
            self._expire()
            return sum(
                (m.exposure for m in self._mandates.values() if m.status == "active"),
                Decimal("0"),
            )

    def current_mandate(self, mandate_id: str) -> Mandate:
        with self._lock:
            self._expire()
            if mandate_id not in self._mandates:
                raise MarketError("record_not_found")
            return self._mandates[mandate_id]

    def _revoke(self, listing_id):
        for mid, m in tuple(self._mandates.items()):
            if m.listing_id == listing_id and m.status == "active":
                self._mandates[mid] = m.model_copy(update={"status": "revoked"})

    def ingest_listing(self, listing: Listing):
        """Trusted fixture update, deliberately not an agent tool."""
        listing = Listing.model_validate_json(listing.model_dump_json())
        with self._lock:
            old = self.read_listing(listing.id)
            if old == listing:
                return
            if old.seller_id != listing.seller_id or listing.version <= old.version:
                raise MarketError("snapshot_conflict")
            self._revoke(listing.id)
            self._dirty.add(listing.id)
            self._listings[listing.id] = listing

    def _calculate(self, r):
        a = assess(
            self.read_listing(r.correlation_id),
            self.read_evidence(r.evidence_ids),
            self.bundle.assumptions,
            self.bundle.policy,
            self.clock(),
        )
        previous = self._assessments.get(r.correlation_id)
        version = previous.version + 1 if previous else 1
        a = a.model_copy(
            update={
                "version": version,
                "id": self._id(f"{r.correlation_id}:a:{version}"),
            }
        )
        self._assessments[r.correlation_id] = a
        self._dirty.discard(r.correlation_id)
        return a

    def handle(self, request: Request) -> Artifact:
        r = Request.model_validate_json(request.model_dump_json(exclude_unset=True))
        fingerprint = json.dumps(r.model_dump(mode="json"), sort_keys=True)
        with self._lock:
            cached = self._requests.get(r.request_id)
            if cached:
                if fingerprint != cached[0]:
                    raise MarketError("request_conflict")
                if isinstance(cached[1], str):
                    raise MarketError(cached[1])
                return cached[1].model_copy(deep=True)
            try:
                result = self._handle(r)
            except MarketError as e:
                self._requests[r.request_id] = (fingerprint, e.code)
                raise
            self._requests[r.request_id] = (fingerprint, result.model_copy(deep=True))
            return result

    def read_owned_unit(self, unit_id):
        for unit in self.inventory.units:
            if unit.id == unit_id:
                return unit
        raise MarketError("record_not_found")

    def inventory_summary(self):
        return summarize_inventory(
            self.inventory.units, self.inventory.outcomes, self.clock()
        )

    def _owned(self, r):
        if r.assessment_version != 0 or r.conversation_version != 0:
            raise MarketError("stale_state")
        u = self.read_owned_unit(r.correlation_id)
        summary = summarize_inventory(
            (u,),
            tuple(o for o in self.inventory.outcomes if o.unit_id == u.id),
            self.clock(),
        )
        eligible = summary.units[0].sale_eligible
        if r.operation == "prepare_resale" and not eligible:
            raise MarketError("stock_unavailable")
        listing = Listing(
            id=u.id,
            seller_id="owned",
            version=1,
            card=u.card,
            quantity=1,
            condition=u.condition,
            condition_reviewed=inspection_current(u),
            description="",
            asking_price="0.00",
            currency="SGD",
            delivery="0.00",
            fees="0.00",
            other_costs="0.00",
        )
        a = assess(
            listing,
            self.read_evidence(r.evidence_ids),
            self.bundle.assumptions,
            self.bundle.policy,
            self.clock(),
        )
        return Artifact(
            request_id=r.request_id,
            operation=r.operation,
            correlation_id=r.correlation_id,
            assessment=a,
            inventory=summary,
        )

    def _handle(self, r):
        if r.expires_at <= self.clock():
            raise MarketError("expired_request")
        if r.policy_version != self.bundle.policy.version:
            raise MarketError("stale_policy")
        if r.operation in ("assess_owned_unit", "prepare_resale"):
            return self._owned(r)
        self.read_listing(r.correlation_id)
        self.read_evidence(r.evidence_ids)
        a = self._assessments.get(r.correlation_id)
        conv = self._conversation.get(r.correlation_id, 0)
        if (
            r.assessment_version != (a.version if a else 0)
            or r.conversation_version != conv
        ):
            raise MarketError("stale_state")
        if self._rounds.get(r.correlation_id, 0) > self.bundle.policy.max_reassessments:
            raise MarketError("reassessment_limit")
        out = dict(
            request_id=r.request_id,
            operation=r.operation,
            correlation_id=r.correlation_id,
        )
        if r.operation == "assess_opportunity":
            if (
                a is None
                or r.correlation_id in self._dirty
                or a.expires_at <= self.clock()
            ):
                self._revoke(r.correlation_id)
                a = self._calculate(r)
            return Artifact(**out, assessment=a)
        if r.operation == "reassess_opportunity":
            if not a:
                raise MarketError("assessment_required")
            if (
                r.mandate_id
                and self.current_mandate(r.mandate_id).listing_id != r.correlation_id
            ):
                raise MarketError("mandate_scope")
            count = self._rounds.get(r.correlation_id, 0)
            self._revoke(r.correlation_id)
            self._dirty.add(r.correlation_id)
            self._rounds[r.correlation_id] = count + 1
            self._conversation[r.correlation_id] = conv + 1
            listing = self.read_listing(r.correlation_id)
            changes = r.changes.model_dump(mode="json", exclude_unset=True)
            fields = {"identity": "card", "price": "asking_price"}
            values = {fields.get(k, k): v for k, v in changes.items()}
            if "condition" in changes or "identity" in changes:
                values["condition_reviewed"] = False
            values["version"] = listing.version + 1
            self._listings[listing.id] = Listing.model_validate(
                listing.model_dump(mode="json") | values
            )
            # New facts invalidate authority even when automatic reassessment is exhausted.
            if count >= self.bundle.policy.max_reassessments:
                raise MarketError("reassessment_limit")
            a = self._calculate(r)
            return Artifact(**out, assessment=a)
        if not a or r.correlation_id in self._dirty:
            raise MarketError("assessment_required")
        if r.operation == "negotiate_acquisition":
            m = self.current_mandate(r.mandate_id)
            if m.listing_id != r.correlation_id:
                raise MarketError("mandate_scope")
            if (
                m.status != "active"
                or m.assessment_version != a.version
                or m.conversation_version != conv
            ):
                raise MarketError("authority_inactive")
            return Artifact(**out, assessment=a, mandate=m)
        if r.operation != "issue_mandate":
            raise MarketError("unsupported_operation")
        if a.expires_at <= self.clock():
            raise MarketError("expired_assessment")
        mid = self._id(f"{r.correlation_id}:m:{a.version}")
        if mid in self._mandates:
            m = self.current_mandate(mid)
            if m.status != "active":
                raise MarketError("authority_inactive")
            return Artifact(**out, assessment=a, mandate=m)
        if a.decision not in ("qualified", "questions_only"):
            return Artifact(**out, assessment=a)
        ceiling = None
        exposure = Decimal("0")
        if a.decision == "qualified":
            p = self.bundle.policy
            used = self.bundle.existing_soft_exposure + self.reserved_exposure
            ceiling = min(
                a.item_ceiling,
                p.per_item_limit,
                p.available_capital - used - a.acquisition_costs,
                p.soft_exposure_cap - used - a.acquisition_costs,
            )
            if ceiling <= 0:
                a = a.model_copy(
                    update={
                        "decision": "rejected",
                        "item_ceiling": None,
                        "reasons": ("exposure_exhausted",),
                    }
                )
                self._assessments[r.correlation_id] = a
                return Artifact(**out, assessment=a)
            exposure = ceiling + a.acquisition_costs
        m = Mandate(
            id=mid,
            listing_id=r.correlation_id,
            assessment_version=a.version,
            conversation_version=conv,
            policy_version=r.policy_version,
            status="active",
            expires_at=min(r.expires_at, a.expires_at),
            ceiling=ceiling,
            exposure=exposure,
        )
        self._mandates[mid] = m
        return Artifact(**out, assessment=a, mandate=m)
