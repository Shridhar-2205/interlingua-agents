"""Grace — stateless A2A speaker/scorer for the Mission Log Relay.

No state is stored in memory. The whole session (shared codebook, round, seed,
arm, token logs, wins, the current wire, and Rocky's reconstruction) travels in
a structured JSON `data` Part (see compress_state.py). Each execute() reads
state, does ONE hop, and either responds (session done) or calls the peer with
updated state — same stateless ping-pong / unwind pattern as the Lewis demo.

Grace owns the source records (she can regenerate any record deterministically
from seed+round) and therefore does the scoring. Rocky only decodes the wire.

Flow per round:
    Grace.transmit(r)  -> build wire (DEFINE/REFER), call Rocky
    Rocky.decode       -> reconstruct from wire+codebook, call Grace back
    Grace.score(r)     -> compare to truth, advance; done? respond : transmit(r+1)
"""
from __future__ import annotations

from uuid import uuid4

import uvicorn
from starlette.applications import Starlette
from typing_extensions import override

from a2a.client import ClientConfig, create_client
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes.agent_card_routes import create_agent_card_routes
from a2a.server.routes.jsonrpc_routes import create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities, AgentCard, AgentExtension, AgentSkill,
    Message, Part, Role, SendMessageRequest,
)
from a2a.types.a2a_pb2 import AgentInterface

from compress_state import CompressionState, decode, encode
from compress import (
    FIELDS, encode_codebook, encode_verbose, make_record, tokens, verbose_tokens,
)

EXT = "https://example.com/ext/emergent-compress/v1"
ROCKY_URL = "http://localhost:9202"   # Rocky's A2A endpoint
DEFAULT_TOTAL = 24
DEFAULT_SEED = 1


def parse_trigger(text: str) -> tuple[str, int, int]:
    """Trigger text is cosmetic except at kickoff: pull optional arm/seed/total."""
    arm, seed, total = "codebook", DEFAULT_SEED, DEFAULT_TOTAL
    for tok in (text or "").split():
        if tok in ("verbose", "codebook"):
            arm = tok
        elif tok.startswith("seed="):
            try:
                seed = int(tok[5:])
            except ValueError:
                pass
        elif tok.startswith("total="):
            try:
                total = int(tok[6:])
            except ValueError:
                pass
    return arm, seed, total


