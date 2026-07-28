# Interlingua — A2A Agents (Smart Convergence)

Inspired by the movie *Project Hail Mary*: an astronaut (Grace) and an alien (Rocky) build a shared language from scratch using A2A protocol. No shared memory — just two beings passing symbols back and forth until they understand each other.

## Algorithm

**Lewis Signaling Game** (from David Lewis, *Convention*, 1969):

1. **Sender** observes a meaning (a state of the world the Receiver can't see)
2. **Sender** picks an arbitrary signal (a symbol with no inherent meaning)
3. **Receiver** sees the signal and guesses which state the world is in
4. Both succeed only if the Receiver's guess matches reality

No pre-existing language. The signals are arbitrary. But if both players want to coordinate, they converge on a stable mapping — each meaning gets a unique signal. Lewis called this a **signaling convention**: self-reinforcing because neither player benefits from deviating once established.

### Smart Convergence Enhancement

This branch adds three optimizations that reduce convergence from ~10-20 rounds to 1-5 rounds:

| Feature | What it does | Why it helps |
|---------|-------------|-------------|
| **Mutual exclusivity** | `coin_exclusive()` never picks a symbol already mapped in either lexicon | Eliminates collisions that waste rounds |
| **Batch proposals** | Propose ALL disagreements in one round instead of one-at-a-time | Resolves 10 meanings in 1-3 rounds, not 10-20 |
| **Confidence scores** | Each mapping has a confidence (0.5–1.0); lower yields to higher | Prevents flip-flopping; established mappings are stable |

### Implementation (`signaling.py`)

| Primitive | What it does |
|-----------|-------------|
| `coin_exclusive(mine, theirs)` | Pick a symbol free in BOTH lexicons (one-to-one guarantee) |
| `propose_batch(mine, theirs)` | Generate proposals for all unresolved meanings at once |
| `resolve_batch(my_lex, proposals)` | Process incoming batch — confidence determines who yields |
| `get_symbol(lex, meaning)` | Extract symbol from lexicon entry (handles both formats) |
| `get_confidence(lex, meaning)` | Extract confidence from lexicon entry |

Confidence levels:
- `COINED = 0.5` — freshly invented, arbitrary
- `ADOPTED = 0.7` — accepted from peer, socially validated
- `AGREED = 1.0` — both agents have same mapping, settled

The loop:

1. Speaker generates **batch proposals** for all disagreements
2. Listener runs `resolve_batch` — for each proposal, compare confidence:
   - Their confidence >= mine → adopt (yield)
   - Their confidence < mine → reject (keep mine)
3. Listener proposes back with their own batch
4. Measure alignment — if 1.0, stop; otherwise next round

Converges in **1-5 rounds** for 10 meanings (vs. 10-20 without batching).

References:
- Lewis, *Convention* (1969) — https://plato.stanford.edu/entries/convention/
- Havrylov & Titov (NIPS 2017) — https://arxiv.org/abs/1705.11192

## Data Storage

No in-memory state. Both agents are fully stateless — zero instance variables, no database, no files. The A2A message metadata **is** the memory. Every message carries the full game state:

```
grace_lex   →  Grace's full dictionary with confidence
              (e.g. {"fire": {"symbol": "✦", "confidence": 0.7}, ...})
rocky_lex   →  Rocky's full dictionary with confidence
round       →  how many rounds have passed
proposals   →  batch of proposals being sent
              (e.g. [{"referent": "river", "symbol": "≈", "confidence": 0.5}, ...])
```

Lexicon format (with confidence):
```json
{
  "fire": {"symbol": "✦", "confidence": 0.7},
  "river": {"symbol": "≈", "confidence": 0.5},
  "moon": {"symbol": "○", "confidence": 1.0}
}
```

Each agent reads state from the incoming message, does one step, and writes updated state into the outgoing message. When the function returns, all local variables are gone — the only surviving copy of the game state is the message that was just sent.

## A2A Ping-Pong Flow

```
Mission Control (curl) ──trigger──▶ Grace (:9101)
                                      │
                                      ▼  init random lexicons (conf=0.5)
                                      ▼  propose_batch() → all 10 meanings
                                      │
                                    Rocky (:9102)
                                      │
                                      ▼  resolve_batch() — adopt if conf ≥ mine
                                      ▼  check alignment → not 1.0
                                      ▼  propose_batch() → remaining disagreements
                                      │
                                    Grace (:9101)
                                      │
                                      ▼  resolve_batch() — adopt if conf ≥ mine
                                      ▼  check alignment → 1.0 ✓ STOP
                                      │
Mission Control ◀──final result────────┘
```

Typical game: **1-3 rounds** (all 10 meanings batched per round).

- **Mission Control → Grace**: one trigger, no game state (just `{"text": "start"}`)
- **Grace ↔ Rocky**: each round sends ALL unresolved proposals at once with confidence scores
- **Stop**: whichever agent sees `alignment == 1.0` or `round >= 60` responds instead of calling the other

Both agents are server AND client. No external loop driver needed.

### Metadata Fields

| Field | Meaning |
|-------|---------|
| `context.grace_lex` | Grace's lexicon with confidence scores |
| `context.rocky_lex` | Rocky's lexicon with confidence scores |
| `context.round` | Current round number |
| `proposals` | Batch of proposals: `[{referent, symbol, confidence}, ...]` |

### Full A2A Message (Grace → Rocky)

```json
{
  "jsonrpc": "2.0",
  "id": "a3f1",
  "method": "SendMessage",
  "params": {
    "message": {
      "messageId": "7c9e2b...",
      "role": "ROLE_USER",
      "parts": [{"text": "signal"}],
      "extensions": ["https://example.com/ext/emergent-lang/v1"],
      "metadata": {
        "https://example.com/ext/emergent-lang/v1/context": {
          "grace_lex": {
            "fire": {"symbol": "✦", "confidence": 0.5},
            "river": {"symbol": "≈", "confidence": 0.5},
            "moon": {"symbol": "○", "confidence": 0.5}
          },
          "rocky_lex": {
            "fire": {"symbol": "△", "confidence": 0.5},
            "river": {"symbol": "▽", "confidence": 0.5},
            "moon": {"symbol": "◆", "confidence": 0.5}
          },
          "round": 1
        },
        "https://example.com/ext/emergent-lang/v1/proposals": [
          {"referent": "fire", "symbol": "✦", "confidence": 0.5},
          {"referent": "river", "symbol": "≈", "confidence": 0.5},
          {"referent": "moon", "symbol": "○", "confidence": 0.5}
        ]
      }
    }
  }
}
```

## A2A over HTTP

Both agents use `a2a-sdk==1.1.2`. Each agent is both **server** and **client**.

### Server (receives A2A messages)

```python
routes = create_agent_card_routes(card) + create_jsonrpc_routes(handler, rpc_url="/")
app = Starlette(routes=routes)
uvicorn.run(app, host="localhost", port=9101)
```

- `GET /.well-known/agent.json` — Agent Card (discovery)
- `POST /` — JSON-RPC endpoint (receives `SendMessage`)

### Client (sends A2A messages)

```python
rocky = await create_client("http://localhost:9102", ClientConfig(streaming=False))
req = SendMessageRequest(message=Message(..., extensions=[EXT]))
req.metadata.update({CONTEXT: {...}, PROPOSALS: [...]})

async for ev in rocky.send_message(req):
    # ev.message — the A2A response
```

### Message Passing

Game state + batch proposals travel in A2A extension metadata:

```python
# Outgoing (client writes)
req.metadata.update({
    "https://example.com/ext/emergent-lang/v1/context": {
        "grace_lex": {...}, "rocky_lex": {...}, "round": 1
    },
    "https://example.com/ext/emergent-lang/v1/proposals": [
        {"referent": "fire", "symbol": "✦", "confidence": 0.5},
        {"referent": "river", "symbol": "≈", "confidence": 0.5},
    ],
})

# Incoming (server reads)
md = context.metadata or {}
ctx = md.get(CONTEXT) or {}
grace_lex = ctx.get("grace_lex", {})
proposals = md.get(PROPOSALS, [])
```

No shared memory, no database — just A2A messages carrying state + proposals back and forth over HTTP.

## Run

```bash
pip install -r requirements.txt

# Start both agents (separate terminals)
python rocky_agent.py    # terminal 1 — Rocky on :9102
python grace_agent.py    # terminal 2 — Grace on :9101
```

### Trigger the game (Mission Control)

```bash
curl -s http://localhost:9101/ \
  -H 'Content-Type: application/json' \
  -H 'A2A-Version: 1.0' \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "SendMessage",
    "params": {
      "message": {
        "messageId": "go",
        "role": "ROLE_USER",
        "parts": [{"text": "start"}]
      }
    }
  }' | python -m json.tool
```

### Verify agent cards

```bash
curl -s http://localhost:9101/.well-known/agent.json | python -m json.tool
curl -s http://localhost:9102/.well-known/agent.json | python -m json.tool
```

## Tests

```bash
# Unit tests (no servers needed)
pytest test_agents.py -m 'not integration' -v

# Integration test (starts both servers, asserts convergence in <= 5 rounds)
pytest test_agents.py -m integration -v
```

## Files

```
signaling.py      — Game logic (coin_exclusive, propose_batch, resolve_batch) — 10 meanings
grace_agent.py    — Stateless ping-pong agent + A2A server/client (Grace)
rocky_agent.py    — Stateless ping-pong agent + A2A server/client (Rocky)
test_agents.py    — Unit + integration tests (40 unit + 2 integration)
requirements.txt  — Dependencies
```
