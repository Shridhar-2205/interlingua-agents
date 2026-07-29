"""Vendored lean L9 models (Apache-2.0, from outshift-open/ioc-protocols-models).

Only the header fields the emergence extension actually uses. Everything the
distributed Cognition Fabric needs but we don't (policy, semantic routing, the
empty epistemic placeholder) is omitted. Belief/grounding/evidence live in the
PAYLOAD, not the header — see l9_envelope.EMERGENCE_PAYLOAD_TYPE.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class Kind(str, Enum):
    intent = "intent"          # open the episode: declare concept space + group
    exchange = "exchange"      # a proposal / prior declaration / grounding turn
    contingency = "contingency"  # grounding failed → open a repair branch
    commit = "commit"          # close the episode (subkind: converged | ready | resolved)
    knowledge = "knowledge"    # write the converged convention out


class Actor(BaseModel):
    id: str
    role: str                  # "sender" | "receiver" | "observer"


class ParticipantSet(BaseModel):
    actors: list[Actor]
    groups: Optional[dict] = None


class Message(BaseModel):
    id: str
    parents: list[str]
    episode: str


class Context(BaseModel):
    topic: str                 # the concept/referent, e.g. "concept:river"


class L9Payload(BaseModel):
    type: str                  # our extension uses "emergence"
    data: dict


class L9Header(BaseModel):
    protocol: str = "SSTP"
    subprotocol: str           # "CIP" (pair) | "SIEP" (population)
    version: str = "0.1"
    kind: Kind
    subkind: Optional[str] = None
    participants: ParticipantSet
    message: Message
    context: Optional[Context] = None


class L9(BaseModel):
    header: L9Header
    payload: L9Payload
