"""Hybrid intelligence — LLM at the two ToM decision points, deterministic fallback.

Two decisions get the LLM (via litellm, using your creds); if no creds / on any
error, they fall back to signaling.py's deterministic ToM so the demo always runs:

  coin(...)   SPEAKER ToM  — choose a symbol for a concept and JUSTIFY it with
                            evidence (features), reasoning about what the peer,
                            given its perception, will understand.
  ground(...) LISTENER ToM — infer which features the incoming symbol addresses,
                            then score grounding (CIP) against the speaker's evidence.

Belief lives in the payload; this module only produces the numbers/text that go there.
"""
from __future__ import annotations

import json
import os
from typing import Optional

import signaling
from lens import Lens

_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")


def available() -> bool:
    return bool(os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
                or os.environ.get("AZURE_OPENAI_API_KEY"))


def _llm(system: str, user: str) -> Optional[dict]:
    """Call the LLM, expect a JSON object back. None on any failure → caller falls back."""
    try:
        import litellm
        model = _MODEL
        base_url = os.environ.get("LLM_API_BASE") or os.environ.get("LLM_BASE_URL")
        kw: dict = {
            "model": model if not base_url or model.startswith("openai/") else f"openai/{model}",
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "temperature": 0.4,
            "response_format": {"type": "json_object"},
        }
        if os.environ.get("LLM_API_KEY"):
            kw["api_key"] = os.environ["LLM_API_KEY"]
        if base_url:
            kw["base_url"] = base_url
        resp = litellm.completion(**kw)
        return json.loads(resp.choices[0].message.content or "{}")
    except Exception as exc:  # noqa: BLE001
        print(f"  [LLM] fallback ({exc})")
        return None


# ── SPEAKER ToM: coin + justify ────────────────────────────────────────────────

def coin(concept: str, lens: Lens, my_lex: dict, peer_model: dict,
         history: list[dict]) -> tuple[str, str, list[str]]:
    """Return (symbol, rationale, evidence). Symbol via deterministic ToM;
    rationale + evidence enriched by the LLM when available."""
    proposal = signaling.propose_with_tom(dict(my_lex), dict(peer_model), history) or {}
    symbol = proposal.get("symbol") or signaling.coin_smart(my_lex, peer_model, history)
    evidence = lens.perceived_evidence(concept)

    if available():
        out = _llm(
            system=("You choose a symbol's justification in an emergent-language game. "
                    "You perceive the world through these features only. Output JSON "
                    '{"rationale": str, "evidence": [feature,...]} using ONLY given features.'),
            user=json.dumps({
                "concept": concept, "symbol": symbol,
                "my_perceived_features": evidence,
                "my_model_of_peer_lexicon": peer_model,
            }),
        )
        if out:
            evidence = [f for f in out.get("evidence", evidence) if f in evidence] or evidence
            return symbol, out.get("rationale", ""), evidence
    return symbol, f"{symbol} for {concept} (features: {', '.join(evidence)})", evidence


# ── LISTENER ToM: interpret + ground ───────────────────────────────────────────

def ground(concept: str, symbol: str, speaker_evidence: list[str], lens: Lens,
           my_lex: dict, history: list[dict]) -> tuple[list[str], float, float]:
    """Return (addresses_evidence, posterior, score). Listener infers which
    features the symbol addresses, then CIP-scores against the speaker's evidence.
    `score` is objective; the caller decides adopt/reject from its own policy."""
    my_view = lens.perceived_evidence(concept)
    addresses = [f for f in speaker_evidence if f in my_view]  # deterministic default

    if available():
        out = _llm(
            system=("You are the listener in an emergent-language game. Given a symbol a peer "
                    "proposed for a concept and the features THEY justified it with, decide which "
                    "of YOUR perceived features it addresses. Output JSON "
                    '{"addresses_evidence": [feature,...]} using only features you perceive.'),
            user=json.dumps({
                "concept": concept, "symbol": symbol,
                "speaker_evidence": speaker_evidence,
                "my_perceived_features": my_view,
            }),
        )
        if out:
            addresses = [f for f in out.get("addresses_evidence", addresses) if f in my_view] or addresses

    score = signaling.contingency_score(addresses, speaker_evidence)
    posterior = round(min(1.0, 0.3 + 0.7 * score), 4)
    return addresses, posterior, score
