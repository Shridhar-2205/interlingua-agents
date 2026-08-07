"""Mission Control — kick off a warehouse session and print what came back.

    python floor_agent.py &
    python office_agent.py &
    python trigger.py                       # honest floor, 60 orders
    python trigger.py honest=false          # the yes-man arm
    python trigger.py orders=200 seed=11
"""
from __future__ import annotations

import asyncio
import os
import sys
from uuid import uuid4

import httpx
from a2a.client import ClientConfig, create_client
from a2a.types import Message, Part, Role, SendMessageRequest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.append(os.path.join(_HERE, "..", "l9"))

from wire import PORTS              # noqa: E402
from l9_envelope import from_a2a    # noqa: E402


async def main() -> None:
    cfg = " ".join(sys.argv[1:]) or "orders=60 seed=3 honest=true"
    hc = httpx.AsyncClient(timeout=600)
    office = await create_client(f"http://localhost:{PORTS['office']}",
                                 ClientConfig(streaming=False, httpx_client=hc))

    print(f"MISSION CONTROL ==> {cfg}")
    req = SendMessageRequest(message=Message(
        message_id=uuid4().hex, role=Role.ROLE_USER, parts=[Part(text=cfg)]))

    async for ev in office.send_message(req):
        if not (hasattr(ev, "message") and ev.message.ByteSize()):
            continue
        text = next((p.text for p in ev.message.parts
                     if p.WhichOneof("content") == "text"), "")
        print(f"MISSION CONTROL <== {text}\n")
        env = from_a2a(ev.message)
        if env is None:
            continue
        d = env.data
        print(f"  right / WRONG / asked-for-help : "
              f"{int(d['right'])} / {int(d['wrong'])} / {int(d['refused'])}")
        print(f"  GAR {d['gar']}   SCR {d['scr']}   W {d['provenance_weight']}")

        if d.get("wrong_deliveries"):
            print("\n  WRONG DELIVERIES")
            for w in d["wrong_deliveries"]:
                print(f"    ordered {w['ordered']:<14} sent {w['sent']}")

        meant, gloss = d.get("office_meant", {}), d.get("glossary", {})
        print("\n  THE GLOSSARY THEY BUILT")
        print(f"    {'sign':<5} {'Office meant':<14} {'Floor reads it as':<22} status")
        for sym, reading in sorted(gloss.items(), key=lambda kv: kv[1]):
            mine = meant.get(sym, "?")
            tag = "agreed" if mine == reading else "DRIFTED — check this"
            print(f"    {sym:<5} {mine:<14} {reading:<22} {tag}")

        never = sorted(f for s, f in meant.items() if s not in gloss)
        if never:
            print(f"\n    Never understood by the Floor: {', '.join(never)}")
        for group in d.get("unresolvable", []):
            print(f"\n    COULD NOT BE AGREED: {' / '.join(group)}")
            print("      identical from the aisle — needs a printed label")

    await hc.aclose()


if __name__ == "__main__":
    asyncio.run(main())
