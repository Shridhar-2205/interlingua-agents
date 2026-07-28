# Scenarios — A2A Message Passing

## Scenario 1: Agreement (convergence in 3 rounds)

Starting state: 3 meanings, agents disagree on all.

### Round 1 — Grace speaks, Rocky listens

**Grace → Rocky:**
```json
{
  "metadata": {
    "https://example.com/ext/emergent-lang/v1/context": {
      "grace_lex": {"apple": "✦", "dance": "≈", "river": "△"},
      "rocky_lex": {"apple": "○", "dance": "◆", "river": "▽"},
      "round": 1,
      "referent": "apple"
    },
    "https://example.com/ext/emergent-lang/v1/message": "✦"
  }
}
```

Rocky adopts: `"apple" → "✦"` (was "○")

**Rocky → Grace:**
```json
{
  "metadata": {
    "https://example.com/ext/emergent-lang/v1/context": {
      "grace_lex": {"apple": "✦", "dance": "≈", "river": "△"},
      "rocky_lex": {"apple": "✦", "dance": "◆", "river": "▽"},
      "round": 2,
      "referent": "dance"
    },
    "https://example.com/ext/emergent-lang/v1/message": "◆"
  }
}
```

Grace adopts: `"dance" → "◆"` (was "≈")

### Round 2 — Grace speaks, Rocky listens

**Grace → Rocky:**
```json
{
  "metadata": {
    "https://example.com/ext/emergent-lang/v1/context": {
      "grace_lex": {"apple": "✦", "dance": "◆", "river": "△"},
      "rocky_lex": {"apple": "✦", "dance": "◆", "river": "▽"},
      "round": 3,
      "referent": "river"
    },
    "https://example.com/ext/emergent-lang/v1/message": "△"
  }
}
```

Rocky adopts: `"river" → "△"` (was "▽")

### Round 3 — Alignment check → DONE

Rocky checks: `alignment == 1.0` (all 3 meanings match)

**Rocky responds (no further call):**
```json
{
  "message": {
    "parts": [{"text": "done | rounds: 3 | alignment: 100% | grace: {'apple': '✦', 'dance': '◆', 'river': '△'} | rocky: {'apple': '✦', 'dance': '◆', 'river': '△'}"}],
    "metadata": {
      "https://example.com/ext/emergent-lang/v1/context": {
        "grace_lex": {"apple": "✦", "dance": "◆", "river": "△"},
        "rocky_lex": {"apple": "✦", "dance": "◆", "river": "△"},
        "round": 3
      }
    }
  }
}
```

Response unwinds back to Mission Control. Game over.

---

## Scenario 2: Disagreement (conflict resolution)

Starting state: Rocky has `"fire" → "✦"` and Grace has `"moon" → "✦"` — same symbol, different meanings. This is a **conflict**.

### Round N — Grace speaks "moon = ✦"

**Grace → Rocky:**
```json
{
  "metadata": {
    "https://example.com/ext/emergent-lang/v1/context": {
      "grace_lex": {"moon": "✦", "fire": "○"},
      "rocky_lex": {"moon": "◆", "fire": "✦"},
      "round": 5,
      "referent": "moon"
    },
    "https://example.com/ext/emergent-lang/v1/message": "✦"
  }
}
```

Rocky runs `adopt(rocky_lex, "moon", "✦")`:
1. Finds conflict: `"fire"` also maps to `"✦"`
2. Removes the conflicting mapping: `del rocky_lex["fire"]`
3. Sets: `rocky_lex["moon"] = "✦"`

Rocky's lexicon is now: `{"moon": "✦"}` — he lost "fire" entirely.

### Round N+1 — Rocky re-coins "fire"

Rocky sees `"fire"` is unresolved (Grace has it, Rocky doesn't). He coins a fresh symbol.

**Rocky → Grace:**
```json
{
  "metadata": {
    "https://example.com/ext/emergent-lang/v1/context": {
      "grace_lex": {"moon": "✦", "fire": "○"},
      "rocky_lex": {"moon": "✦", "fire": "☆"},
      "round": 6,
      "referent": "fire"
    },
    "https://example.com/ext/emergent-lang/v1/message": "☆"
  }
}
```

Grace adopts: `"fire" → "☆"` (was "○")

### Round N+2 — Alignment check

Both now agree: `{"moon": "✦", "fire": "☆"}`

The conflict took 2 extra rounds to resolve — one to break the collision, one to re-establish the lost mapping.

---

## Scenario 3: Already aligned (early exit)

Starting state: both agents happen to agree on everything already.

### Trigger — Mission Control → Grace

Grace initializes lexicons. By chance (or test setup), they're identical:
```
grace_lex: {"apple": "✦", "dance": "≈", "river": "△"}
rocky_lex: {"apple": "✦", "dance": "≈", "river": "△"}
```

Grace checks alignment → `1.0` immediately.

**Grace responds (no call to Rocky at all):**
```json
{
  "message": {
    "parts": [{"text": "done | rounds: 0 | alignment: 100% | grace: {'apple': '✦', 'dance': '≈', 'river': '△'} | rocky: {'apple': '✦', 'dance': '≈', 'river': '△'}"}],
    "metadata": {
      "https://example.com/ext/emergent-lang/v1/context": {
        "grace_lex": {"apple": "✦", "dance": "≈", "river": "△"},
        "rocky_lex": {"apple": "✦", "dance": "≈", "river": "△"},
        "round": 0
      }
    }
  }
}
```

Zero rounds. Zero network calls. Game was already won at initialization.

---

## Scenario 4: Max rounds (timeout)

Starting state: agents keep coining new symbols instead of adopting (hypothetical — our implementation always adopts, but this shows the safety net).

After 60 rounds of ping-pong with no convergence:

```json
{
  "message": {
    "parts": [{"text": "done | rounds: 60 | alignment: 40% | grace: {...} | rocky: {...}"}],
    "metadata": {
      "https://example.com/ext/emergent-lang/v1/context": {
        "grace_lex": {"apple": "✦", "dance": "≈", "river": "△", "sea": "▽", ...},
        "rocky_lex": {"apple": "✦", "dance": "≈", "river": "○", "sea": "◆", ...},
        "round": 60
      }
    }
  }
}
```

Game stops at round 60 regardless. Partial alignment reported. This prevents infinite ping-pong.

---

## Summary

| Scenario | Rounds | What happens |
|----------|--------|-------------|
| Clean agreement | N meanings = N rounds | Each round resolves one disagreement |
| Symbol conflict | +2 extra rounds per conflict | Adopt breaks collision, then re-coin the lost meaning |
| Already aligned | 0 rounds | Grace detects 1.0 immediately, responds without calling Rocky |
| Timeout | 60 (max) | Game stops, reports partial alignment |
