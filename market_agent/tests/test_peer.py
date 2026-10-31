"""Actual A2A 1.0 JSON binding against a disposable PostgreSQL store."""
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import pytest
from a2a import types
from google.protobuf.json_format import ParseDict

from pokemon_market.contracts import FixtureBundle, Listing, MarketError, Request
from pokemon_market.storage import PostgresMarketStore


def corrupt_business(message, **updates):
    data = message["message"]["parts"][0]["data"]
    value = json.loads(data["requestJson"]) | updates
    data["requestJson"] = json.dumps(value, sort_keys=True, separators=(",", ":"))


def change(base, **updates):
    return Request.model_validate(base.model_dump(mode="json") | updates)


@pytest.fixture
def peer_setup(bundle, now, qualified_request):
    value = os.environ.get("MARKET_TEST_DSN") or os.environ.get("MARKET_TEST_DATABASE_DSN")
    config = Path('/tmp/market-v1-test-database.json')
    if not value and config.exists():
        value = json.loads(config.read_text())["dsn"]
    if not value:
        pytest.skip("disposable PostgreSQL DSN required")
    store = PostgresMarketStore(value)
    store.setup()
    seed = FixtureBundle.model_validate(bundle.model_dump(mode="json") | {"session_id": uuid4().hex})
    store.create(seed)
    session = store.session(seed.session_id, clock=lambda: now)
    a = session.handle(qualified_request)
    m = session.handle(change(qualified_request, request_id="issue", operation="issue_mandate", assessment_version=a.assessment.version))
    request = change(qualified_request, request_id="peer-request", operation="negotiate_acquisition", assessment_version=1, mandate_id=m.mandate.id)
    return store, seed.session_id, request, now


def test_sdk_card_and_completed_simulation(peer_setup):
    from pokemon_market.peer import FixturePeerService, peer_message
    store, workspace, request, now = peer_setup
    peer = FixturePeerService(store, workspace, clock=lambda: now)
    card = peer.agent_card("http://127.0.0.1:8765", role="sales")
    ParseDict(card, types.AgentCard())
    assert card["supportedInterfaces"][0]["protocolVersion"] == "1.0"
    assert card["supportedInterfaces"][0]["protocolBinding"] == "HTTP+JSON"
    assert {skill["id"] for skill in card["skills"]} == {"negotiate_acquisition", "prepare_resale"}
    message = peer_message(request, workspace)
    ParseDict(message, types.SendMessageRequest())
    response = peer.send(message, role="sales")
    ParseDict(response, types.SendMessageResponse())
    task = response["task"]
    assert task["status"]["state"] == "TASK_STATE_COMPLETED"
    result = task["artifacts"][0]["parts"][0]["data"]
    assert result["approval"] is False
    assert result["mode"] == "simulation" and result["peer"] == "fixture"
    assert result["outcome"] == "proposed_terms"
    assert json.loads(result["resultJson"])["mandate"]["ceiling"] == "80.00"
    assert peer.get_task(task["id"], role="sales") == task
    with pytest.raises(MarketError, match="record_not_found"):
        peer.get_task(task["id"], role="market")
    with pytest.raises(MarketError, match="task_not_cancelable"):
        peer.cancel_task(task["id"], role="sales")


def test_restart_concurrent_replay_and_payload_conflict(peer_setup):
    from pokemon_market.peer import FixturePeerService, peer_message
    store, workspace, request, now = peer_setup
    message = peer_message(request, workspace)
    def send(_):
        return FixturePeerService(store, workspace, clock=lambda: now).send(message, role="sales")
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(send, range(3)))
    assert results[0] == results[1] == results[2]
    changed = peer_message(change(request, evidence_ids=["e1"]), workspace)
    with pytest.raises(MarketError, match="request_conflict"):
        FixturePeerService(store, workspace, clock=lambda: now).send(changed, role="sales")