def _summary(cs: CompressionState) -> str:
    tl, vl = cs.tokens_log, cs.verbose_log
    k = max(1, cs.total // 4)
    first = sum(tl[:k]) / k if tl else 0.0
    last = sum(tl[-k:]) / k if tl else 0.0
    ratio = (sum(vl) / sum(tl)) if sum(tl) else 1.0
    return (f"done | arm: {cs.arm} | rounds: {cs.total} | "
            f"accuracy: {cs.wins}/{cs.total} | tokens: {sum(tl)} (vs verbose "
            f"{sum(vl)}) | ratio: {ratio:.2f}x | per-round first{k}avg {first:.1f} "
            f"-> last{k}avg {last:.1f}")


class GraceCompressExecutor(AgentExecutor):
    """Stateless executor — no instance variables, no stored state."""

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        state = decode(context.message)

        if state.total == 0:
            # Trigger from Mission Control (no data Part) — start a fresh session.
            text = next((p.text for p in context.message.parts
                         if p.WhichOneof("content") == "text"), "") if context.message else ""
            arm, seed, total = parse_trigger(text)
            cs = CompressionState(arm=arm, seed=seed, total=total, round=0)
            print(f"[Grace] session start | arm={arm} seed={seed} total={total}")
            await self._transmit_and_call(context, event_queue, cs)
            return

        # State arrived from Rocky carrying his reconstruction — score this round.
        truth = make_record(state.seed, state.round)
        win = state.reconstruction == truth
        state.wins += int(win)
        print(f"[Grace] round {state.round} | truth={truth} "
              f"| recon={state.reconstruction} | {'OK' if win else 'MISS'}")

        state.round += 1
        if state.round >= state.total:
            summary = _summary(state)
            print(f"[Grace] {summary}")
            reply = Message(
                message_id=uuid4().hex,
                context_id=context.context_id or "",
                task_id=context.task_id or "",
                role=Role.ROLE_AGENT,
                parts=[
                    Part(text=summary),
                    encode(CompressionState(
                        codebook=state.codebook, round=state.round, seed=state.seed,
                        total=state.total, arm=state.arm, tokens_log=state.tokens_log,
                        verbose_log=state.verbose_log, wins=state.wins,
                    )),
                ],
                extensions=[EXT],
            )
            await event_queue.enqueue_event(reply)
            return

        await self._transmit_and_call(context, event_queue, state)

    async def _transmit_and_call(self, context: RequestContext,
                                 event_queue: EventQueue, cs: CompressionState) -> None:
        """Build the wire for cs.round, log tokens, call Rocky, pass his reply back."""
        record = make_record(cs.seed, cs.round)
        if cs.arm == "codebook":
            wire, cs.codebook = encode_codebook(record, cs.codebook)
        else:
            wire = encode_verbose(record)
        cs.tokens_log = list(cs.tokens_log) + [tokens(wire)]
        cs.verbose_log = list(cs.verbose_log) + [verbose_tokens(record)]
        cs.wire = wire
        cs.reconstruction = None

        print(f"[Grace] round {cs.round} | transmit {wire} "
              f"| {tokens(wire)} tok (verbose {verbose_tokens(record)})")

        rocky = await create_client(ROCKY_URL, ClientConfig(streaming=False))
        req = SendMessageRequest(
            message=Message(
                message_id=uuid4().hex, role=Role.ROLE_USER,
                parts=[Part(text="input"), encode(cs)],
                extensions=[EXT],
            ),
        )
        result_text = ""
        result_state: CompressionState = CompressionState()
        async for ev in rocky.send_message(req):
            if hasattr(ev, "message") and ev.message.ByteSize():
                result_text = next(
                    (p.text for p in ev.message.parts if p.WhichOneof("content") == "text"), ""
                )
                result_state = decode(ev.message)

        reply = Message(
            message_id=uuid4().hex,
            context_id=context.context_id or "",
            task_id=context.task_id or "",
            role=Role.ROLE_AGENT,
            parts=[Part(text=result_text), encode(result_state)],
            extensions=[EXT],
        )
        await event_queue.enqueue_event(reply)

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("cancel not supported")


def build_agent_card(host: str = "localhost", port: int = 9201) -> AgentCard:
    """Agent Card — served at GET /.well-known/agent.json for A2A discovery."""
    ext = AgentExtension(uri=EXT, description="Session state via a structured data Part.",
                         required=False)
    ext.params.update({"keys": sorted(
        ["codebook", "round", "seed", "total", "arm", "tokens_log",
         "verbose_log", "wins", "wire", "reconstruction"]),
        "fields": FIELDS})
    return AgentCard(
        name="Grace-Compress",
        description="Stateless speaker/scorer for the Mission Log Relay (the astronaut).",
        version="1.0.0",
        supported_interfaces=[
            AgentInterface(url=f"http://{host}:{port}/", protocol_binding="JSONRPC"),
        ],
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(streaming=False, extensions=[ext]),
        skills=[AgentSkill(
            id="relay", name="Run mission-log relay",
            description="Relay a stream of records; build a shared codebook to cut tokens.",
            tags=["emergent", "compression"],
        )],
    )


def main() -> None:
    host, port = "localhost", 9201
    card = build_agent_card(host, port)
    handler = DefaultRequestHandler(
        agent_executor=GraceCompressExecutor(), task_store=InMemoryTaskStore(), agent_card=card,
    )
    routes = create_agent_card_routes(card) + create_jsonrpc_routes(handler, rpc_url="/")
    app = Starlette(routes=routes)
    print(f"Grace-Compress listening on http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
