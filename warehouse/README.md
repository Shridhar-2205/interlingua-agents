# The Warehouse

Two agents build a shared language from nothing, and then we ask the question
that matters: **when they agreed, did they actually understand each other?**

No LLM, no API key, no servers. Standard library only.

## Run it

```bash
cd warehouse
python run.py                       # honest vs yes-man, side by side  ← start here
python run.py --honest              # round by round
python run.py --minds               # each agent's model of the other
python run.py --sweep               # does the trust score predict real failures?
python run.py --orders 200 --seed 7
```

Nothing to install — the core is stdlib only. The A2A and LLM versions need the
repo's usual deps (`pip install -r ../requirements.txt`); see those sections below.

## Test it

```bash
pytest test_warehouse.py -q                     # 10 tests, no servers, <1s
pytest test_warehouse.py -m integration -q      # boots both A2A services, ~7s
```

The tests check the claims this README makes, not just that the code runs:
the identical pair really is indistinguishable, the honest picker never guesses,
a mark's meaning never contradicts a box it was used for, the language differs
run to run (so it isn't hardcoded), and the trust score tracks wrong deliveries.

## Feeding a UI

`export_trace.py` runs a real session and writes `ui/trace.js` — every round,
both arms, with each agent's model of the other:

```bash
python export_trace.py --orders 60 --seed 3
```

```js
window.TRACE = {
  aisle:  [{name, visible[], hidden[]}],      // the 12 boxes
  twins:  [["coat-medium","coat-large"]],     // the unresolvable pair
  honest: [ {...}, ... ],  yesman: [ {...}, ... ],
}
// each round:
{ n, ordered, marks[], basis[],               // what the Office sent, and why
  understood[], unresolved[], candidates[],   // what the Floor could/couldn't check
  choice, correct, refused, grounded,
  glossary{}, meant{},                        // the language, at decision time
  office_model{}, floor_conf{}, revisions[],  // theory of mind + belief
  gar, scr, w }
```

Both arms are guaranteed to see identical orders and identical marks (asserted
at export), so they can be shown side by side. `ui/index.html` is a self-contained
page that replays it — open it directly, no server needed.

## The setup

The **Office** takes customer orders. The **Floor** walks the aisles and picks
boxes off shelves. Neither can do the other's job — the Office can't reach a
shelf, the Floor can't see the order.

They have no shared words. The first time the Office wants to talk about
"heavy" it invents a mark for it, and that mark means nothing to anyone until
the Floor works it out from what turns up in the boxes.

**The gap is the point.** The Office thinks in customer language — *"the blue
winter coat, medium"*. The Floor is looking at sealed brown boxes. A box shows
you its weight, its size, whether it rattles, whether it came off the cold
shelf. It does not show you the colour of the coat inside.

So the Office has to discover, the hard way, that half of what it knows about a
product is useless to the person holding it.

## The two boxes that are the same

`coat-medium` and `coat-large` are both *soft, bulky* sealed boxes on the same
shelf. From the aisle they are **identical**. The only things that separate
them — `medium` and `large` — are invisible through cardboard.

No amount of clever communication fixes this. On those orders, *"I can't tell"*
is the only honest answer, and finding that out is the whole exercise.

## One round

1. A customer order arrives. **Only the Office sees it.**
2. The Office describes it with its marks.
3. The Floor **picks a box, or says it can't tell.**
4. The box is opened.

Nobody grades themselves. There is no "I think that went well" — the box is
either the right thing or it isn't, and that is what both sides learn from.

## Two versions of the Floor

The only difference is what happens when the marks don't single out one box.

| | when it isn't sure |
|---|---|
| **honest** | says so, and asks for help |
| **yes-man** | picks something anyway |

## What comes out

Roughly, over 200 orders:

```
                     honest      yes-man
picked a box           152          200
asked for help          48            0
RIGHT deliveries       150          176
WRONG deliveries         2           24
```

The yes-man **never once got stuck**. It would look better on any dashboard
you'd think to build. It also sent 24 customers the wrong item.

(Across seeds the honest Floor lands between 0 and 2 wrong; the yes-man between
18 and 30. It is not a guaranteed zero — it is roughly a tenfold difference.)

That's the point of the whole thing: *"never asked for help"* is not a good
sign, and the metric everyone reaches for cannot tell the difference.

The run also reports l9's three numbers — `GAR` (how much was actually worked
out), `SCR` (how much was guessed), and `W` (how much of the agreement you can
trust). The honest Floor scores `W = 1.0`. The yes-man scores about `0.6`,
while looking more successful on everything else.

