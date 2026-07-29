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

`SignalState` is the single source of truth for that schema. `pack_state`
serializes only these keys (rejecting unknown ones and omitting None-valued
optionals); `read_state` validates back into a `SignalState`, casting `round` to
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
class SignalState:
    """Fixed schema for the signaling payload carried in a data Part.

    Optional fields (`referent`, `message`) default to None so the terminal
    "done" message can omit them cleanly.
    """

    grace_lex: dict[str, str] = field(default_factory=dict)
    rocky_lex: dict[str, str] = field(default_factory=dict)
    round: int = 0
    referent: Optional[str] = None
    message: Optional[str] = None


# The complete, closed set of allowed payload keys — derived from SignalState so
# the schema has a single definition.
ALLOWED_KEYS = frozenset(f.name for f in fields(SignalState))


def _coerce(state: Union[SignalState, dict[str, Any]]) -> SignalState:
    """Normalize input into a SignalState, rejecting unknown keys."""
    if isinstance(state, SignalState):
        return state
    if isinstance(state, dict):
        unknown = set(state) - ALLOWED_KEYS
        if unknown:
            raise ValueError(
                f"unknown state key(s): {sorted(unknown)}; "
                f"allowed keys are {sorted(ALLOWED_KEYS)}"
            )
        return SignalState(**state)
    raise TypeError(f"state must be SignalState or dict, got {type(state).__name__}")


def pack_state(state: Union[SignalState, dict[str, Any]]) -> Part:
    """Encode state as a structured JSON `data` Part.

    Accepts a SignalState or a plain dict. Only the fixed schema keys are
    serialized; unknown keys raise ValueError. None-valued optional fields
    (referent, message) are omitted rather than written as null.
    """
    gs = _coerce(state)
    payload: dict[str, Any] = {
        "grace_lex": dict(gs.grace_lex),
        "rocky_lex": dict(gs.rocky_lex),
        "round": int(gs.round),
    }
    if gs.referent is not None:
        payload["referent"] = gs.referent
    if gs.message is not None:
        payload["message"] = gs.message

    value = struct_pb2.Value()
    value.struct_value.update(payload)
    return Part(data=value)


def read_state(message: Any) -> SignalState:
    """Read state from the first `data` Part of an incoming message.

    Returns an empty SignalState (empty lexicons, round 0, optionals None) when
    there is no message or no data Part — e.g. the initial trigger from Mission
    Control, which carries only a text Part. Unknown keys raise ValueError, and
    `round` is cast to int (protobuf stores numbers as doubles, so it arrives as
    a float such as 3.0).
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

    return SignalState(
        grace_lex=dict(raw.get("grace_lex", {})),
        rocky_lex=dict(raw.get("rocky_lex", {})),
        round=int(raw.get("round", 0)),
        referent=raw.get("referent"),
        message=raw.get("message"),
    )
