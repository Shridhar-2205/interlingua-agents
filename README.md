# Interlingua — A2A Agents (Theory of Mind)

Inspired by the movie *Project Hail Mary*: an astronaut (Grace) and an alien (Rocky) build a shared language from scratch using A2A protocol. No shared memory — just two beings passing symbols back and forth until they understand each other.

## Algorithm

**Lewis Signaling Game** (from David Lewis, *Convention*, 1969):

1. **Sender** observes a meaning (a state of the world the Receiver can't see)
2. **Sender** picks an arbitrary signal (a symbol with no inherent meaning)
3. **Receiver** sees the signal and guesses which state the world is in
4. Both succeed only if the Receiver's guess matches reality

No pre-existing language. The signals are arbitrary. But if both players want to coordinate, they converge on a stable mapping — each meaning gets a unique signal. Lewis called this a **signaling convention**: self-reinforcing because neither player benefits from deviating once established.

### Theory of Mind Enhancement

Each agent models what the other believes and predicts whether a proposal will be accepted before sending it:

| Feature | What it does | Why it helps |
|---------|-------------|-------------|
| **Predict acceptance** | Before proposing, estimate if peer will accept | Avoids wasted rounds on doomed proposals |
| **Smart coining** | Avoid symbols rejected before or already in peer's lexicon | Reduces conflicts |
| **History tracking** | Past proposals + outcomes travel in metadata | Agents never repeat failed attempts |
| **Cooperative acceptance** | Accept by default, reject only established conflicts | Faster convergence |

### Implementation (`signaling.py`)

Five primitives power the negotiation:

| Primitive | What it does |
|-----------|-------------|
| `coin_smart(mine, theirs, history)` | Pick a symbol avoiding conflicts AND past rejections |
| `predict_acceptance(meaning, symbol, peer_lex, history)` | Score 0.0–1.0 for likelihood peer accepts |
| `propose_with_tom(mine, theirs, history)` | Pick the proposal with highest predicted acceptance |
| `decide_accept(my_lex, meaning, symbol, peer_lex, history)` | Accept unless conflicts with an established mapping |
| `record_outcome(history, referent, symbol, accepted, speaker)` | Append outcome to history (returns new list) |

The loop:

1. Speaker finds all unresolved meanings (where agents disagree)
2. For each, **predict** whether peer will accept
3. Pick the meaning+symbol with highest acceptance score
4. Listener **decides** accept/reject using its own knowledge
5. **Record** outcome in history (travels in metadata)
6. Measure alignment — if 1.0, stop; otherwise next round

References:
- Lewis, *Convention* (1969) — https://plato.stanford.edu/entries/convention/
- Havrylov & Titov (NIPS 2017) — https://arxiv.org/abs/1705.11192

## Data Storage

No in-memory state. Both agents are fully stateless — zero instance variables, no database, no files. The A2A message metadata **is** the memory. Every message carries the full game state:

```
grace_lex   →  Grace's full dictionary       (e.g. {"fire": "✦", "river": "≈", ...})
rocky_lex   →  Rocky's full dictionary       (e.g. {"fire": "○", "river": "△", ...})
round       →  how many rounds have passed   (e.g. 7)
history     →  list of past proposals+outcomes
referent    →  concept being discussed       (e.g. "river")
message     →  symbol being proposed         (e.g. "≈")
```

Each agent reads state from the incoming message, does one step, and writes updated state into the outgoing message. When the function returns, all local variables are gone — the only surviving copy of the game state is the message that was just sent.

### History Format

History is a list of past outcomes carried in metadata:

```json
[
  {"referent": "river", "symbol": "≈", "accepted": true, "speaker": "grace"},
  {"referent": "fire", "symbol": "✦", "accepted": false, "speaker": "rocky"},
  {"referent": "river", "symbol": "△", "accepted": true, "speaker": "rocky"}
]
```

Agents use this to avoid repeating rejected proposals and to determine which mappings are established.

## A2A Ping-Pong Flow

```
Mission Control (curl) ──trigger──▶ Grace (:9101)
                                      │
                                      ▼  init random lexicons
                                      ▼  propose_with_tom() → best candidate
                                      │
                                    Rocky (:9102)
                                      │
                                      ▼  decide_accept() → accept/reject
                                      ▼  record_outcome() → append to history
                                      ▼  propose_with_tom() → best candidate
                                      │
                                    Grace (:9101)
                                      │
                                      ▼  decide_accept() → accept/reject
                                      ▼  record_outcome() → append to history
                                      ▼  propose_with_tom() → best candidate
                                      │
                                    Rocky (:9102)
                                      │
                                     ...
                                      │
                                      ▼  alignment == 1.0 → stop
                                      │
Mission Control ◀──final result────────┘
```

Each round: one meaning proposed (the one with highest predicted acceptance).
History grows with each round — agents learn from past failures.

- **Mission Control → Grace**: one trigger, no game state (just `{"text": "start"}`)
- **Grace ↔ Rocky**: each round sends one proposal + full history in metadata
- **Stop**: whichever agent sees `alignment == 1.0` or `round >= 60` responds instead of calling the other

Both agents are server AND client. No external loop driver needed.

### Metadata Fields

| Field | Meaning |
|-------|---------|
| `context.grace_lex` | Grace's lexicon |
| `context.rocky_lex` | Rocky's lexicon |
| `context.round` | Current round number |
| `context.history` | List of past proposal outcomes |
| `message` | The symbol being proposed |
| `referent` | The concept being discussed this round |

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
          "grace_lex": {"fire": "✦", "river": "≈", "moon": "○"},
          "rocky_lex": {"fire": "○", "river": "△", "moon": "✦"},
          "round": 3,
          "history": [
            {"referent": "apple", "symbol": "✦", "accepted": true, "speaker": "grace"}
          ]
        },
        "https://example.com/ext/emergent-lang/v1/message": "≈",
        "https://example.com/ext/emergent-lang/v1/referent": "river"
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
req.metadata.update({CONTEXT: {...}, MESSAGE: sym, REFERENT: referent})

async for ev in rocky.send_message(req):
    # ev.message — the A2A response
```

### Message Passing

Game state + history travels in A2A extension metadata on every message:

```python
# Outgoing (client writes)
req.metadata.update({
    "https://example.com/ext/emergent-lang/v1/context": {
        "grace_lex": {...}, "rocky_lex": {...}, "round": 3,
        "history": [{"referent": "apple", "symbol": "✦", "accepted": True, "speaker": "grace"}]
    },
    "https://example.com/ext/emergent-lang/v1/message": "≈",
    "https://example.com/ext/emergent-lang/v1/referent": "river",
})

# Incoming (server reads)
md = context.metadata or {}
ctx = md.get(CONTEXT) or {}
grace_lex = ctx.get("grace_lex", {})
history = ctx.get("history", [])
signal = md.get(MESSAGE)
referent = md.get(REFERENT)
```

No shared memory, no database — just A2A messages carrying state + history back and forth over HTTP.

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

# Integration test (starts both servers, triggers full game, asserts 100% convergence)
pytest test_agents.py -m integration -v
```

## Files

```
signaling.py      — Game logic (ToM: predict, propose, decide, record) — 10 meanings
grace_agent.py    — Stateless ping-pong agent + A2A server/client (Grace)
rocky_agent.py    — Stateless ping-pong agent + A2A server/client (Rocky)
test_agents.py    — Unit + integration tests (33 unit + 1 integration)
requirements.txt  — Dependencies
```
