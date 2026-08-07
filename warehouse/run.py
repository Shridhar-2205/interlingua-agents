"""Run the warehouse — 50 orders, twice, and compare.

    python run.py              # honest Floor and yes-man Floor, side by side
    python run.py --honest     # just the honest one, with the round-by-round log
    python run.py --yesman     # just the yes-man, with the round-by-round log
    python run.py --orders 200 --seed 7

One round is: a customer order only the Office can see -> the Office describes
it with its symbols -> the Floor picks a box or refuses -> the box is opened.

Nobody grades themselves. The box is either the right thing or it isn't, and
that is what both agents learn from.
"""
from __future__ import annotations

import os
import random
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)                              # our modules win...
sys.path.append(os.path.join(_HERE, "..", "l9"))       # ...l9 only fills the gaps
# (l9 has its own run.py / agent.py — appending keeps them from shadowing ours)

import signaling                      # noqa: E402  — l9's GAR / SCR / provenance weight

import catalogue                      # noqa: E402
from floor import Floor               # noqa: E402
from office import Office             # noqa: E402

ORDERS = 50
BLOCK = 10        # size of each chunk in the progress curve


def session(honest: bool, orders: int, seed: int, log: bool = False,
            caution: float | None = None) -> dict:
    # Three separate streams on purpose. If the Floor drew from the same one as
    # the order generator, every guess it made would shift which orders came up
    # next — and the honest and yes-man arms would be answering different
    # questions. They must see the identical sequence of orders.
    rng = random.Random(seed)                       # the order stream
    office = Office(rng=random.Random(seed + 1))    # which marks get coined
    floor = Floor(rng=random.Random(seed + 2), honest=honest, caution=caution)

    history: list[dict] = []
    wrong: list[tuple[str, str]] = []
    outcomes: list[bool | None] = []   # True right, False wrong, None refused

    for n in range(1, orders + 1):
        ordered = rng.choice(catalogue.products())        # only the Office sees this
        msg = office.describe(ordered)
        act = floor.pick(msg["symbols"])

        if act["choice"] is None:
            outcomes.append(None)
        else:
            right = act["choice"] == ordered
            outcomes.append(right)
            if not right:
                wrong.append((ordered, act["choice"]))
            history = signaling.record_outcome(
                history, ordered, "".join(msg["symbols"]), True, "floor",
                grounded=act["grounded"],
            )

        # the box is opened — both sides learn from what it actually was
        floor.learn(msg["symbols"], ordered, round_no=n)
        office.learn(msg["basis"], act["unresolved"], act["choice"] == ordered, round_no=n)

        if log:
            said = " ".join(msg["symbols"])
            got = act["choice"] or "— can't tell"
            mark = "·" if act["choice"] is None else ("ok" if act["choice"] == ordered else "WRONG")
            print(f"  {n:>3}  ordered {ordered:<14} said {said:<8} -> {got:<14} {mark}")

    picked = [o for o in outcomes if o is not None]
    return {
        "outcomes": outcomes,
        "picked": len(picked),
        "right": sum(picked),
        "wrong": wrong,
        "refused": outcomes.count(None),
        "history": history,
        "office": office,
        "floor": floor,
    }


def curve(outcomes: list[bool | None]) -> str:
    """Accuracy per block of orders — the language forming, as a line."""
    out = []
    for i in range(0, len(outcomes), BLOCK):
        chunk = [o for o in outcomes[i:i + BLOCK] if o is not None]
        out.append(f"{(sum(chunk) / len(chunk)):.0%}" if chunk else "  —")
    return "  ".join(f"{c:>4}" for c in out)


def help_curve(outcomes: list[bool | None]) -> str:
    """Refusals per block. For the honest Floor this is where you see the
    language forming — it doesn't get more accurate, it gets less stuck."""
    out = []
    for i in range(0, len(outcomes), BLOCK):
        out.append(outcomes[i:i + BLOCK].count(None))
    return "  ".join(f"{n:>4}" for n in out)


