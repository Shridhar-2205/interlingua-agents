"""Game-state channel over A2A messages (a2a-sdk 1.1.2).

State travels as a structured JSON `data` Part (A2A "Option A"), not in message
metadata. In the 1.1.2 protobuf schema a `Part` is a oneof over
text | raw | url | data, where `data` is a google.protobuf.Value — so the JSON
is carried inline (no type/mimeType/bytes wrapper).

All game state (both lexicons, round number, current referent, and the proposed
symbol) lives in a single `data` Part. Agents stay stateless: read the state
Part from the incoming message, do one step, write a new state Part on the way out.
"""
from __future__ import annotations

from typing import Any

from google.protobuf import struct_pb2
from google.protobuf.json_format import MessageToDict

from a2a.types import Part


def pack_state(state: dict[str, Any]) -> Part:
    """Encode game state as a structured JSON `data` Part."""
    value = struct_pb2.Value()
    value.struct_value.update(state)
    return Part(data=value)


def read_state(message: Any) -> dict[str, Any]:
    """Read game state from the first `data` Part of an incoming message.

    Returns an empty dict when there is no message or no data Part (e.g. the
    initial trigger from Mission Control, which carries only a text Part).

    Note: protobuf stores all numbers as doubles, so ints arrive as floats
    (3 -> 3.0). Callers cast where exact ints matter (e.g. `int(state["round"])`).
    """
    if message is None:
        return {}
    for part in message.parts:
        if part.WhichOneof("content") == "data":
            return MessageToDict(part).get("data", {})
    return {}
