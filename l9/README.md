# interlingua-l9 — emergent convention over an A2A extension

Two (then N) agents converge on a **shared symbol convention** they build from
scratch, and we **prove the convergence is genuine, not mimicry** — using an
**A2A extension** we define that carries L9-style epistemic structure (belief,
evidence, grounding, Theory of Mind) on every message.

Builds on:
- `Shridhar-2205/interlingua-agents` — stateless A2A ping-pong + Lewis signaling,
  and its `feature/theory-of-mind` branch (reused: `predict_acceptance`,
  `propose_with_tom`, `decide_accept`, `record_outcome`, `coin_smart`).
- `outshift-open/ioc-protocols-models` — L9 header + CIP grounding + SIEP GAR/SCR
  (vendored lean, reimplemented for the language game).

## The idea

| Piece | What it is |
|---|---|
| **Shared world** (`world.py`) | Concepts + features both agents perceive. Grounds meaning. Symbols are NOT shared — they emerge. |
| **Perceptual lens** (`lens.py`, axis A) | Each agent perceives a different feature slice (Grace=visual, Rocky=physical). The gap they must negotiate. |
| **Decision policy** (`lens.py`, axis C) | `grounding_strictness` / `compliance` — the knob that turns genuine agreement into mimicry. |
| **Theory of Mind** (`signaling.py` + `intelligence.py`) | Each agent models the peer's lexicon and reasons "what will they understand?" — the "intelligence". |
| **A2A extension** (`l9_envelope.py`) | `https://outshift.io/a2a-ext/emergence/v1` — lean L9 header + `emergence` payload in a structured DataPart. |

Hybrid intelligence: the LLM (via `litellm`, `intelligence.py`) does the two ToM
judgements (coin+justify, interpret+ground); deterministic ToM is the fallback,
so it runs with **no creds**.

## Episode (L9 grammar)

```
trigger → intent → exchange:prior (each agent coins its own lexicon)
        → exchange loop (propose → ground → adopt | contingency-repair)
        → commit:converged → knowledge (write the shared convention)
```

Starting from **independent priors** is what makes GAR/SCR meaningful — they
measure movement from a declared baseline.

## Run

```bash
python run.py            # genuine: both agents ground before adopting → W≈1.0
python run.py --mimic    # rocky adopts blind → same 100% alignment, but W drops
```

No `a2a-sdk` or LLM needed for the reasoning core — `run.py` simulates the
ping-pong in-process. Set `LLM_API_KEY` (+ `LLM_MODEL`) to switch on LLM ToM.

## Files

| File | Role |
|---|---|
| `world.py` | shared concepts + features (the known environment) |
| `lens.py` | per-agent perceptual lens (A) + decision policy (C) |
| `signaling.py` | Lewis + ToM primitives (reused) + CIP grounding + GAR/SCR/MPC/W |
| `intelligence.py` | LLM ToM at coin/ground, deterministic fallback |
| `l9_models.py` | vendored lean L9 pydantic models |
| `l9_envelope.py` | the A2A extension: URI, header/payload builders, pack/unpack |
| `agent.py` | stateless step() loop + prior formation (A2A transport = TODO) |
| `run.py` | in-process demo driver + metrics report |

## TODO

1. Wire `agent.py` to `a2a-sdk` servers/clients (mirror base `grace_agent.py`);
   advertise the extension on the Agent Card via `l9_envelope.agent_card_extension()`.
2. Turn on LLM ToM (creds) and widen the perception gap for a sharper genuine-vs-mimic contrast.
3. Phase 2: scale to 3–6 agents (Naming Game); `subprotocol` switches to `SIEP`.
4. Coordinate with colleague on the UI (consumes the `emergence` payload).
