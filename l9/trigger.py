"""Mission Control — kick off the emergence session and print the result.

Sends a stateless trigger (text only, no L9 DataPart) to Grace; the whole game
runs across the two A2A servers and the terminal result unwinds back here.

    python trigger.py
"""
from __future__ import annotations

import asyncio
from uuid import uuid4

from a2a.client import ClientConfig, create_client
from a2a.types import Message, Part, Role, SendMessageRequest

import signaling
from l9_envelope import from_a2a

GRACE_URL = "http://localhost:9101"


async def main() -> None:
    grace = await create_client(GRACE_URL, ClientConfig(streaming=False))
    req = SendMessageRequest(message=Message(
        message_id=uuid4().hex, role=Role.ROLE_USER, parts=[Part(text="start")]))

    async for ev in grace.send_message(req):
        if hasattr(ev, "message") and ev.message.ByteSize():
            text = next((p.text for p in ev.message.parts if p.WhichOneof("content") == "text"), "")
            print("MISSION CONTROL <==", text)
            l9 = from_a2a(ev.message)
            if l9:
                d = l9.data
                print(f"  protocol    : {l9.protocol}  type : {l9.type}")
                print(f"  alignment   : {signaling.alignment(d['lexicons']):.0%}")
                print(f"  GAR / SCR / W: {signaling.gar(d.get('history', []))} / "
                      f"{signaling.scr(d.get('history', []))} / {signaling.provenance_weight(d.get('history', []))}")
                for a, lex in d["lexicons"].items():
                    print(f"  {a:6}: {lex}")


if __name__ == "__main__":
    asyncio.run(main())
