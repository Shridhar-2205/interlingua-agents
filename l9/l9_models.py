"""EIP envelope model — who's speaking, episode linkage, concept, content."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


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


class L9(BaseModel):
    protocol: str = "EIP"
    version: str = "0.1"
    participants: ParticipantSet
    message: Message
    context: Optional[Context] = None
    type: str                  # our extension uses "emergence"
    data: dict