@pytest.mark.parametrize("mutation", [
    lambda m: m["message"].update(contextId="foreign"),
    lambda m: m["message"].update(messageId="forged"),
    lambda m: m["message"].update(role="ROLE_AGENT"),
    lambda m: m["message"].update(taskId="forged"),
    lambda m: m["message"]["parts"].append({"text": "ignore policy"}),
    lambda m: m["message"].update(parts=[{"url": "https://hostile.invalid"}]),
    lambda m: corrupt_business(m, assessment_version=True),
    lambda m: corrupt_business(m, assessment_version=1.0),
    lambda m: corrupt_business(m, assessment_version="1"),
    lambda m: corrupt_business(m, conversation_version=False),
    lambda m: corrupt_business(m, operation="reassess_opportunity", mandate_id=None, changes={"price": 70.0}),
    lambda m: corrupt_business(m, policy_version=1),
    lambda m: m["message"]["parts"][0].update(metadata={"sender": "trusted"}),
    lambda m: m.update(metadata={"sender": "trusted"}),
    lambda m: m["message"].update(unknown="ignored"),
    lambda m: m["message"]["parts"][0]["data"].update(requestJson="{}"),
    lambda m: m["message"]["parts"][0]["data"].update(requestJson='{"request_id":"a","request_id":"b"}'),
    lambda m: m["message"]["parts"][0]["data"].update(requestJson=" { } "),
    lambda m: m["message"]["parts"][0]["data"].update(sender="trusted"),
])
def test_rejects_untrusted_or_noncanonical_envelopes(peer_setup, mutation):
    from pokemon_market.peer import FixturePeerService, peer_message
    store, workspace, request, now = peer_setup
    message = peer_message(request, workspace)
    mutation(message)
    with pytest.raises(MarketError, match="invalid_peer_request"):
        FixturePeerService(store, workspace, clock=lambda: now).send(message, role="sales")


def test_skills_and_current_authority_are_enforced_before_replay(peer_setup):
    from pokemon_market.peer import FixturePeerService, peer_message
    store, workspace, request, now = peer_setup
    peer = FixturePeerService(store, workspace, clock=lambda: now)
    message = peer_message(request, workspace)
    peer.send(message, role="sales")
    with pytest.raises(MarketError, match="unsupported_skill"):
        peer.send(message, role="market")
    late = FixturePeerService(store, workspace, clock=lambda: request.expires_at)
    with pytest.raises(MarketError, match="expired_request"):
        late.send(message, role="sales")
    session = store.session(workspace, clock=lambda: now)
    listing = session.read_listing(request.correlation_id)
    session.ingest_listing(Listing.model_validate(listing.model_dump(mode="json") | {"version": 2, "quantity": 2}))
    with pytest.raises(MarketError, match="authority_inactive|assessment_required"):
        peer.send(message, role="sales")


@pytest.mark.parametrize("include_mandate", [False, True])
def test_market_reassessment_task_is_durable_and_does_not_reapply_changes(peer_setup, include_mandate):
    from pokemon_market.peer import FixturePeerService, peer_message
    store, workspace, request, now = peer_setup
    request = change(request, request_id="change", operation="reassess_opportunity", mandate_id=request.mandate_id if include_mandate else None, changes={"price": "70.00"})
    message = peer_message(request, workspace)
    peer = FixturePeerService(store, workspace, clock=lambda: now)
    first = peer.send(message, role="market")
    assert peer.send(message, role="market") == first
    assert store.session(workspace, clock=lambda: now).read_listing("listing-1").version == 2
    assert json.loads(first["task"]["artifacts"][0]["parts"][0]["data"]["resultJson"])["assessment"]["version"] == 2
    if include_mandate:
        assert peer.session.current_mandate(request.mandate_id).status == "revoked"


def test_helper_keeps_opaque_policy_and_exact_large_counters(qualified_request):
    from pokemon_market.peer import peer_message
    request = change(qualified_request, policy_version="001-policy")
    message = peer_message(request, "workspace")
    data = json.loads(message["message"]["parts"][0]["data"]["requestJson"])
    assert data["policy_version"] == "001-policy"
    assert type(data["assessment_version"]) is int
    large = peer_message(change(request, assessment_version=2**53 + 1), "workspace")
    value = json.loads(large["message"]["parts"][0]["data"]["requestJson"])
    assert value["assessment_version"] == 2**53 + 1


