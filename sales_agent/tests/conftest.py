from datetime import datetime, timezone
import pytest

NOW = datetime(2026, 10, 29, 12, tzinfo=timezone.utc)

@pytest.fixture
def payload():
    return {
        'lead': {'lead_id': 'lead-1', 'conversation_id': 'thread-1',
                 'seller_id': 'seller-1', 'listing_id': 'listing-1',
                 'card': {'name': 'Pikachu', 'set_code': 'SV1', 'number': '025',
                          'language': 'en', 'printing': 'reverse-holo'},
                 'condition': 'near-mint', 'evidence': ['fixture:front-photo'],
                 'currency': 'SGD'},
        'mandate': {'mandate_id': 'mandate-1', 'lead_id': 'lead-1',
                    'conversation_id': 'thread-1', 'currency': 'SGD',
                    'ceiling_minor': 5000, 'max_rounds': 3,
                    'policy_version': 1, 'state_version': 1,
                    'expires_at': '2026-10-29T13:00:00Z'},
    }

@pytest.fixture
def factory(payload):
    from pokemon_sales.session import SalesSession, SimulatedSeller
    def make(*, replies=None, data=None, clock=None):
        return SalesSession(**(data or payload),
            current={'policy_version': 1, 'state_version': 1},
            seller=SimulatedSeller(replies or []), clock=clock or (lambda: NOW))
    return make
