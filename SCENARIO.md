# Scenarios — A2A Message Passing (Smart Convergence)

## Scenario 1: Batch convergence in 2 rounds

Starting state: 3 meanings, agents disagree on all. Batch proposals resolve everything in 2 rounds.

### Round 1 — Grace batch-proposes all disagreements

Grace generates proposals for all 3 unresolved meanings at once:

**Grace → Rocky:**
```json
{
  "metadata": {
    "https://example.com/ext/emergent-lang/v1/context": {
      "grace_lex": {
        "apple": {"symbol": "✦", "confidence": 0.5},
        "dance": {"symbol": "≈", "confidence": 0.5},
        "river": {"symbol": "△", "confidence": 0.5}
      },
      "rocky_lex": {
        "apple": {"symbol": "○", "confidence": 0.5},
        "dance": {"symbol": "◆", "confidence": 0.5},
        "river": {"symbol": "▽", "confidence": 0.5}
      },
      "round": 1
    },
    "https://example.com/ext/emergent-lang/v1/proposals": [
      {"referent": "apple", "symbol": "✦", "confidence": 0.5},
      {"referent": "dance", "symbol": "≈", "confidence": 0.5},
      {"referent": "river", "symbol": "△", "confidence": 0.5}
    ]
  }
}
```

Rocky runs `resolve_batch`:
- `apple`: Grace conf=0.5, Rocky conf=0.5 → equal, **adopt** Grace's "✦"
- `dance`: Grace conf=0.5, Rocky conf=0.5 → equal, **adopt** Grace's "≈"
- `river`: Grace conf=0.5, Rocky conf=0.5 → equal, **adopt** Grace's "△"

Rocky's lexicon after: `{"apple": {"symbol": "✦", "confidence": 0.7}, "dance": {"symbol": "≈", "confidence": 0.7}, "river": {"symbol": "△", "confidence": 0.7}}`

### Round 2 — Rocky checks alignment → DONE

Rocky sees alignment = 1.0, responds:

```json
{
  "message": {
    "parts": [{"text": "done | rounds: 1 | alignment: 100% | grace: {...} | rocky: {...}"}],
    "metadata": {
      "https://example.com/ext/emergent-lang/v1/context": {
        "grace_lex": {
          "apple": {"symbol": "✦", "confidence": 0.5},
          "dance": {"symbol": "≈", "confidence": 0.5},
          "river": {"symbol": "△", "confidence": 0.5}
        },
        "rocky_lex": {
          "apple": {"symbol": "✦", "confidence": 0.7},
          "dance": {"symbol": "≈", "confidence": 0.7},
          "river": {"symbol": "△", "confidence": 0.7}
        },
        "round": 1
      }
    }
  }
}
```

All 3 meanings resolved in **1 round** (vs. 3 rounds without batching).

---

## Scenario 2: Confidence-based yielding

Starting state: Rocky has `"fire" → "✦"` with confidence 0.7 (adopted). Grace has `"fire" → "○"` with confidence 0.5 (coined).

### Grace proposes batch including fire

**Grace → Rocky:**
```json
{
  "metadata": {
    "https://example.com/ext/emergent-lang/v1/proposals": [
      {"referent": "fire", "symbol": "○", "confidence": 0.5}
    ]
  }
}
```

Rocky runs `resolve_batch`:
- `fire`: Grace conf=0.5, Rocky conf=0.7 → Rocky's confidence is **higher** → **reject**
- Rocky keeps `"fire" → "✦"` (confidence 0.7)

### Rocky proposes back

**Rocky → Grace:**
```json
{
  "metadata": {
    "https://example.com/ext/emergent-lang/v1/proposals": [
      {"referent": "fire", "symbol": "✦", "confidence": 0.7}
    ]
  }
}
```

Grace runs `resolve_batch`:
- `fire`: Rocky conf=0.7, Grace conf=0.5 → Rocky's confidence is higher → **adopt**
- Grace sets `"fire" → {"symbol": "✦", "confidence": 0.7}`

Result: the higher-confidence mapping wins. No flip-flopping.

---

## Scenario 3: Mutual exclusivity prevents collisions

Starting state: Grace has `"star" → "○"` and Rocky has `"wind" → "○"` — same symbol, different meanings.

### Without mutual exclusivity (old behavior)

Grace proposes "○" for `star`. Rocky adopts but loses `wind=○`. Extra round needed to re-coin wind.

### With mutual exclusivity (this branch)

Grace's `coin_exclusive()` sees "○" is already in Rocky's lexicon. Instead of proposing "○", she coins a fresh symbol "☆" that's free in both lexicons.

**Grace → Rocky:**
```json
{
  "metadata": {
    "https://example.com/ext/emergent-lang/v1/proposals": [
      {"referent": "star", "symbol": "☆", "confidence": 0.5}
    ]
  }
}
```

Rocky adopts "☆" for star. His `wind=○` mapping is untouched. Zero collision rounds.

---

## Scenario 4: Full 10-meaning convergence

Starting state: 10 meanings, all different between agents. All confidence = 0.5 (freshly coined).

### Round 1 — Grace batch-proposes all 10

Grace sends 10 proposals. Rocky receives all 10 with confidence 0.5.
Rocky's confidence for each is also 0.5 → equal confidence → adopts all 10.

Rocky checks alignment → 1.0 → **DONE**.

```json
{
  "message": {
    "parts": [{"text": "done | rounds: 1 | alignment: 100% | grace: {...} | rocky: {...}"}]
  }
}
```

**10 meanings converged in 1 round.** Batch proposals + equal confidence = instant convergence.

---

## Scenario 5: Max rounds (timeout)

After 60 rounds with persistent confidence deadlocks:

```json
{
  "message": {
    "parts": [{"text": "done | rounds: 60 | alignment: 80% | grace: {...} | rocky: {...}"}],
    "metadata": {
      "https://example.com/ext/emergent-lang/v1/context": {
        "grace_lex": {"apple": {"symbol": "✦", "confidence": 1.0}, ...},
        "rocky_lex": {"apple": {"symbol": "✦", "confidence": 1.0}, ...},
        "round": 60
      }
    }
  }
}
```

Game stops at round 60. In practice, smart convergence resolves in 1-5 rounds.

---

## Summary

| Scenario | Rounds | What happens |
|----------|--------|-------------|
| Batch agreement (equal confidence) | 1 round | All meanings resolved in one batch |
| Confidence yielding | 2-3 rounds | Lower confidence yields, higher wins |
| Mutual exclusivity | 0 extra rounds | No symbol collisions ever occur |
| Full 10-meaning game | 1-5 rounds | Batch + confidence = fast convergence |
| Timeout | 60 (max) | Safety net — rarely hit with smart convergence |