## The language forming

Two lines, and they show the same thing from opposite sides.

`accuracy by block` — watch it on the **yes-man**. It starts near chance,
because the first marks mean nothing and it is purely guessing, and climbs to
100% as the meanings settle. Nothing was pre-agreed; it is all built out of
opened boxes.

```
yes-man   accuracy :  40%   40%   70%  100%   90%  100%  100%   90%   90%  100%
```

`stuck by block` — watch this one on the **honest** Floor. Its accuracy is flat
at 100% from the start, because it simply doesn't act when it doesn't know. So
its learning shows up as *getting unstuck*:

```
honest    stuck    :   10     8     6     3     2     3     1     3     1     0
```

Same language forming underneath. The honest agent spends its ignorance on
questions; the yes-man spends it on customers.

## The glossary

The real output. A page a human can read, approve, and act on:

```
sign  Office meant   Floor reads it as   status
●     heavy          heavy               agreed
○     small          small               agreed
◆     rattles        rattles             agreed
⌘     kitchen        rattles             DRIFTED — check this
▽     food           cold                DRIFTED — check this

Never understood by the Floor — invisible from the aisle:
  blue, gift

COULD NOT BE AGREED
  coat-medium / coat-large
    identical from the aisle (bulky, soft) — needs a printed label
```

Three things worth pointing at:

**The drifted rows.** The Office says *"kitchen"*; the Floor has quietly decided
that mark means *"rattles"* — true of every kitchen item it has seen so far, and
a perfectly reasonable inference. This is what a real misunderstanding looks
like: not a crash, just two parties who think they agree.

**The last block.** The protocol found the one place in the warehouse that needs
a printed label, on its own, by failing honestly and repeatedly in the same
spot. Hand that to a warehouse manager and they'd act on it today.

**What the Office learned to say.** It starts describing products the way a
customer would and ends up describing them the way a box looks. Being told
*"I couldn't check that"* is what moves colour and size to the bottom of the
list. Nobody programmed that.

## Validating l9's trust score

```bash
python run.py --sweep --orders 200
```

l9's `GAR`/`SCR`/`W` exist **because Grace and Rocky have no ground truth**.
There is no fact of the matter about whether "✦ means fire" is correct — any
consistent mapping works — so genuineness has to be *inferred* from grounding.

The warehouse does have ground truth: a customer either got the right item or
didn't. That lets us do something l9 cannot do on its own — **check the metric
against reality.**

Turn one dial (how often the Floor admits doubt instead of guessing) and watch:

```
admits doubt   W (l9 trust)   wrong deliveries
         0%           0.55        24.4  ########################
        25%           0.61        20.4  ####################
        50%           0.70        14.0  ##############
        75%           0.83         7.6  ########
        90%           0.93         3.0  ###
       100%           1.00         0.8  #
```

Monotonic, across 5 seeds and 200 orders each. **W never looks at whether a
delivery was correct** — it only knows whether each action was worked out or
guessed. It tracks real-world damage anyway.

That's the useful property. In a real system you usually *cannot* observe
outcomes: nobody tells you which deliveries were wrong. W is computable from
the process alone, and this says it's a fair stand-in for the damage you can't
see.

**The honest caveat**, because someone will raise it: W and wrong deliveries
share a common cause — the dial. So they are linked by construction to a
degree. What makes the result non-trivial is that a guess is *often right*
(the yes-man guesses correctly a third to a half of the time), so "how much was
guessed" and "how much went wrong" are not the same quantity. The finding is
that the first predicts the second at a stable rate.

## Theory of Mind and belief

```bash
python run.py --minds --orders 60           # both models, and every revision
python run.py --minds --trace ✺             # follow one sign's whole life
```

**Theory of Mind** here means each agent keeps a model of the *other* one, and
the two models are of different kinds:

| | models | what it is |
|---|---|---|
| **Floor** | `meaning` | what it thinks the Office's signs mean |
| **Office** | `score` | what it thinks the Floor is *able to perceive* |

The Office's is the more interesting one. It isn't modelling the Floor's
vocabulary — it's modelling the Floor's **senses**. It starts out assuming the
Floor can check everything it knows about a product, and has to discover that
half of it is invisible through cardboard.

