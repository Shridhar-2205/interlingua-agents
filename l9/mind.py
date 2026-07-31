"""Mind — a drop-in Theory-of-Mind advisor any A2A agent can import.

Give it the shared object vocabulary and an LLM callable. Before your agent
generates/sends a turn, call `observe(history)` then `advise()`: it tracks the
peer's emerging vocabulary, tells you what's grounded vs still unresolved, and
suggests the next move — turning a reactive agent into a strategic one.

Self-contained: depends only on the standard library and the LLM callable you
pass in. No coupling to the Grace/Rocky demo (world/lens/signaling). Domain- and
transport-agnostic, and stateless-friendly — `observe()` recomputes belief from
the whole conversation each call, so it fits stateless A2A agents.

    from l9 import Mind
    mind = Mind("human", ENVIRONMENT, call_llm)
    mind.observe(history)
    messages = history + [{"role": "system", "content": mind.advise().prompt}]
    reply = call_llm(messages)
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Callable, List

Llm = Callable[[List[dict]], str]   # (messages) -> assistant text


def _extract_json(text: str) -> dict:
    """Parse a JSON object, tolerating ```json fences and surrounding prose."""
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t[3:]
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    t = t.strip()
    try:
        return json.loads(t)
    except Exception:  # noqa: BLE001
        i, j = t.find("{"), t.rfind("}")
        return json.loads(t[i:j + 1]) if i != -1 and j > i else {}


@dataclass
class Advice:
    prompt: str          # inject as a system/user message before your LLM call
    peer_model: dict     # object -> {"word": str, "count": int}
    grounded: list       # objects confirmed (count >= ground_threshold)
    unresolved: list     # objects not yet confirmed

    def __str__(self) -> str:
        return self.prompt


class Mind:
    """Local Theory-of-Mind advisor: track the peer's vocabulary, advise the next move."""

    def __init__(self, agent_id: str, objects: list, llm: Llm, *,
                 ground_threshold: int = 3, target: int = 10) -> None:
        self.agent_id = agent_id
        self.objects = list(objects)
        self.llm = llm
        self.ground_threshold = ground_threshold
        self.target = target
        self.peer_model: dict = {}          # object -> {"word", "count"}
        self._said: list = []

    # ── perception: infer the peer's vocabulary from the conversation ──────────
    def observe(self, history: list) -> "Mind":
        convo = "\n".join(f"{m.get('role')}: {m.get('content')}" for m in history)
        system = (
            "You track another agent's emerging invented vocabulary for these objects: "
            f"{', '.join(self.objects)}. Read the conversation and report, for each object the "
            "OTHER agent has consistently used a non-English/invented word for, that word and how "
            'many distinct times you saw it used for that object. '
            'Output ONLY JSON: {"vocab":[{"object":str,"word":str,"count":int}]}. '
            "Only include objects with clear evidence."
        )
        out = _extract_json(self.llm([{"role": "system", "content": system},
                                      {"role": "user", "content": convo or "(empty)"}]))
        self.peer_model = {
            v["object"]: {"word": v.get("word"), "count": int(v.get("count", 1))}
            for v in out.get("vocab", [])
            if v.get("object") in self.objects and v.get("word")
        }
        return self

    def _grounded(self) -> list:
        return [o for o, v in self.peer_model.items() if v["count"] >= self.ground_threshold]

    # ── strategy: what to do next, as a prompt block to inject ────────────────
    def advise(self) -> Advice:
        grounded = self._grounded()
        partial = [o for o in self.peer_model if o not in grounded]
        unseen = [o for o in self.objects if o not in self.peer_model]
        nxt = partial[0] if partial else (unseen[0] if unseen else None)

        lines = ["MEMORY & STRATEGY (you track the other creature's language — do NOT forget or get distracted):"]
        if grounded:
            lines.append(f"Confirmed (≥{self.ground_threshold}×): " +
                         ", ".join(f"{o}={self.peer_model[o]['word']}" for o in grounded))
        if partial:
            lines.append("Partial (need more evidence): " +
                         ", ".join(f"{o}={self.peer_model[o]['word']}({self.peer_model[o]['count']}×)" for o in partial))
        lines.append(f"Progress: {len(grounded)}/{self.target} confirmed.")
        if len(grounded) >= self.target:
            lines.append("You have enough confirmed mappings — output MAPPINGS_COMPLETE with the JSON pairs now.")
        elif nxt:
            lines.append(f"NEXT MOVE: focus on '{nxt}'. Point at it, say its name clearly, and watch which "
                         "sound the other creature makes. Stay on this one object until it is confirmed.")
        return Advice(prompt="\n".join(lines), peer_model=dict(self.peer_model),
                      grounded=grounded, unresolved=partial + unseen)

    def record(self, my_message: str) -> None:
        self._said.append(my_message)

    def metrics(self) -> dict:
        g = self._grounded()
        return {"confirmed": len(g), "target": self.target,
                "coverage": round(len(g) / self.target, 3) if self.target else 0.0,
                "peer_model": dict(self.peer_model)}
