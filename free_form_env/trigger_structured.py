"""Mission Control for the depth-B structured agents — kick off, print the result."""
from __future__ import annotations

import asyncio
import os
import sys
from uuid import uuid4

import httpx
from a2a.client import ClientConfig, create_client
from a2a.types import Message, Part, Role, SendMessageRequest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "l9"))
import signaling
from l9_envelope import from_a2a
from emergence_structured import OBJECTS


async def main() -> None:
    hc = httpx.AsyncClient(timeout=120)
    human = await create_client("http://localhost:9201", ClientConfig(streaming=False, httpx_client=hc))
    req = SendMessageRequest(message=Message(
        message_id=uuid4().hex, role=Role.ROLE_USER, parts=[Part(text="begin")]))
    async for ev in human.send_message(req):
        if hasattr(ev, "message") and ev.message.ByteSize():
            text = next((p.text for p in ev.message.parts if p.WhichOneof("content") == "text"), "")
            print("MISSION CONTROL <==", text)
            l9 = from_a2a(ev.message)
            if l9:
                d = l9.payload.data
                print(f"  alignment : {signaling.alignment(d['lexicons'], OBJECTS):.0%} on {len(OBJECTS)} objects")
                print(f"  GAR / SCR : {signaling.gar(d.get('history', []))} / {signaling.scr(d.get('history', []))}")
                print(f"  shared vocab: {d['lexicons']['human']}")


if __name__ == "__main__":
    asyncio.run(main())