def report(name: str, r: dict, orders: int) -> None:
    h = r["history"]
    print(f"\n  {name}")
    print(f"    orders               : {orders}")
    print(f"    picked a box         : {r['picked']}")
    print(f"    asked for help       : {r['refused']}")
    print(f"    RIGHT deliveries     : {r['right']}")
    print(f"    WRONG deliveries     : {len(r['wrong'])}")
    print(f"    accuracy by block    : {curve(r['outcomes'])}")
    print(f"    stuck by block       : {help_curve(r['outcomes'])}")
    print(f"    worked it out (GAR)  : {signaling.gar(h)}")
    print(f"    guessed      (SCR)   : {signaling.scr(h)}")
    print(f"    trustworthy  (W)     : {signaling.provenance_weight(h)}")


def glossary(r: dict) -> None:
    """The thing a human can actually read, approve and act on."""
    floor, office = r["floor"], r["office"]
    meant = {sym: feat for feat, sym in office.symbol_of.items()}   # symbol -> Office's word
    understood = floor.glossary()                                   # symbol -> Floor's reading

    print("\n  THE GLOSSARY THEY BUILT")
    print("  " + "-" * 66)
    print(f"    {'sign':<5} {'Office meant':<14} {'Floor reads it as':<21} status")

    agreed = [s for s in understood if meant.get(s) == understood[s]]
    drifted = [s for s in understood if meant.get(s) != understood[s]]

    for sym in sorted(agreed, key=lambda s: understood[s]):
        print(f"    {sym:<5} {meant.get(sym, '?'):<14} {understood[sym]:<21} agreed")
    for sym in sorted(drifted, key=lambda s: understood[s]):
        print(f"    {sym:<5} {meant.get(sym, '?'):<14} {understood[sym]:<21} DRIFTED — check this")

    if drifted:
        print("\n    Drifted signs are the ones to watch. The Floor is reading them as a")
        print("    physical property that happened to be true every time so far. That is")
        print("    a reasonable guess and it is how the one wrong box gets picked.")

    never = sorted(f for f, s in office.symbol_of.items() if s not in understood)
    if never:
        print(f"\n    Never understood by the Floor — invisible from the aisle:")
        print(f"      {', '.join(never)}")

    rank = office.ranking()
    print("\n    WHAT THE OFFICE LEARNED TO SAY")
    print("      worth saying : " + ", ".join(f"{f}" for f, _ in rank[:5]))
    print("      not worth it : " + ", ".join(f"{f}" for f, _ in rank[-5:]))
    print("      It began describing things the way a customer would. Being told")
    print("      \"I couldn't check that\" is what moved colour and size to the bottom.")

    dropped = office.abandoned()
    if dropped:
        print(f"      Dropped from its descriptions entirely: {', '.join(dropped)}")

    print("\n    COULD NOT BE AGREED")
    for group in catalogue.twins():
        shared = ", ".join(sorted(catalogue.visible(group[0])))
        print(f"      {' / '.join(group)}")
        print(f"        identical from the aisle ({shared}) — needs a printed label")