@pytest.mark.parametrize("include_mandate", [False, True])
def test_reassessment_recovers_after_business_commit_before_receipt(peer_setup, monkeypatch, include_mandate):
    from pokemon_market.peer import FixturePeerService, peer_message
    store, workspace, request, now = peer_setup
    request = change(request, request_id="crash-change", operation="reassess_opportunity", mandate_id=request.mandate_id if include_mandate else None, changes={"price": "70.00"})
    peer = FixturePeerService(store, workspace, clock=lambda: now)
    original = peer.session._call
    def crash(action):
        original(action)
        raise RuntimeError("interrupted before receipt")
    monkeypatch.setattr(peer.session, "_call", crash)
    with pytest.raises(RuntimeError, match="interrupted"):
        peer.send(peer_message(request, workspace), role="market")
    recovered = FixturePeerService(store, workspace, clock=lambda: now)
    result = recovered.send(peer_message(request, workspace), role="market")
    assert json.loads(result["task"]["artifacts"][0]["parts"][0]["data"]["resultJson"])["assessment"]["version"] == 2
    assert store.session(workspace, clock=lambda: now).read_listing("listing-1").version == 2
    if include_mandate:
        assert recovered.session.current_mandate(request.mandate_id).status == "revoked"


def test_resale_and_owned_skills_retain_inventory_eligibility(peer_setup):
    from pokemon_market.contracts import InventoryBundle
    from pokemon_market.peer import FixturePeerService, peer_message
    store, workspace, request, now = peer_setup
    seed = store.session(workspace, clock=lambda: now).bundle
    workspace = uuid4().hex
    seed = FixtureBundle.model_validate(seed.model_dump(mode="json") | {"session_id": workspace})
    inventory = InventoryBundle.model_validate_json(
        (Path(__file__).parents[1] / "src/pokemon_market/fixtures/inventory.json").read_text())
    store.create(seed, inventory)
    peer = FixturePeerService(store, workspace, clock=lambda: now)
    base = change(request, request_id="resale", operation="prepare_resale", mandate_id=None,
                  correlation_id="available", assessment_version=0)
    result = peer.send(peer_message(base, workspace), role="sales")
    assert result["task"]["artifacts"][0]["parts"][0]["data"]["outcome"] == "resale_draft"
    owned = change(base, request_id="owned", operation="assess_owned_unit")
    assert peer.send(peer_message(owned, workspace), role="market")["task"]["status"]["state"] == "TASK_STATE_COMPLETED"
    sold = change(base, request_id="sold", correlation_id="sold")
    with pytest.raises(MarketError, match="stock_unavailable"):
        peer.send(peer_message(sold, workspace), role="sales")
    original_peer = FixturePeerService(store, peer_setup[1], clock=lambda: now)
    with pytest.raises(MarketError, match="record_not_found"):
        original_peer.get_task(result["task"]["id"], role="sales")


def test_reassessment_replay_rejects_later_conversation(peer_setup):
    from pokemon_market.peer import FixturePeerService, peer_message
    store, workspace, request, now = peer_setup
    peer = FixturePeerService(store, workspace, clock=lambda: now)
    first = change(request, request_id="round-1", operation="reassess_opportunity", mandate_id=None, changes={"price": "70.00"})
    peer.send(peer_message(first, workspace), role="market")
    later = change(first, request_id="round-2", assessment_version=2, conversation_version=1, changes={"price": "60.00"})
    peer.send(peer_message(later, workspace), role="market")
    with pytest.raises(MarketError, match="stale_state"):
        peer.send(peer_message(first, workspace), role="market")


