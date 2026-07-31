"""The A2A extension we define — 'emergence' — plus ELP pack/unpack.

An A2A Extension = a URI advertised on the Agent Card's capabilities.extensions,
listed in each message's `extensions`, whose payload contract we define. Ours
carries a flat ELP envelope (l9_models.L9) in a structured A2A DataPart, with a
content type `emergence` that adds belief, evidence, grounding, a ToM
belief-model, and history to every message — so convention convergence is
observable and measurable.

Layering:
  build_l9(...)  -> L9            build the envelope
  pack_l9(l9)    -> dict          JSON-able (goes into a Part's data Value)
  unpack_l9(d)   -> L9            validate back
  to_data_part / from_a2a        thin a2a-sdk wrappers (lazy import)
"""
from __future__ import annotations

import uuid
from typing import Any, Optional

from l9_models import L9, Actor, ParticipantSet, Message, Context

# ── The extension identity ─────────────────────────────────────────────────────
EXT_URI = "https://outshift.io/a2a-ext/emergence/v1"
EMERGENCE_PAYLOAD_TYPE = "emergence"
MEDIA_L9 = "application/vnd.elp+json"   # DataPart media_type (self-describing)

# `data` schema (documented; not enforced beyond dict):
#   lexicons   : {agent_id: {concept: symbol}}   full state (agents stay stateless)
#   round      : int
#   speaker    : agent_id
#   referent   : concept being proposed this turn
#   proposal   : symbol proposed
#   utterance  : {text, evidence:[feature], addresses_evidence:[feature]}
#   grounding  : {contingency_verified: bool, contingency_score: float, repair_reason: str|None}
#                always null as written on the wire today — the listener's actual
#                score/addresses_evidence are used internally (agent.step) and only
#                surface as history[].accepted/grounded, not written back here
#   belief     : {prior: float, posterior: float, revision_cause: str}
#   tom        : {agent_id: {concept: symbol}}    sender's MODEL of each peer's lexicon
#   history    : [{referent, symbol, accepted, grounded, speaker}]  the GAR/SCR event log
#   decision   : "init" | "propose" | "converged"   (the only values agent.step produces)


def episode_urn(concept: str, run_id: str) -> str:
    return f"urn:ioc:emerge:{concept}:{run_id}"


def build_l9(
    *,
    sender: str,
    recipients: list[str],
    episode: str,
    data: dict,
    topic: Optional[str] = None,
    parents: Optional[list[str]] = None,
) -> L9:
    """Build a flat ELP message for the emergence extension."""
    actors = [Actor(id=sender, role="sender")] + [Actor(id=r, role="receiver") for r in recipients]
    return L9(
        participants=ParticipantSet(actors=actors, groups=None),
        message=Message(id=uuid.uuid4().hex, parents=parents or [], episode=episode),
        context=Context(topic=topic) if topic else None,
        type=EMERGENCE_PAYLOAD_TYPE,
        data=data,
    )


def pack_l9(l9: L9) -> dict[str, Any]:
    return l9.model_dump(mode="json")


def unpack_l9(d: dict[str, Any]) -> L9:
    return L9.model_validate(d)


# ── a2a-sdk wrappers (lazy import so the core is testable without a2a) ──────────

def to_data_part(l9: L9):
    """Wrap the L9 envelope in a self-describing A2A DataPart (media_type set)."""
    from google.protobuf import struct_pb2
    from a2a.types import Part
    value = struct_pb2.Value()
    value.struct_value.update(pack_l9(l9))
    return Part(data=value, media_type=MEDIA_L9)


def from_a2a(message) -> Optional[L9]:
    """Pull the L9 envelope out of the first data Part of an A2A message."""
    from google.protobuf.json_format import MessageToDict
    if message is None:
        return None
    for part in message.parts:
        if part.WhichOneof("content") == "data":
            return unpack_l9(MessageToDict(part).get("data", {}))
    return None


def agent_card_extension() -> dict:
    """Descriptor to advertise on the Agent Card's capabilities.extensions."""
    return {
        "uri": EXT_URI,
        "description": "Emergent-convention convergence with belief/grounding/ToM (ELP-over-A2A).",
        "required": False,
        "params": {
            "protocol": "ELP",
            "payload_type": EMERGENCE_PAYLOAD_TYPE,
            "carries": ["lexicons", "utterance", "grounding", "belief", "tom", "history"],
        },
    }
