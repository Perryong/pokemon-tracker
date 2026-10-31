"""Bounded fixture A2A 1.0 JSON binding. Authentication belongs to the HTTP host."""

import copy
import hashlib
import json
from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid5

from a2a import types
from google.protobuf.json_format import MessageToDict, ParseDict, ParseError
from psycopg.types.json import Jsonb
from pydantic import ValidationError

from .contracts import Artifact, MarketError, Request

_SKILLS = {
    "market": ("reassess_opportunity", "assess_owned_unit"),
    "sales": ("negotiate_acquisition", "prepare_resale"),
}


def _sdk(value, message_type):
    """Use the actual SDK JSON binding; business numbers travel inside JSON text."""
    try:
        return MessageToDict(ParseDict(value, message_type()))
    except (ParseError, TypeError, ValueError, OverflowError):
        raise MarketError("invalid_peer_request") from None


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _business(value):
    try:
        request = Request.model_validate(value)
    except (ValidationError, TypeError, ValueError):
        raise MarketError("invalid_peer_request") from None
    return request


def peer_message(request, workspace):
    """Encode strict Request JSON in data.requestJson, preserving every numeric type."""
    data = (request.model_dump(mode="json", exclude_unset=True)
            if isinstance(request, Request) else copy.deepcopy(request))
    request = _business(data)
    if not isinstance(workspace, str) or not workspace or len(workspace) > 300:
        raise MarketError("invalid_peer_request")
    return _sdk({"message": {"messageId": request.request_id, "contextId": workspace,
                             "role": "ROLE_USER", "parts": [{"data": {
                                 "requestJson": _canonical(request.model_dump(mode="json", exclude_unset=True))
                             }}]}},
                types.SendMessageRequest)


