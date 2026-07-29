"""State channel over A2A messages (a2a-sdk 1.1.2).

All state travels as a structured JSON `data` Part (A2A "Option A"), not in
message metadata or text. In the 1.1.2 protobuf schema a `Part` is a oneof over
text | raw | url | data, where `data` is a google.protobuf.Value — so the JSON
is carried inline (no type/mimeType/bytes wrapper).

The payload has a FIXED schema — exactly these keys, nothing else:

    grace_lex : dict[str, str]     meaning -> symbol (Grace's lexicon)
    rocky_lex : dict[str, str]     meaning -> symbol (Rocky's lexicon)
    round     : int                round counter (crosses the wire as a float
                                    via protobuf Value; cast back to int on read)
    referent  : str | None         meaning being negotiated; omitted on the
                                    terminal "done" message
    message   : str | None         proposed symbol; omitted on the terminal
                                    "done" message

`EmergentState` is the single source of truth for that schema. `encode`
serializes only these keys (rejecting unknown ones and omitting None-valued
optionals); `decode` validates back into an `EmergentState`, casting `round` to
int and defaulting the optionals to None. Agents stay stateless: read state from
the incoming message, do one step, write new state on the way out.
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any, Optional, Union

from google.protobuf import struct_pb2
from google.protobuf.json_format import MessageToDict

from a2a.types import Part


@dataclass
class EmergentState:
    """Fixed schema for the payload carried in a data Part."""

    grace_lex: dict[str, str] = field(default_factory=dict)
    rocky_lex: dict[str, str] = field(default_factory=dict)
    round: int = 0
    referent: Optional[str] = None
    message: Optional[str] = None


ALLOWED_KEYS = frozenset(f.name for f in fields(EmergentState))


def _normalize(state: Union[EmergentState, dict[str, Any]]) -> EmergentState:
    """Normalize input into an EmergentState, rejecting unknown keys."""
    if isinstance(state, EmergentState):
        return state
    if isinstance(state, dict):
        unknown = set(state) - ALLOWED_KEYS
        if unknown:
            raise ValueError(
                f"unknown state key(s): {sorted(unknown)}; "
                f"allowed keys are {sorted(ALLOWED_KEYS)}"
            )
        return EmergentState(**state)
    raise TypeError(f"state must be EmergentState or dict, got {type(state).__name__}")


def encode(state: Union[EmergentState, dict[str, Any]]) -> Part:
    """Encode state into a structured JSON `data` Part for an outgoing A2A message."""
    es = _normalize(state)
    payload: dict[str, Any] = {
        "grace_lex": dict(es.grace_lex),
        "rocky_lex": dict(es.rocky_lex),
        "round": int(es.round),
    }
    if es.referent is not None:
        payload["referent"] = es.referent
    if es.message is not None:
        payload["message"] = es.message

    value = struct_pb2.Value()
    value.struct_value.update(payload)
    return Part(data=value)


def decode(message: Any) -> EmergentState:
    """Decode state from the first `data` Part of an incoming A2A message.

    Returns an empty EmergentState when there is no message or no data Part.
    """
    raw: dict[str, Any] = {}
    if message is not None:
        for part in message.parts:
            if part.WhichOneof("content") == "data":
                raw = MessageToDict(part).get("data", {})
                break

    unknown = set(raw) - ALLOWED_KEYS
    if unknown:
        raise ValueError(
            f"unknown state key(s): {sorted(unknown)}; "
            f"allowed keys are {sorted(ALLOWED_KEYS)}"
        )

    return EmergentState(
        grace_lex=dict(raw.get("grace_lex", {})),
        rocky_lex=dict(raw.get("rocky_lex", {})),
        round=int(raw.get("round", 0)),
        referent=raw.get("referent"),
        message=raw.get("message"),
    )
