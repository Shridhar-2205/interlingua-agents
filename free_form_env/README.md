# Free Form Environment — First Contact

Two A2A agents (Human + Alien) in a shared environment of 40 physical objects.
They communicate over HTTP using the [A2A protocol](https://github.com/google/A2A),
each powered by an LLM with a persona system prompt. They talk freely — no fixed
rounds, no external judge — until the human believes they've agreed on 10 word mappings.

## How it works

- **Human Agent** (port 9201): Speaks English. Points at objects, names them, tries to
  learn alien words through repetition and gestures.
- **Alien Agent** (port 9202): Speaks Zyphorian (invented language). Cannot understand
  English. Responds with its own consistent alien words while mimicking human sounds.

Both agents are A2A client + server. The human is triggered externally, then drives
a ping-pong loop: it sends a message to the alien via A2A, gets a reply, generates
its next response via LLM, and repeats. The loop ends when the human is confident
it has identified 10 English↔Alien word mappings.

## The shared environment

40 fixed objects both agents can see, point at, pick up, and gesture about:

```
fire, water, rock, tree, sun, moon, sky, cloud, rain, wind,
flower, fruit, seed, leaf, root, fish, bird, snake, insect, egg,
hand, eye, mouth, foot, head, cave, river, mountain, sand, mud,
bone, stick, shell, feather, fur, smoke, ice, lightning, shadow, star
```

The human knows them by English names. The alien perceives them by description
(e.g. "the hot bright dancing thing" for fire) and invents its own Zyphorian words.

## Results

In our test run, the agents aligned on **10 mappings in 14 exchanges**:

| English | Alien |
|---------|-------|
| fire | vrk |
| water | oosha |
| rock | felk |
| sun | draak-zul |
| tree | morra-plix |
| leaf | thiip |
| moon | qip-norra |
| stick | zrik |
| bird | tii-draak |
| mountain | felk-thaan |

The first few exchanges were gesture-heavy warmup (pointing, nodding, establishing
that nodding = agreement). Then they hit a stride of ~1 new word per exchange, with
a couple of social bonding rounds mixed in before the human declared completion.

## Setup

```bash
pip install a2a-sdk httpx uvicorn starlette
```

Copy the env file and fill in your API key:

```bash
cp .env.sample .env
# Edit .env with your real LLM_API_KEY
```

## Running

Terminal 1 — start the Alien agent:

```bash
cd free_form_env
export $(grep -v '^#' .env | xargs)
python alien_agent.py
```

Terminal 2 — start the Human agent:

```bash
cd free_form_env
export $(grep -v '^#' .env | xargs)
python human_agent.py
```

Terminal 3 — trigger the conversation:

```bash
curl -s -X POST http://localhost:9201/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "message/send",
    "params": {
      "message": {
        "messageId": "trigger-001",
        "role": "ROLE_USER",
        "parts": [{"text": "begin"}]
      }
    }
  }'
```

Or using the A2A SDK client:

```python
import asyncio
import httpx
from uuid import uuid4
from a2a.client import ClientConfig, create_client
from a2a.types import Message, Part, Role, SendMessageRequest

async def trigger():
    http_client = httpx.AsyncClient(timeout=600)
    client = await create_client(
        "http://localhost:9201",
        ClientConfig(streaming=False, httpx_client=http_client),
    )
    req = SendMessageRequest(
        message=Message(
            message_id=uuid4().hex,
            role=Role.ROLE_USER,
            parts=[Part(text="begin")],
        ),
    )
    async for ev in client.send_message(req):
        if hasattr(ev, "message") and ev.message.ByteSize():
            for p in ev.message.parts:
                if p.WhichOneof("content") == "text":
                    print(p.text)

asyncio.run(trigger())
```

Watch the human agent's terminal for the live conversation and final mappings.

## Architecture

```
┌─────────────────┐         A2A/HTTP          ┌─────────────────┐
│  Human Agent    │◄────────────────────────►  │  Alien Agent    │
│  :9201          │   SendMessage/response     │  :9202          │
│                 │                            │                 │
│  Persona: EN    │                            │  Persona: ZYP   │
│  LLM: inline    │                            │  LLM: inline    │
│  Drives loop    │                            │  Responds only  │
└─────────────────┘                            └─────────────────┘
        ▲
        │ trigger (curl / A2A client)
        │
   External caller
```

Both agents maintain their own conversation history for LLM context.
The alien's language stays consistent because its full history is passed
to the LLM on every turn. No shared state, no external coordination —
just two agents talking over HTTP until they converge.