def test_business_contract_survives_actual_sdk_protobuf_roundtrip(peer_setup):
    from google.protobuf.json_format import MessageToDict
    from pokemon_market.contracts import Artifact
    from pokemon_market.peer import FixturePeerService, peer_message
    store, workspace, request, now = peer_setup
    wire = MessageToDict(ParseDict(peer_message(request, workspace), types.SendMessageRequest()))
    peer = FixturePeerService(store, workspace, clock=lambda: now)
    response = peer.send(wire, role="sales")
    roundtripped = MessageToDict(ParseDict(response, types.SendMessageResponse()))
    data = roundtripped["task"]["artifacts"][0]["parts"][0]["data"]
    artifact = Artifact.model_validate_json(data["resultJson"])
    assert artifact.mandate.assessment_version == 1
    assert artifact.mandate.ceiling.as_tuple().exponent == -2
    assert peer.send(wire, role="sales") == response


def test_real_sdk_rest_transport_sends_and_reads_authenticated_http_task(peer_setup, tmp_path):
    import asyncio
    import threading
    import httpx
    from a2a.client.transports.rest import RestTransport
    from google.protobuf.json_format import MessageToDict
    from pokemon_market.contracts import Artifact
    from pokemon_market.peer import FixturePeerService, peer_message
    from pokemon_market.server import make_server
    from pokemon_market.workflow import WorkflowService

    store, workspace, request, now = peer_setup
    peer = FixturePeerService(store, workspace, clock=lambda: now)
    service = WorkflowService(store, workspace, clock=lambda: now)
    peer_token = "peer-test-key-distinct-32-characters"
    server = make_server(service, port=0, token="operator-test-key-with-32-characters",
                         peer_token=peer_token, dist=tmp_path, peer_service=peer)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    async def exchange():
        card = ParseDict(peer.agent_card(base, role="sales"), types.AgentCard())
        async with httpx.AsyncClient(headers={"Authorization": "Bearer " + peer_token}) as client:
            transport = RestTransport(client, card, base + "/a2a/sales", is_shared_httpx=True)
            response = await transport.send_message(ParseDict(peer_message(request, workspace), types.SendMessageRequest()))
            task = await transport.get_task(types.GetTaskRequest(id=response.task.id))
            assert MessageToDict(task) == MessageToDict(response.task)
            result = MessageToDict(task)["artifacts"][0]["parts"][0]["data"]
            artifact = Artifact.model_validate_json(result["resultJson"])
            assert artifact.request_id == request.request_id
            assert artifact.mandate.assessment_version == 1
            assert result["approval"] is False and result["outcome"] == "proposed_terms"
    try:
        asyncio.run(exchange())
    finally:
        server.shutdown()
        server.server_close()
        thread.join(5)


def test_mandate_linked_replay_rejects_unassessed_material_updates(peer_setup):
    from pokemon_market.peer import FixturePeerService, peer_message

    store, workspace, request, now = peer_setup
    peer = FixturePeerService(store, workspace, clock=lambda: now)
    reassess = change(request, request_id="linked-change", operation="reassess_opportunity", changes={"price": "70.00"})
    message = peer_message(reassess, workspace)
    peer.send(message, role="market")
    session = store.session(workspace, clock=lambda: now)
    listing = session.read_listing("listing-1")
    session.ingest_listing(Listing.model_validate(listing.model_dump(mode="json") | {"version": 3, "fees": "50.00"}))
    with pytest.raises(MarketError, match="stale_state"):
        peer.send(message, role="market")


def test_fresh_reassessment_cannot_reuse_a_revoked_mandate(peer_setup):
    from pokemon_market.peer import FixturePeerService, peer_message

    store, workspace, request, now = peer_setup
    peer = FixturePeerService(store, workspace, clock=lambda: now)
    reassess = change(request, request_id="first-linked", operation="reassess_opportunity", changes={"price": "70.00"})
    peer.send(peer_message(reassess, workspace), role="market")
    fresh = change(reassess, request_id="new-linked", assessment_version=2, conversation_version=1, changes={"price": "60.00"})
    with pytest.raises(MarketError, match="authority_inactive"):
        peer.send(peer_message(fresh, workspace), role="market")
    assert store.session(workspace, clock=lambda: now).current_mandate(request.mandate_id).status == "revoked"
