"""Temporary fixture contracts; these do not authenticate a Market Agent."""
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, AwareDatetime

Text = Annotated[str, Field(min_length=1, max_length=300, pattern=r'\S')]
Positive = Annotated[int, Field(strict=True, gt=0)]


class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)


class Card(Contract):
    name: Text
    set_code: Text
    number: Text
    language: Literal['en', 'ja']
    printing: Text


class Lead(Contract):
    lead_id: Text
    conversation_id: Text
    seller_id: Text
    listing_id: Text
    card: Card
    condition: Text
    evidence: Annotated[tuple[Text, ...], Field(min_length=1, max_length=20)]
    currency: Literal['SGD']


class Mandate(Contract):
    mandate_id: Text
    lead_id: Text
    conversation_id: Text
    currency: Literal['SGD']
    ceiling_minor: Positive | None  # None grants questions-only authority
    max_rounds: Annotated[int, Field(strict=True, gt=0, le=20)]
    policy_version: Positive
    state_version: Positive
    expires_at: AwareDatetime


class SellerReply(Contract):
    text: Annotated[str, Field(max_length=4000)] = ''
    opt_out: Annotated[bool, Field(strict=True)] = False
    facts_reviewed: Annotated[bool, Field(strict=True)] = False
    material_facts: dict[Literal['condition', 'printing', 'quantity', 'delivery', 'fees', 'identity'], Text] = Field(default_factory=dict)