class FixturePeerService:
    """One stable workspace, two role-scoped fixture surfaces, no commitments."""

    def __init__(self, store, workspace, *, clock=None):
        self.store = store
        self.workspace = workspace
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.session = store.session(workspace, clock=self.clock)
        # Construction is explicit development-host setup, like store.setup().
        self.session.bundle
        with store._connect() as connection:
            connection.execute("SELECT pg_advisory_xact_lock(671328590)")
            connection.execute("""
                CREATE TABLE IF NOT EXISTS market_private.peer_tasks (
                    workspace text NOT NULL,
                    role text NOT NULL CHECK (role IN ('market','sales')),
                    request_id text NOT NULL,
                    task_id text NOT NULL,
                    payload_hash text NOT NULL,
                    response jsonb,
                    PRIMARY KEY (workspace, role, request_id),
                    UNIQUE (workspace, role, task_id)
                );
                REVOKE ALL ON market_private.peer_tasks FROM PUBLIC;
                DO $$ BEGIN
                    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
                        REVOKE ALL ON market_private.peer_tasks FROM anon;
                    END IF;
                    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
                        REVOKE ALL ON market_private.peer_tasks FROM authenticated;
                    END IF;
                END $$;
            """)

    def _role(self, role):
        if role not in _SKILLS:
            raise MarketError("unsupported_role")
        return _SKILLS[role]

    def agent_card(self, base_url, role="market"):
        skills = self._role(role)
        return _sdk({
            "name": f"Fixture {role.title()}",
            "description": "Private simulation fixture; completed tasks never grant purchase approval. "
                           "Structured data.requestJson carries canonical Request JSON; "
                           "artifact data.resultJson carries canonical Artifact JSON.",
            "version": "1.0.0",
            "supportedInterfaces": [{"url": base_url.rstrip("/") + f"/a2a/{role}",
                                     "protocolBinding": "HTTP+JSON", "protocolVersion": "1.0"}],
            "capabilities": {},
            "securitySchemes": {"fixtureBearer": {"httpAuthSecurityScheme": {"scheme": "bearer"}}},
            "securityRequirements": [{"schemes": {"fixtureBearer": {"list": []}}}],
            "defaultInputModes": ["application/json"],
            "defaultOutputModes": ["application/json"],
            "skills": [{"id": skill, "name": skill.replace("_", " "),
                        "description": "Simulated " + skill.replace("_", " "),
                        "tags": ["simulation", "fixture"]} for skill in skills],
        }, types.AgentCard)

    def _request(self, payload, role):
        skills = self._role(role)
        try:
            if not isinstance(payload, dict) or set(payload) != {"message"}:
                raise ValueError()
            message = payload["message"]
            if not isinstance(message, dict) or set(message) != {"messageId", "contextId", "role", "parts"}:
                raise ValueError()
            parts = message["parts"]
            if (message["contextId"] != self.workspace or message["role"] != "ROLE_USER"
                    or not isinstance(parts, list) or len(parts) != 1
                    or not isinstance(parts[0], dict) or set(parts[0]) != {"data"}
                    or not isinstance(parts[0]["data"], dict)):
                raise ValueError()
            data = parts[0]["data"]
            if set(data) != {"requestJson"} or not isinstance(data["requestJson"], str):
                raise ValueError()
            # A JSON string survives Struct's double conversion without changing types.
            text = data["requestJson"]
            if len(text) > 65536:
                raise ValueError()
            value = json.loads(text)
            if text != _canonical(value):
                raise ValueError()
            request = _business(value)
            if message["messageId"] != request.request_id:
                raise ValueError()
            encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
            if len(encoded) > 65536:
                raise ValueError()
        except (KeyError, TypeError, ValueError, RecursionError):
            raise MarketError("invalid_peer_request") from None
        _sdk(payload, types.SendMessageRequest)
        if request.operation not in skills:
            raise MarketError("unsupported_skill")
        return request, hashlib.sha256(encoded).hexdigest()

    def _current(self, session, request):
        """Receipts are historical; validate today's authority before exposing replay."""
        if request.expires_at <= self.clock():
            raise MarketError("expired_request")
        if request.policy_version != session.bundle.policy.version:
            raise MarketError("stale_policy")
        if request.operation in ("prepare_resale", "assess_owned_unit"):
            session._owned(request)
            return
        session.read_listing(request.correlation_id)
        session.read_evidence(request.evidence_ids)
        if request.operation == "negotiate_acquisition":
            session._handle(request)
            return
        assessment = session._assessments.get(request.correlation_id)
        version = request.assessment_version
        conversation = request.conversation_version
        cached = session._requests.get(request.request_id)
        replayed = bool(cached and isinstance(cached[1], Artifact))
        if replayed:
            # Recover a committed reassessment even if its transport receipt was lost.
            expected = json.dumps(request.model_dump(mode="json"), sort_keys=True)
            if cached[0] != expected:
                raise MarketError("request_conflict")
            if request.correlation_id in session._dirty:
                raise MarketError("stale_state")
            version = cached[1].assessment.version
            conversation += 1
        if (not assessment or assessment.version != version
                or session._conversation.get(request.correlation_id, 0) != conversation):
            raise MarketError("stale_state")
        if request.mandate_id:
            mandate = session.current_mandate(request.mandate_id)
            if mandate.listing_id != request.correlation_id:
                raise MarketError("mandate_scope")
            if mandate.status != "active" and not replayed:
                raise MarketError("authority_inactive")

    def send(self, payload, role="market"):
        request, fingerprint = self._request(payload, role)
        task_id = uuid5(NAMESPACE_URL, json.dumps([self.workspace, role, request.request_id])).hex
        # Always acquire the receipt lock before the session lock. A crash between
        # commits recovers from MarketSession's durable request cache on retry.
        with self.store._connect() as connection:
            connection.execute(
                "INSERT INTO market_private.peer_tasks (workspace,role,request_id,task_id,payload_hash) "
                "VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                (self.workspace, role, request.request_id, task_id, fingerprint),
            )
            row = connection.execute(
                "SELECT payload_hash,response FROM market_private.peer_tasks "
                "WHERE workspace=%s AND role=%s AND request_id=%s FOR UPDATE",
                (self.workspace, role, request.request_id),
            ).fetchone()
            if row[0] != fingerprint:
                raise MarketError("request_conflict")
            def handle(session):
                self._current(session, request)
                return session.handle(request)
            result = self.session._call(handle)
            if row[1] is not None:
                return _sdk(row[1], types.SendMessageResponse)
            outcome = {"negotiate_acquisition": "proposed_terms", "prepare_resale": "resale_draft"}.get(request.operation, "assessment")
            response = _sdk({"task": {
                "id": task_id, "contextId": self.workspace,
                "status": {"state": "TASK_STATE_COMPLETED", "timestamp": self.clock().isoformat()},
                "artifacts": [{"artifactId": task_id + "-result", "parts": [{"data": {
                    "mode": "simulation", "peer": "fixture", "outcome": outcome,
                    "approval": False, "resultJson": _canonical(result.model_dump(mode="json")),
                }}]}],
            }}, types.SendMessageResponse)
            connection.execute(
                "UPDATE market_private.peer_tasks SET response=%s "
                "WHERE workspace=%s AND role=%s AND request_id=%s",
                (Jsonb(response), self.workspace, role, request.request_id),
            )
            return response

    def get_task(self, task_id, role="market"):
        self._role(role)
        with self.store._connect() as connection:
            row = connection.execute(
                "SELECT response FROM market_private.peer_tasks "
                "WHERE workspace=%s AND role=%s AND task_id=%s",
                (self.workspace, role, task_id),
            ).fetchone()
        if not row or row[0] is None:
            raise MarketError("record_not_found")
        return _sdk(row[0]["task"], types.Task)

    def cancel_task(self, task_id, role="market"):
        self.get_task(task_id, role)
        # Fixture work completes synchronously; cancellation cannot undo an outcome.
        raise MarketError("task_not_cancelable")