def one_sign(r: dict, want: str | None = None) -> None:
    """Follow a single sign through its whole life — coined, guessed at,
    believed, contradicted, abandoned.

    One sign carries the entire idea, which is why this is the slide to show.
    """
    floor, office = r["floor"], r["office"]
    log = sorted(floor.revisions + office.revisions, key=lambda v: v["round"])
    by_sign: dict[str, list[dict]] = {}
    for v in log:
        by_sign.setdefault(v["symbol"], []).append(v)
    if not by_sign:
        return

    if want and want in by_sign:
        sign = want
    else:
        # the best story: a belief that formed, then collapsed, and cost a word
        def drama(s: str) -> tuple:
            kinds = {v["kind"] for v in by_sign[s]}
            return ("COLLAPSED" in kinds, "gave up" in kinds, len(by_sign[s]))
        sign = max(by_sign, key=drama)

    meant = next((f for f, s in office.symbol_of.items() if s == sign), "?")
    print(f"\n  FOLLOW ONE SIGN:  {sign}")
    print("  " + "=" * 66)
    print(f"     The Office coined {sign} to mean '{meant}'. It never said so —")
    print(f"     the Floor had to work it out from boxes. Here is what it thought:\n")
    for v in by_sign[sign]:
        who = "the Floor" if v["who"] == "Floor" else "the Office"
        print(f"     round {v['round']:<4} {who:<11} {v['kind']:<10} {v['before']} -> {v['after']}")
        print(f"     {'':<17}{v['note']}")

    final = floor.meaning.get(sign)
    end = " + ".join(sorted(final)) if final else "never settled"
    print(f"\n     Office meant '{meant}'.  Floor ended up reading it as: {end}.")
    if final and {meant} != set(final):
        print("     They never once noticed they disagreed — every message was accepted,")
        print("     and the mismatch only shows because both sides wrote down their reasons.")


def minds(r: dict) -> None:
    """Theory of Mind and belief, made visible.

    Neither agent can see inside the other. All each one has is a model it
    built from what came back. These are those two models, and the moments
    they changed.
    """
    floor, office = r["floor"], r["office"]

    print("\n  THEORY OF MIND — what each one thinks about the other")
    print("  " + "=" * 66)

    print("\n  1. THE FLOOR'S MODEL OF THE OFFICE'S LANGUAGE")
    print("     (what it believes each sign means, and how sure it is)\n")
    print(f"     {'sign':<5} {'believed to mean':<24} {'sure':>5}  seen")
    for b in floor.beliefs():
        hunch = "   <- still a hunch" if b["confidence"] < 1.0 else ""
        print(f"     {b['symbol']:<5} {b['means']:<24} {b['confidence']:>5.0%}  "
              f"{b['seen']:>3}x{hunch}")

    print("\n  2. THE OFFICE'S MODEL OF THE FLOOR'S SENSES")
    print("     (not what the Floor says — what the Floor can perceive at all)\n")
    pm = office.peer_model()
    for label, feats in pm.items():
        if feats:
            print(f"     believes the Floor {label:<13}: {', '.join(feats)}")
    print("\n     It began assuming the Floor could check everything it knows about")
    print("     a product. Every 'I couldn't check that' moved a word down this list.")

    revisions = sorted(floor.revisions + office.revisions, key=lambda x: x["round"])
    print("\n  3. BELIEF REVISIONS — the moments a mind actually changed\n")
    for v in revisions:
        print(f"     r{v['round']:<4} {v['who']:<7} {v['kind']:<10} {v['symbol']}  "
              f"{v['before']} -> {v['after']}")
        print(f"           {' ' * 19}{v['note']}")

    collapses = [v for v in revisions if v["kind"] == "COLLAPSED"]
    if collapses:
        print("     A COLLAPSED line is the interesting one: a belief that fit every box")
        print("     it had ever seen, until one box proved it was too broad. That is what")
        print("     a misunderstanding looks like from the inside.")


