"""State channel over A2A messages (a2a-sdk 1.1.2).

Same design as the Lewis demo's emergent_state.py: all session state travels as
a structured JSON `data` Part (A2A "Option A"), never in text or metadata. The
`text` Part is cosmetic (a human-readable label like "input" or "done | ...").

The payload has a FIXED schema — exactly these keys, nothing else:

    codebook    : dict[str,str]   shared value-phrase -> short code (grows over time)
    round       : int             current round index (crosses the wire as a float
                                   via protobuf Value; cast back to int on read)
    seed        : int             RNG seed for the deterministic record stream
    total       : int             number of records in the session
    arm         : str             "verbose" | "codebook" (the only A/B difference)
    tokens_log  : list[int]       wire-tokens actually sent, per round
    verbose_log : list[int]       counterfactual spelled-out cost, per round
    wins        : int             exact reconstructions so far
    wire        : dict[str,str]   field -> transmitted segment; omitted on terminal
    reconstruction : dict[str,str] listener's decoded record; omitted until Rocky
                                   answers and on the terminal message

`CompressionState` is the single source of truth for that schema. `encode`
serializes only these keys (rejecting unknown ones and omitting None-valued
optionals); `decode` validates back into a `CompressionState`, casting numeric
fields to int and defaulting the optionals to None. Agents stay stateless.
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any, Dict, List, Optional, Union

from google.protobuf import struct_pb2
from google.protobuf.json_format import MessageToDict

from a2a.types import Part


@dataclass
class CompressionState:
    """Fixed schema for the payload carried in a data Part."""

    codebook: Dict[str, str] = field(default_factory=dict)
    round: int = 0
    seed: int = 1
    total: int = 0
    arm: str = "codebook"
    tokens_log: List[int] = field(default_factory=list)
    verbose_log: List[int] = field(default_factory=list)
    wins: int = 0
    wire: Optional[Dict[str, str]] = None
    reconstruction: Optional[Dict[str, str]] = None


ALLOWED_KEYS = frozenset(f.name for f in fields(CompressionState))


def _normalize(state: Union[CompressionState, Dict[str, Any]]) -> CompressionState:
    """Normalize input into a CompressionState, rejecting unknown keys."""
    if isinstance(state, CompressionState):
        return state
    if isinstance(state, dict):
        unknown = set(state) - ALLOWED_KEYS
        if unknown:
            raise ValueError(
                f"unknown state key(s): {sorted(unknown)}; "
                f"allowed keys are {sorted(ALLOWED_KEYS)}"
            )
        return CompressionState(**state)
    raise TypeError(f"state must be CompressionState or dict, got {type(state).__name__}")


def encode(state: Union[CompressionState, Dict[str, Any]]) -> Part:
    """Encode state into a structured JSON `data` Part for an outgoing A2A message."""
    cs = _normalize(state)
    payload: Dict[str, Any] = {
        "codebook": dict(cs.codebook),
        "round": int(cs.round),
        "seed": int(cs.seed),
        "total": int(cs.total),
        "arm": cs.arm,
        "tokens_log": [int(x) for x in cs.tokens_log],
        "verbose_log": [int(x) for x in cs.verbose_log],
        "wins": int(cs.wins),
    }
    if cs.wire is not None:
        payload["wire"] = dict(cs.wire)
    if cs.reconstruction is not None:
        payload["reconstruction"] = dict(cs.reconstruction)

    value = struct_pb2.Value()
    value.struct_value.update(payload)
    return Part(data=value)


def decode(message: Any) -> CompressionState:
    """Decode state from the first `data` Part of an incoming A2A message.

    Returns an empty CompressionState when there is no message or no data Part.
    """
    raw: Dict[str, Any] = {}
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

    wire = raw.get("wire")
    reconstruction = raw.get("reconstruction")
    return CompressionState(
        codebook={str(k): str(v) for k, v in dict(raw.get("codebook", {})).items()},
        round=int(raw.get("round", 0)),
        seed=int(raw.get("seed", 1)),
        total=int(raw.get("total", 0)),
        arm=str(raw.get("arm", "codebook")),
        tokens_log=[int(x) for x in raw.get("tokens_log", [])],
        verbose_log=[int(x) for x in raw.get("verbose_log", [])],
        wins=int(raw.get("wins", 0)),
        wire={str(k): str(v) for k, v in wire.items()} if wire is not None else None,
        reconstruction=({str(k): str(v) for k, v in reconstruction.items()}
                        if reconstruction is not None else None),
    )
