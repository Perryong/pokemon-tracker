"""Deterministic authorization and an in-memory simulated connector.

Only this trusted boundary can render counterparty messages. Model-generated prose
is never dispatched. A session is single-use, serial and scoped to one conversation.
"""
from collections import deque
from copy import deepcopy
from datetime import datetime, timezone
from threading import RLock
import re
from .contracts import Lead, Mandate, SellerReply

QUESTIONS = {
    'condition': 'Could you confirm the condition and any damage?',
    'printing': 'Could you confirm the exact set, number, language and printing?',
    'photos': 'Could you provide clear front and back photos?',
    'delivery': 'What delivery methods and costs are available?',
}
ACTIONS = frozenset({'ask_question', 'propose_price', 'prepare_proposal'})


class SimulatedSeller:
    """Fixture transport, with no network or commitment API."""
    def __init__(self, replies):
        self._replies = deque(SellerReply.model_validate(deepcopy(r)) for r in replies)
        self.sent = []

    def exchange(self, *, conversation_id, seller_id, listing_id, text):
        self.sent.append(dict(conversation_id=conversation_id, seller_id=seller_id,
                              listing_id=listing_id, text=text))
        return self._replies.popleft() if self._replies else SellerReply(text='No additional seller facts in this fixture.', facts_reviewed=True)


class SalesSession:
    def __init__(self, *, lead, mandate, current, seller, clock=None):
        self.lead = Lead.model_validate(deepcopy(lead))
        self.mandate = Mandate.model_validate(deepcopy(mandate))
        if (self.lead.lead_id, self.lead.conversation_id, self.lead.currency) != (
                self.mandate.lead_id, self.mandate.conversation_id, self.mandate.currency):
            raise ValueError('mandate does not match lead scope')
        # Trusted service state; never supplied as a model tool argument.
        self.current = dict(current)
        self.seller = seller
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.rounds = 0
        self.opted_out = False
        self.reassessment = None
        self.proposal = None
        self.last_price = None
        self.transcript = []
        self._lock = RLock()

    def _reject(self, reason):
        self.proposal = None
        return {'status': 'rejected', 'reason': reason}

    def _guard(self, conversation_id):
        if conversation_id != self.lead.conversation_id: return 'wrong_conversation'
        if self.opted_out: return 'seller_opt_out'
        now = self.clock()
        if now.tzinfo is None: return 'invalid_clock'
        if now >= self.mandate.expires_at: return 'expired_mandate'
        if any(type(self.current.get(k)) is not int or self.current[k] != getattr(self.mandate, k)
               for k in ('policy_version', 'state_version')): return 'stale_mandate'
        if self.reassessment: return 'reassessment_required'
        return None

    def act(self, action, conversation_id, **arguments):
        with self._lock:
            reason = self._guard(conversation_id)
            if reason: return self._reject(reason)
            if action not in ACTIONS: return self._reject('unavailable_action')
            expected = {'topic'} if action == 'ask_question' else {'amount_minor'}
            if set(arguments) != expected: return self._reject('invalid_arguments')
            if action == 'ask_question':
                topic = arguments['topic']
                if not isinstance(topic, str) or topic not in QUESTIONS:
                    return self._reject('invalid_topic')
                text = QUESTIONS[topic]
            else:
                amount = arguments['amount_minor']
                ceiling = self.mandate.ceiling_minor
                if ceiling is None: return self._reject('questions_only')
                if type(amount) is not int or not 0 < amount <= ceiling:
                    return self._reject('price_out_of_mandate')
                text = (f'Would SGD {amount // 100}.{amount % 100:02d} be possible, '
                        'subject to final operator approval and verification of the stated card and condition? '
                        'This is a conditional enquiry only.')
            if action == 'prepare_proposal':
                if self.last_price != amount:
                    return self._reject('no_matching_conditional_proposal')
                self.proposal = {
                    'status': 'awaiting_operator_approval',
                    'lead_id': self.lead.lead_id, 'mandate_id': self.mandate.mandate_id,
                    'conversation_id': self.lead.conversation_id,
                    'seller_id': self.lead.seller_id, 'listing_id': self.lead.listing_id,
                    'card': self.lead.card.model_dump(), 'condition': self.lead.condition,
                    'evidence': list(self.lead.evidence), 'quantity': 1,
                    'amount_minor': amount, 'currency': self.lead.currency,
                    'policy_version': self.mandate.policy_version,
                    'state_version': self.mandate.state_version,
                    'conversation_version': self.rounds,
                    'expires_at': self.mandate.expires_at.isoformat(),
                    'exact_commitment_draft': f'Proposed purchase: 1 card for SGD {amount // 100}.{amount % 100:02d}, subject to operator review of card identity, condition and delivery.',
                    'unresolved_terms': ['delivery and fees', 'payment and meetup details'],
                    'dispatchable': False,
                }
                return {'status': 'awaiting_operator_approval', 'proposal': deepcopy(self.proposal)}
            if self.rounds >= self.mandate.max_rounds:
                return self._reject('rounds_exhausted')
            self.proposal = None
            self.rounds += 1
            reply = self.seller.exchange(conversation_id=self.lead.conversation_id,
                seller_id=self.lead.seller_id, listing_id=self.lead.listing_id, text=text)
            self.transcript.append({'outbound': text, 'seller': reply.model_dump()})
            if action == 'propose_price': self.last_price = amount
            if reply.opt_out or re.search(r'\b(stop|unsubscribe|do not contact|don.t contact|leave me alone)\b', reply.text, re.I):
                self.opted_out = True
                self.last_price = None
            if not self.opted_out and (reply.material_facts or (reply.text and not reply.facts_reviewed)):
                self.last_price = None
                self.reassessment = {
                    'kind': 'market_reassessment_request',
                    'transport': 'local_fixture_unauthenticated',
                    'lead_id': self.lead.lead_id, 'conversation_id': self.lead.conversation_id,
                    'mandate_id': self.mandate.mandate_id,
                    'conversation_version': self.rounds,
                    'policy_version': self.mandate.policy_version,
                    'state_version': self.mandate.state_version,
                    'facts': dict(reply.material_facts) or {'unclassified_seller_message': reply.text},
                    'requires_replacement_mandate': True,
                }
            return {'status': 'sent', 'seller_reply': reply.model_dump(),
                    'reassessment': deepcopy(self.reassessment)}
