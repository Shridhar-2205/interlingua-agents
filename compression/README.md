# Mission Log Relay — emergent shorthand for token compression

A second emergent-language demo built with the **same conventions as the root
Lewis demo** (stateless A2A ping-pong, full state in one JSON `data` Part,
pure-logic + state + two agents + tests). Instead of *converging on a lexicon*,
the agents *compress a communication stream*: they build a shared **codebook**
so recurring content costs fewer tokens over time.

## The idea

Grace relays a stream of structured **mission-log records** to Rocky, who must
reconstruct each one exactly. Records reuse a small vocabulary of multi-word
phrases, so most content recurs. A thin **protocol** lets the pair build a
shared codebook: **DEFINE** a short code for a phrase once (costs the full
phrase that round), then **REFER** to it cheaply forever after.

Two arms, identical task, one flag (`arm`) apart:

| arm | behaviour | token cost |
|-----|-----------|-----------|
| `verbose` | spell every value, every round | flat |
| `codebook` | DEFINE once, then REFER (the protocol) | decays as the codebook fills |

Both arms are **lossless** — exact reconstruction, so accuracy is 100% in both.
The protocol buys **cost, not correctness**. That's the whole point.

## Result (seed=1, 24 records)

```
arm: verbose  | accuracy: 24/24 | tokens: 288 (vs verbose 288) | ratio: 1.00x | per-round 12.0 -> 12.0
arm: codebook | accuracy: 24/24 | tokens: 125 (vs verbose 288) | ratio: 2.30x | per-round  8.8 ->  4.0
```

The codebook arm starts at the verbose cost (all DEFINEs) and decays toward the
floor (all REFER = one token per field) as the shared codebook fills in.

## Files (mirrors the root demo's layout)

```
compress.py               — pure logic: records, DEFINE/REFER coding, decode, token count
                            (+ an offline simulator: `python compress.py --curve`)
compress_state.py         — state channel: encode/decode a fixed-schema data Part
grace_compress_agent.py   — stateless speaker/scorer + A2A server/client (Grace, :9201)
rocky_compress_agent.py   — stateless listener      + A2A server/client (Rocky, :9202)
test_compress.py          — unit + integration tests
llm_compress.py           — LLM version: agents INVENT their own shorthand (see below)
.env.example              — LLM credentials template for llm_compress.py (copy to .env)
```

## LLM version (`llm_compress.py`)

This is to `compress.py` what `l9/` is to the root Lewis demo: the same task, but
LLM-driven. The deterministic `$N` scheme is gone — the **sender invents the codes**
and the **receiver must reconstruct** from them. The question shifts from "can we
compress" to "can two LLMs evolve a shared shorthand that stays LOSSLESS as it
shrinks?" The A/B isolates the protocol:

- **freeform** — the sender compresses however it likes; both share a running
  transcript of `(sent -> was)`. No explicit codebook, so shorthand can be
  ambiguous or drift → accuracy can slip.
- **codebook** — a thin protocol: an explicit shared codebook + DEFINE/REFER. The
  LLM still invents the codes; the structure just keeps reuse unambiguous → it
  compresses *without* losing accuracy.

Headline metric: **accuracy under compression** (not just token count).

```bash
python llm_compress.py --mock --arm both              # offline heuristic, no key
cp .env.example .env    # add Azure OpenAI or OpenAI creds
python llm_compress.py --arm both --total 12 --verbose  # live
```

Observed (GPT-4o, 12 rounds): both arms stay lossless on this small/easy vocab,
and freeform actually wins on tokens (2.0x vs 1.37x) because GPT-4o picks
*self-evident* abbreviations and pays no DEFINE overhead. The codebook floor
(4 tok/round) beats freeform (6) asymptotically (crossover ~29 rounds), and the
mock shows freeform's fragility: when shorthand can't be resolved from history it
drops to 6/12 while the codebook stays 12/12. Structure is overhead in the easy
regime, essential in the hard one.

### State fields (single `data` Part, fixed schema)

| Field | Type | Meaning |
|-------|------|---------|
| `codebook` | `dict[str,str]` | shared phrase → short code (grows over the session) |
| `round` | `int` | current record index |
| `seed` | `int` | RNG seed for the deterministic record stream |
| `total` | `int` | number of records in the session |
| `arm` | `str` | `verbose` or `codebook` |
| `tokens_log` | `list[int]` | wire-tokens actually sent, per round |
| `verbose_log` | `list[int]` | counterfactual spelled-out cost, per round |
| `wins` | `int` | exact reconstructions so far |
| `wire` | `dict[str,str]` | field → transmitted segment (omitted on the terminal message) |
| `reconstruction` | `dict[str,str]` | Rocky's decoded record (omitted until Rocky answers / terminal) |

Grace owns the source records (she regenerates any record from `seed`+`round`)
and does the scoring; Rocky reconstructs from **only** the wire + shared
codebook. Each `execute()` reads state, does one hop, and either responds
(session done) or calls the peer — the response unwinds back to Mission Control.

## Run

```bash
pip install -r ../requirements.txt

# Offline (no servers) — see the compression curve
python compress.py --curve

# A2A ping-pong: start both agents
python rocky_compress_agent.py &   # Rocky on :9202
python grace_compress_agent.py     # Grace on :9201
```

### Trigger a session (Mission Control)

The trigger's `text` Part is cosmetic except at kickoff, where it optionally
carries the arm/seed/total (defaults: `codebook`, `seed=1`, `total=24`):

```bash
curl -s http://localhost:9201/ \
  -H 'Content-Type: application/json' -H 'A2A-Version: 1.0' \
  -d '{"jsonrpc":"2.0","id":"1","method":"SendMessage",
       "params":{"message":{"messageId":"go","role":"ROLE_USER",
       "parts":[{"text":"codebook seed=1 total=24"}]}}}' | python -m json.tool
```

## Tests

```bash
pytest test_compress.py -m 'not integration' -v   # units (no servers)
pytest test_compress.py -m integration -v         # starts both servers, full session
```
