"""Trigger — kick off the ELP emergence session via Agent Alpha.

Sends a stateless text trigger to Alpha on port 9401. The game runs across
both agents and the terminal result unwinds back here with metrics.

    python trigger.py
"""
from __future__ import annotations

import sys
import os
import asyncio
from uuid import uuid4

from a2a.client import ClientConfig, create_client
from a2a.types import Message, Part, Role, SendMessageRequest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "l9"))
import signaling
from l9_envelope import from_a2a

ALPHA_URL = "http://localhost:9401"


async def main() -> None:
    alpha = await create_client(ALPHA_URL, ClientConfig(streaming=False))
    req = SendMessageRequest(message=Message(
        message_id=uuid4().hex, role=Role.ROLE_USER, parts=[Part(text="start")]))

    async for ev in alpha.send_message(req):
        if hasattr(ev, "message") and ev.message.ByteSize():
            text = next((p.text for p in ev.message.parts if p.WhichOneof("content") == "text"), "")
            print("RESULT <==", text)
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
