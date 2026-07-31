"""Drive a full session and log every A2A message exchanged, in order.

Builds the exact same wire-format A2A messages the live transport (a2a_agent.py)
sends — same build_l9/to_data_part/_message helpers — but drives the hops
in-process (like run.py) so the whole episode can be captured without needing
two live servers.

Writes two files per run:
  runs/<label>.json   machine-readable: every message's full A2A wire JSON, in order
  runs/<label>.log    human-readable: one annotated block per message

Usage:
    python log_run.py --label genuine_no_llm      # deterministic (unset OPENAI_API_KEY first)
    python log_run.py --label genuine_with_llm    # LLM ToM (l9/.env creds)
    python log_run.py --label mimic_no_llm --mimic
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from uuid import uuid4

from google.protobuf.json_format import MessageToDict
from a2a.types import Message, Part, Role

import agent
import intelligence
import lens as lens_mod
import signaling
from a2a_agent import _message
from l9_envelope import EXT_URI, build_l9, episode_urn, to_data_part
from l9_models import Kind

RUNS_DIR = Path(__file__).with_name("runs")


def _wire(msg) -> dict:
    return MessageToDict(msg, preserving_proto_field_name=True)


def drive_and_log(agents: list[str], mimic: bool, max_hops: int = 200) -> list[dict]:
    """Run the episode; return one record per message actually placed on the wire."""
    if mimic:
        lens_mod.BY_ID["rocky"] = lens_mod.ROCKY_COMPLIANT

    episode = episode_urn("session", "loggedRUN")
    records: list[dict] = []

    # 0. Synthetic "intent" — the episode opens with each agent's independently
    #    formed prior (local, no LLM — see agent.form_prior). Not a real network
    #    hop (priors are formed locally before any message is sent), but recorded
    #    here so the log shows the starting point the negotiation measures from.
    state = agent.initial_state(agents)
    intent = build_l9(kind=Kind.intent, sender=agents[0], recipients=agents[1:],
                      episode=episode, data=state, subprotocol="CIP")
    intent_msg = Message(
        message_id=uuid4().hex, role=Role.ROLE_USER,
        parts=[Part(text=f"session opens | priors formed independently for {agents}"),
               to_data_part(intent)],
        extensions=[EXT_URI],
    )
    records.append({
        "hop": 0, "kind": "intent", "sender": agents[0], "receiver": agents[1:],
        "note": "priors formed locally (no LLM) — independent starting lexicons",
        "wire_message": _wire(intent_msg),
    })

    turn = 0
    while state.get("decision") != "converged" and turn < max_hops:
        me = agents[turn % len(agents)]
        peer = agents[(turn + 1) % len(agents)]
        nxt = agent.step(state, me)

        if nxt.get("decision") == "converged":
            l9 = build_l9(kind=Kind.commit, subkind="converged", sender=me,
                          recipients=[peer], episode=episode, data=nxt, subprotocol="CIP")
            h = nxt.get("history", [])
            note = (f"CONVERGED | round {nxt['round']} | align {signaling.alignment(nxt['lexicons']):.0%} "
                    f"| GAR {signaling.gar(h)} SCR {signaling.scr(h)} W {signaling.provenance_weight(h)}")
        else:
            l9 = build_l9(kind=Kind.exchange, sender=me, recipients=[peer], episode=episode,
                          data=nxt, topic=f"concept:{nxt['referent']}", subprotocol="CIP")
            note = f"{me}: proposes '{nxt['proposal']}' for '{nxt['referent']}' -> {peer}"

        records.append({
            "hop": turn + 1, "kind": str(l9.header.kind.value) + (f":{l9.header.subkind}" if l9.header.subkind else ""),
            "sender": me, "receiver": peer, "note": note,
            "wire_message": _wire(_message(l9, Role.ROLE_USER if nxt.get("decision") != "converged" else Role.ROLE_AGENT)),
        })

        state = nxt
        turn += 1
        if nxt.get("decision") == "converged":
            break

    return records


def write_log(records: list[dict], label: str) -> None:
    RUNS_DIR.mkdir(exist_ok=True)
    json_path = RUNS_DIR / f"{label}.json"
    log_path = RUNS_DIR / f"{label}.log"

    json_path.write_text(json.dumps({"label": label, "messages": records}, indent=2, ensure_ascii=False))

    lines = [f"===== RUN: {label}  ({len(records)} messages) =====", ""]
    for r in records:
        lines.append(f"--- hop {r['hop']:>3}  [{r['kind']}]  {r['sender']} -> {r['receiver']} ---")
        lines.append(f"  {r['note']}")
        lines.append(json.dumps(r["wire_message"], indent=2, ensure_ascii=False))
        lines.append("")
    log_path.write_text("\n".join(lines))

    print(f"wrote {json_path}  ({json_path.stat().st_size} bytes)")
    print(f"wrote {log_path}  ({log_path.stat().st_size} bytes)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True)
    ap.add_argument("--mimic", action="store_true")
    args = ap.parse_args()

    print(f"LLM available: {intelligence.available()}  (label={args.label})", file=sys.stderr)
    records = drive_and_log(["grace", "rocky"], mimic=args.mimic)
    write_log(records, args.label)


if __name__ == "__main__":
    main()
