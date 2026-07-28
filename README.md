# Interlingua — A2A Agents

Inspired by the movie *Project Hail Mary*: an astronaut (Grace) and an alien (Rocky) build a shared language from scratch using A2A protocol. No shared memory — just two beings passing symbols back and forth until they understand each other.

## Algorithm

**Lewis Signaling Game** (from David Lewis, *Convention*, 1969):

1. **Sender** observes a meaning (a state of the world the Receiver can't see)
2. **Sender** picks an arbitrary signal (a symbol with no inherent meaning)
3. **Receiver** sees the signal and guesses which state the world is in
4. Both succeed only if the Receiver's guess matches reality

No pre-existing language. The signals are arbitrary. But if both players want to coordinate, they converge on a stable mapping — each meaning gets a unique signal. Lewis called this a **signaling convention**: self-reinforcing because neither player benefits from deviating once established.

Nobody sat down and decided "✦ means fire." It emerged from repeated successful coordination. Any consistent mapping works equally well — the one that sticks is arbitrary but stable.

That's what Grace and Rocky do here: Grace proposes symbols for concepts, Rocky adopts them, rounds repeat until they share a dictionary neither designed but both follow.

Our implementation targets disagreements first and exits early once fully aligned.

### Implementation (`signaling.py`)

Three primitives power the entire negotiation:

| Primitive | What it does | Role in the game |
|-----------|-------------|------------------|
| `coin(mine, theirs)` | Pick a random symbol not yet used by either agent | **Innovation** — introduce a novel sign into the channel |
| `adopt(lex, meaning, symbol)` | Accept the speaker's symbol for a meaning; remove any conflicting mappings | **Alignment** — convention spreads by imitation |
| `alignment(a, b)` | Fraction of meanings where both agents agree on the same symbol | **Convergence check** — 1.0 means a fully shared language |

The loop:

1. Speaker picks a meaning that the two agents disagree on
2. Speaker **coins** a symbol (or reuses one it already has)
3. Listener **adopts** that symbol — overwrites its own mapping
4. Measure **alignment** — if 1.0, stop; otherwise next round

There is no reward signal, no gradient, no central dictionary. The language emerges purely from use and imitation — exactly the dynamic Lewis described in 1969.

References:
- Lewis, *Convention* (1969) — https://plato.stanford.edu/entries/convention/
- Havrylov & Titov (NIPS 2017) — https://arxiv.org/abs/1705.11192

## Data Storage

No in-memory state. Both agents are fully stateless — zero instance variables, no database, no files. The A2A message metadata **is** the memory. Every message carries the full game state:

```
grace_lex   →  Grace's full dictionary       (e.g. {"fire": "✦", "river": "≈", ...})
rocky_lex   →  Rocky's full dictionary       (e.g. {"fire": "○", "river": "△", ...})
round       →  how many rounds have passed   (e.g. 7)
referent    →  concept being discussed       (e.g. "river")
message     →  symbol being proposed         (e.g. "≈")
```

Each agent reads state from the incoming message, does one step, and writes updated state into the outgoing message. When the function returns, all local variables are gone — the only surviving copy of the game state is the message that was just sent.

Kill either agent mid-game, restart it, and the next call still works — because everything the agent needs is in that call's metadata.

## A2A Ping-Pong Flow

```
Mission Control (curl) ──trigger──▶ Grace (:9101)
                                      │
                                      ▼  coin symbol, send state
                                    Rocky (:9102)
                                      │
                                      ▼  adopt, coin, send state
                                    Grace (:9101)
                                      │
                                      ▼  adopt, coin, send state
                                    Rocky (:9102)
                                      │
                                     ...
                                      │
                                      ▼  alignment == 1.0 → stop
                                    (response unwinds back)
                                      │
Mission Control ◀──final result────────┘
```

- **Mission Control → Grace**: one trigger, no game state (just `{"text": "start"}`)
- **Grace ↔ Rocky**: agents call each other back and forth, each passing the full game state in metadata
- **Stop**: whichever agent sees `alignment == 1.0` or `round >= 60` just responds instead of calling the other — the response chain unwinds back to Mission Control

Both agents are server AND client. No external loop driver needed.

### Metadata Fields

| Field | Meaning |
|-------|---------|
| `context.grace_lex` | Grace's lexicon (e.g. `{"fire": "✦", "river": "≈"}`) |
| `context.rocky_lex` | Rocky's lexicon |
| `context.round` | Current round number |
| `context.referent` | The concept being discussed this round |
| `message` | The symbol being proposed |

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
          "referent": "river"
        },
        "https://example.com/ext/emergent-lang/v1/message": "≈"
      }
    }
  }
}
```

### Stop Response (from whichever agent converges)

```json
{
  "message": {
    "messageId": "b4a8d1...",
    "role": "ROLE_AGENT",
    "parts": [{"text": "done | rounds: 10 | alignment: 100% | grace: {...} | rocky: {...}"}],
    "extensions": ["https://example.com/ext/emergent-lang/v1"],
    "metadata": {
      "https://example.com/ext/emergent-lang/v1/context": {
        "grace_lex": {"fire": "✦", "river": "≈", ...},
        "rocky_lex": {"fire": "✦", "river": "≈", ...},
        "round": 10
      }
    }
  }
}
```

## Convergence

10 meanings, both agents adopt unconditionally. Each round resolves one disagreement. Converges in ~10-20 rounds (depending on randomized initial conflict). Max 60 rounds before giving up.

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
req.metadata.update({CONTEXT: {...}, MESSAGE: sym})

async for ev in rocky.send_message(req):
    # ev.message — the A2A response (parts, metadata, extensions)
```

