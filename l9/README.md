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

### In-process (no deps) — logic + metrics

```bash
python run.py            # genuine: both agents ground before adopting → W≈1.0
python run.py --mimic    # rocky adopts blind → same 100% alignment, but W drops
```

### Live A2A — two real agents over HTTP

```bash
pip install -r ../requirements.txt        # a2a-sdk==1.1.2, uvicorn, ...
python rocky.py &                         # Rocky  :9102
python grace.py &                         # Grace  :9101
python trigger.py                         # Mission Control → prints the converged result
```

Each agent serves an Agent Card at `/.well-known/agent-card.json` advertising the
extension `https://outshift.io/a2a-ext/emergence/v1`; every message is the L9
envelope in a DataPart (`media_type: application/vnd.sstp.l9+json`).

**LLM ToM:** copy `.env.example` → `l9/.env` and set `OPENAI_API_KEY` (+ optional
`OPENAI_BASE_URL` for an OpenAI-compatible gateway, `LLM_MODEL`). `l9/.env` is
gitignored. With no key, the deterministic ToM fallback runs — same interface,
no LLM needed. Note: a full LLM game is ~40–50 sequential calls (minutes); for a
snappy demo, form priors deterministically and use the LLM only for negotiation.

## Reusable: `Mind` — drop a Theory-of-Mind advisor into any A2A agent

`Mind` is a **self-contained** facade (stdlib + an LLM callable you pass in; no
dependency on the Grace/Rocky demo). Any agent can import it and call it right
before it generates/sends a turn to go from reactive to strategic:

```python
from l9 import Mind                                  # add l9/'s parent to sys.path

mind = Mind("human", OBJECTS, call_llm)              # domain + LLM injected
mind.observe(history)                                # infer the peer's vocabulary
messages = history + [{"role": "system",
                       "content": mind.advise().prompt}]   # inject memory + next-move strategy
reply = call_llm(messages)
mind.record(reply)
```

- `observe(history)` recomputes belief from the whole conversation (stateless-friendly).
- `advise()` → `Advice(prompt, peer_model, grounded, unresolved)`.
- `metrics()` → `{confirmed, target, coverage, peer_model}`.

Worked example: `../free_form_env/human_agent_smart.py` wires `Mind` into the
free-form Human agent (depth A — the alien can stay dumb). Run it **instead of**
`human_agent.py` (same port 9201) against the unchanged `alien_agent.py`.

## Files

| File | Role |
|---|---|
| `world.py` | shared concepts + features (the known environment) |
| `lens.py` | per-agent perceptual lens (A) + decision policy (C) |
| `signaling.py` | Lewis + ToM primitives (reused) + CIP grounding + GAR/SCR/MPC/W |
| `intelligence.py` | LLM ToM at coin/ground, deterministic fallback |
| `l9_models.py` | vendored lean L9 pydantic models |
| `l9_envelope.py` | the A2A extension: URI, header/payload builders, pack/unpack |
| `agent.py` | stateless step() loop + prior formation (transport-free reasoning core) |
| `a2a_agent.py` | A2A server+client executor + Agent Card (advertises the extension) |
| `grace.py` / `rocky.py` | entrypoints (`:9101` / `:9102`) |
| `trigger.py` | Mission Control — kicks off a session, prints the result |
| `run.py` | in-process demo driver + metrics report |

## TODO

1. ~~Wire to a2a-sdk servers/clients + advertise the extension on the Agent Card.~~ ✅ done
2. ~~Turn on LLM ToM (OpenAI-compatible gateway).~~ ✅ done
3. **Speed up the LLM path** — full game is ~40–50 sequential calls (~5 min). Form priors
   deterministically and use the LLM only in the negotiation loop (drops ~20 calls); optionally
   fewer concepts / parallelize. Needed before a live demo.
4. Widen the perception gap for a sharper genuine-vs-mimic contrast.
5. Live `--mimic` over A2A (start Rocky with the compliant lens) for the side-by-side demo.
6. Phase 2: scale to 3–6 agents (Naming Game); `subprotocol` switches to `SIEP`.
7. Add the `A2A-Extensions` activation handshake (only needed once mixing non-emergence agents).
8. Coordinate with colleague on the UI (consumes the `emergence` payload).