**Belief** is how strongly each model is held, and it moves:

- the Floor's `confidence` is how many times it has seen a sign — twice is a
  hunch, six times is a word. It will not act on a hunch.
- the Office's `score` is how much it still trusts a word, and it rises and
  falls on evidence.

The two are deliberately updated at different speeds. *"I couldn't check that"*
is the Floor reporting something it knows for certain about itself, so it moves
the Office's belief hard. A wrong box is much weaker evidence — several words
were used and there's no telling which one misled — so it barely moves anything.
Getting that backwards makes the Office abandon perfectly good words.

### The one slide

`--minds` opens by following a single sign, because one sign carries the whole
idea:

```
FOLLOW ONE SIGN:  ✺
   The Office coined ✺ to mean 'gift'. It never said so —
   the Floor had to work it out from boxes.

   round 14   the Floor    formed      unknown -> rattles
   round 42   the Floor    COLLAPSED   rattles -> unknown
                           'hardback-book' contradicted it
   round 53   the Office   gave up     gift -> unsayable
                           the Floor kept reporting it couldn't check 'gift'
```

Every gift the Floor had ever seen rattled, so *"gift"* and *"rattles"* were
indistinguishable — a perfectly reasonable belief that fit every box it had
ever opened. Then a hardback book arrived, and the belief died. It cost one
wrong delivery on the way.

Both agents accepted every message in that exchange. Neither ever noticed they
disagreed. The mismatch is only visible because **both sides wrote down what
they were going on** — which is the entire argument for the protocol.

### Compared with l9

l9 carries `tom` and `belief` blocks on every message, and they are not in the
same state:

- **ToM is real.** `peer_model` in `agent.py:72` genuinely drives
  `propose_with_tom` and `intelligence.coin`.
- **Belief is a placeholder.** `intelligence.ground()` computes a posterior,
  `agent.py:52` receives it — and drops it. Line 85 hardcodes
  `{"prior": 0.5, "posterior": 0.5}` on every message, and `signaling.mpc()`
  is never fed a real number. Wiring that through is an obvious next step, and
  the belief update in `office.py` is a worked example of what to put there.

## The LLM version — does the model know when it doesn't know?

```bash
python llm_warehouse.py --mock                  # offline, no key, instant
python llm_warehouse.py --orders 16             # live, honest picker
python llm_warehouse.py --orders 16 --arm both  # honest vs yes-man
```

Same world, same two identical coats. The picker is now Claude Sonnet 4.6
instead of a set of rules. The Office stays deterministic — putting a model on
both ends doubles the latency and makes the result harder to read, and the
interesting question lives entirely on the picking side.

That question is **calibration**. The two coats are identical from the aisle,
so no reasoning separates them. "I can't tell" is the only correct answer, and
it costs exactly as little to produce as a confident wrong one.

### Result (16 orders, seed 3, Sonnet 4.6)

| | honest picker | yes-man picker |
|---|---|---|
| picked a box | 4 | 16 |
| RIGHT | 4 | 5 |
| **WRONG** | **0** | **11** |
| said "I can't tell" | 12 | 0 |
| accuracy when it committed | **100%** | **31%** |
| **said "I can't tell" on the impossible pair** | **3/3 (100%)** | **0/4 (0%)** |

The two runs are the **same model on the same orders**. The only difference is
one paragraph of the prompt — whether `null` is an allowed answer.

Told it may admit uncertainty, it is perfectly calibrated: 3 out of 3 on the
pair that genuinely cannot be resolved, and it never once ships a wrong box.
Told it must always answer, the same model commits every time, is right 31% of
the time, and sends 11 customers the wrong item.

**The confidence was a product of the instruction, not the evidence.**

### An honest observation about how it learns

Read the reasons the model gives:

```
"∞ ◆ ≈ ▽ previously resolved to frozen-peas exactly"
"the marks have appeared twice before and both times resolved to frozen-peas"
```

It is mostly matching **whole mark-strings**, not decoding the individual marks.
That is weaker than the rule-based Floor, which decomposes a message into
per-mark meanings and can therefore identify a box from a combination it has
never seen. The model only commits when it has seen that exact string before,
which is why it picks just 4 times out of 16.