`create_client(url)` discovers the agent card, then sends `SendMessage` as JSON-RPC POST.

### Message Passing

Game state travels in A2A extension metadata on every message:

```python
# Outgoing (client writes)
req.metadata.update({
    "https://example.com/ext/emergent-lang/v1/context": {
        "grace_lex": {...}, "rocky_lex": {...}, "round": 3, "referent": "river"
    },
    "https://example.com/ext/emergent-lang/v1/message": "≈",
})

# Incoming (server reads)
md = context.metadata or {}
ctx = md.get(CONTEXT) or {}
grace_lex = ctx.get("grace_lex", {})
signal = md.get(MESSAGE)
```

No shared memory, no database — just A2A messages carrying state back and forth over HTTP.

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

### Expected response

```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "result": {
    "message": {
      "parts": [
        {"text": "done | rounds: 12 | alignment: 100% | grace: {'apple': '✦', 'dance': '≈', ...} | rocky: {'apple': '✦', 'dance': '≈', ...}"}
      ],
      "metadata": {
        "https://example.com/ext/emergent-lang/v1/context": {
          "grace_lex": {"apple": "✦", "dance": "≈", "river": "△", "sea": "▽", "moon": "◆", "fire": "∿", "star": "☆", "wind": "⬡", "stone": "♁", "tree": "∆"},
          "rocky_lex": {"apple": "✦", "dance": "≈", "river": "△", "sea": "▽", "moon": "◆", "fire": "∿", "star": "☆", "wind": "⬡", "stone": "♁", "tree": "∆"},
          "round": 12
        }
      }
    }
  }
}
```

Both lexicons are identical — all 10 meanings converged. The symbols are random each run but always match between agents.

### Verify agent cards

```bash
# Grace's identity
curl -s http://localhost:9101/.well-known/agent.json | python -m json.tool

# Rocky's identity
curl -s http://localhost:9102/.well-known/agent.json | python -m json.tool
```

## Tests

```bash
# Unit tests (no servers needed — mocks the A2A calls)
pytest test_agents.py -m 'not integration' -v

# Integration test (starts both servers, triggers full game, asserts 100% convergence)
pytest test_agents.py -m integration -v
```

## Files

```
signaling.py      — Game logic (coin, adopt, alignment) — 10 meanings
grace_agent.py    — Stateless ping-pong agent + A2A server/client (Grace)
rocky_agent.py    — Stateless ping-pong agent + A2A server/client (Rocky)
test_agents.py    — Unit + integration tests
requirements.txt  — Dependencies
```