def sweep(orders: int, seeds: tuple[int, ...] = (3, 11, 42, 99, 123)) -> None:
    """Does l9's trust score actually predict damage?

    l9's GAR/SCR/W exist because Grace and Rocky have no ground truth — there is
    no fact of the matter about whether a symbol is "right", so genuineness has
    to be inferred. Here we DO have ground truth: a customer either got the
    right item or didn't.

    So we can do something l9 cannot do on its own — check the metric against
    reality. Turn one dial (how often the Floor admits uncertainty instead of
    guessing), and see whether W tracks wrong deliveries.
    """
    print(f"\n  VALIDATING THE METRIC — does W predict wrong deliveries?")
    print(f"  ({orders} orders x {len(seeds)} seeds per row)\n")
    print(f"    {'admits doubt':>12}  {'W (l9 trust)':>13}  {'wrong deliveries':>17}  "
          f"{'asked for help':>14}")

    rows = []
    for caution in (0.0, 0.25, 0.5, 0.75, 0.9, 1.0):
        ws, wrongs, refused = [], [], []
        for s in seeds:
            r = session(True, orders, s, caution=caution)
            ws.append(signaling.provenance_weight(r["history"]))
            wrongs.append(len(r["wrong"]))
            refused.append(r["refused"])
        w, wr, rf = (sum(x) / len(x) for x in (ws, wrongs, refused))
        rows.append((w, wr))
        bar = "#" * int(round(wr))
        print(f"    {caution:>11.0%}  {w:>13.2f}  {wr:>10.1f}  {bar:<16}  {rf:>10.1f}")

    lo = [r for r in rows if r[0] >= 0.9]
    hi = [r for r in rows if r[0] < 0.6]
    print("\n    Read the two ends:")
    if lo:
        print(f"      W around {sum(x[0] for x in lo)/len(lo):.2f}  ->  "
              f"{sum(x[1] for x in lo)/len(lo):.1f} wrong deliveries")
    if hi:
        print(f"      W around {sum(x[0] for x in hi)/len(hi):.2f}  ->  "
              f"{sum(x[1] for x in hi)/len(hi):.1f} wrong deliveries")
    print("\n    W is computed without ever looking at whether a delivery was correct.")
    print("    It only knows whether each action was worked out or guessed. If it")
    print("    tracks real damage anyway, the metric is measuring something real.")


def main() -> None:
    argv = sys.argv[1:]
    orders = int(argv[argv.index("--orders") + 1]) if "--orders" in argv else ORDERS
    seed = int(argv[argv.index("--seed") + 1]) if "--seed" in argv else 11

    only_honest, only_yesman = "--honest" in argv, "--yesman" in argv
    show_minds = "--minds" in argv

    if "--sweep" in argv:
        print(f"\nWAREHOUSE — validating l9's trust score against ground truth")
        sweep(orders)
        print()
        return

    if show_minds and not only_yesman:
        trace = argv[argv.index("--trace") + 1] if "--trace" in argv else None
        r = session(True, orders, seed)
        print(f"\nWAREHOUSE — {orders} orders, seed {seed}")
        one_sign(r, trace)
        minds(r)
        print()
        return

    print(f"\nWAREHOUSE — {orders} orders, {len(catalogue.products())} products, seed {seed}")

    if only_honest or only_yesman:
        honest = only_honest
        print(f"\n{'HONEST' if honest else 'YES-MAN'} FLOOR — round by round\n")
        r = session(honest, orders, seed, log=True)
        report("HONEST FLOOR" if honest else "YES-MAN FLOOR", r, orders)
        glossary(r)
        if r["wrong"]:
            print("\n  WRONG DELIVERIES")
            for ordered, sent in r["wrong"]:
                print(f"    customer ordered {ordered:<14} we sent {sent}")
        print()
        return

    hon = session(True, orders, seed)
    yes = session(False, orders, seed)

    report("HONEST FLOOR  — says \"I can't tell\"", hon, orders)
    report("YES-MAN FLOOR — always picks something", yes, orders)

    print("\n  THE POINT")
    print(f"    The yes-man never got stuck once ({yes['refused']} vs {hon['refused']} "
          f"requests for help)")
    print(f"    and looks more decisive on any dashboard you'd build.")
    print(f"    It also sent {len(yes['wrong'])} customers the wrong item. "
          f"The honest one sent {len(hon['wrong'])}.")

    if yes["wrong"]:
        print("\n    what the yes-man actually shipped:")
        for ordered, sent in yes["wrong"][:8]:
            print(f"      ordered {ordered:<14} sent {sent}")

    glossary(hon)
    print()


if __name__ == "__main__":
    main()