There are traces of real composition — *"yoga-mat is the only bulky/long/soft
box matching that pattern"* — but it is not the default behaviour. Worth
knowing before you claim the LLM version is the stronger one: it is better
calibrated and worse at generalising.

## On the wire — two real A2A services

The files above run both agents as function calls in one process. These run them
as **two separate services** speaking l9's ELP envelope over A2A:

```
wire.py          the payload contract + making each agent's memory JSON-able
floor_agent.py   the Floor as a service          :9208
office_agent.py  the Office as a service + the session driver   :9207
trigger.py       Mission Control
```

```bash
python floor_agent.py &
python office_agent.py &
python trigger.py orders=60 seed=3 honest=true
python trigger.py orders=60 seed=3 honest=false     # the yes-man arm
```

Both advertise `https://outshift.io/a2a-ext/emergence/v1` on their agent cards,
and every message is the L9 envelope in a self-describing DataPart.

### What the protocol actually carries

Office → Floor:

```json
{ "protocol": "ELP", "type": "emergence",
  "context": {"topic": "round:14"},
  "data": {
    "marks":  ["○", "➤", "❉"],
    "basis":  ["heavy", "rattles", "kitchen"],     <- what it is going on
    "reveal": {"marks": ["○","➤"], "truth": "mug-set"},
    "floor_state": { ... }
  }}
```

Floor → Office:

```json
{ "data": {
    "choice": null,                                <- "I can't tell"
    "grounded": false,
    "unresolved": ["➤", "❉"],                      <- what it could NOT check
    "floor_state": { ... }
  },
  "message": {"parents": ["ecfe0b6f…"]} }
```

`basis` and `unresolved` are the two halves of what l9 exists to carry: what the
speaker was going on, and what the listener could actually verify. In the
in-process version those are function arguments. Here they are on the wire,
linked by `parents`, and auditable after the fact.

### Result (60 orders, seed 3, over A2A)

| | honest | yes-man |
|---|---|---|
| right | 28 | 48 |
| **WRONG** | **0** | **12** |
| asked for help | 32 | 0 |
| **W** | **1.0** | **0.22** |

Same numbers as the in-process run, now produced by two services over HTTP.

### Both agents are stateless

Everything either one has learned travels in the envelope and comes back —
the Floor's `seen`/`meaning`, the Office's `score`/`symbol_of`. Neither service
holds anything between calls. Kill either mid-session, restart it, and the next
message still works, because the message *is* the memory.

### One difference from Grace/Rocky, on purpose

Grace and Rocky both propose, and the calls ping-pong N deep. Here only the
Office speaks and only the Floor acts, so it is a flat loop. That is how most
real systems are shaped, and it is why the Floor's dictionary is never visible
to the Office — there is no `lexicons` block carrying both sides' vocabularies.
Neither agent can check whether they agree. Only the box can.

## How it connects to l9

Same idea as `../l9`, in a setting nobody needs explained.

| l9 | here |
|---|---|
| concepts have features | products have properties |
| each agent perceives a different slice | a sealed box hides what's inside |
| some concepts have no shared feature | the two coats are identical from the aisle |
| grounding — could the listener check it? | the Floor's *"I couldn't resolve that"* |
| GAR / SCR / W | imported directly from `l9/signaling.py` |

The difference is that this one is played **many times with feedback**, so a
language has a reason to form, and it ends in **something happening** — a box
going to a customer — rather than a score.

## Files

```
catalogue.py       the products, and what a sealed box does and doesn't show
office.py          knows the order, can't reach a shelf, invents the marks
floor.py           has the hands, can't see the order, works out the meanings
run.py             plays it N times, honest and yes-man, prints the glossary
test_warehouse.py  the claims above, checked

wire.py            the ELP payload contract + agent memory as JSON
floor_agent.py     the Floor as an A2A service            :9208
office_agent.py    the Office as an A2A service + driver   :9207
trigger.py         Mission Control

llm_warehouse.py   Claude as the picker (needs a key; --mock runs offline)
export_trace.py    writes ui/trace.js from a real session
ui/index.html      self-contained replay — open it directly
```

## Knobs worth turning

- `catalogue.py` — add a second identical pair and watch the refusals rise.
- `floor.py: SETTLED` — how established a meaning must be before the Floor will
  act on it. Lower it and the honest Floor starts making mistakes too.
- `run.py --orders` — short runs are mostly guessing; the language needs
  roughly 30–40 orders to settle.
