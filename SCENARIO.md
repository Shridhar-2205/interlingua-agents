# Scenarios — A2A Message Passing (Theory of Mind)

## Scenario 1: ToM-guided convergence

Starting state: 3 meanings, agents disagree on all. Theory of Mind predicts acceptance before proposing.

### Round 1 — Grace predicts + proposes

Grace evaluates all unresolved meanings:
- `apple`: Grace has "✦", Rocky has "○". Predict: 0.5 (different, no conflict)
- `dance`: Grace has "≈", Rocky has "◆". Predict: 0.5
- `river`: Grace has "△", Rocky has "▽". Predict: 0.5

All equal — picks `apple` with her symbol "✦".

**Grace → Rocky:**
```json
{
  "metadata": {
    "https://example.com/ext/emergent-lang/v1/context": {
      "grace_lex": {"apple": "✦", "dance": "≈", "river": "△"},
      "rocky_lex": {"apple": "○", "dance": "◆", "river": "▽"},
      "round": 1,
      "history": []
    },
    "https://example.com/ext/emergent-lang/v1/message": "✦",
    "https://example.com/ext/emergent-lang/v1/referent": "apple"
  }
}
```

Rocky runs `decide_accept`: no established conflict → **accepts**.
Rocky runs `adopt(rocky_lex, "apple", "✦")`.
History updated: `[{"referent": "apple", "symbol": "✦", "accepted": true, "speaker": "grace"}]`

### Round 2 — Rocky predicts + proposes

Rocky evaluates unresolved: `dance`, `river`.
- `dance`: Rocky has "◆", Grace has "≈". Predict: 0.5
- `river`: Rocky has "▽", Grace has "△". Predict: 0.5

Picks `dance` with "◆".

**Rocky → Grace:**
```json
{
  "metadata": {
    "https://example.com/ext/emergent-lang/v1/context": {
      "grace_lex": {"apple": "✦", "dance": "≈", "river": "△"},
      "rocky_lex": {"apple": "✦", "dance": "◆", "river": "▽"},
      "round": 2,
      "history": [{"referent": "apple", "symbol": "✦", "accepted": true, "speaker": "grace"}]
    },
    "https://example.com/ext/emergent-lang/v1/message": "◆",
    "https://example.com/ext/emergent-lang/v1/referent": "dance"
  }
}
```

Grace: `decide_accept` → accepts. Adopts "◆" for dance.

### Round 3 — Grace proposes river

Only `river` remains unresolved. Grace proposes "△".

Rocky accepts. Alignment = 1.0 → **DONE**.

```json
{
  "message": {
    "parts": [{"text": "done | rounds: 3 | alignment: 100% | grace: {'apple': '✦', 'dance': '◆', 'river': '△'} | rocky: {'apple': '✦', 'dance': '◆', 'river': '△'}"}],
    "metadata": {
      "https://example.com/ext/emergent-lang/v1/context": {
        "grace_lex": {"apple": "✦", "dance": "◆", "river": "△"},
        "rocky_lex": {"apple": "✦", "dance": "◆", "river": "△"},
        "round": 3,
        "history": [
          {"referent": "apple", "symbol": "✦", "accepted": true, "speaker": "grace"},
          {"referent": "dance", "symbol": "◆", "accepted": true, "speaker": "rocky"},
          {"referent": "river", "symbol": "△", "accepted": true, "speaker": "grace"}
        ]
      }
    }
  }
}
```

---

## Scenario 2: Rejection + History avoids repeated failure

Starting state: Rocky has `"fire" → "✦"` established (accepted in history). Grace proposes "✦" for `moon`.

### Round N — Grace proposes "moon = ✦"

Grace predicts: "✦" is in Rocky's lexicon for `fire` → score 0.3 (symbol taken).
But it's the best she has — sends it anyway.

**Grace → Rocky:**
```json
{
  "metadata": {
    "https://example.com/ext/emergent-lang/v1/context": {
      "grace_lex": {"moon": "✦", "fire": "○"},
      "rocky_lex": {"moon": "◆", "fire": "✦"},
      "round": 5,
      "history": [
        {"referent": "fire", "symbol": "✦", "accepted": true, "speaker": "rocky"}
      ]
    },
    "https://example.com/ext/emergent-lang/v1/message": "✦",
    "https://example.com/ext/emergent-lang/v1/referent": "moon"
  }
}
```

Rocky runs `decide_accept`:
- "✦" maps to `fire` in his lexicon
- History shows `fire=✦` was previously accepted → **established**
- **Rejects** to protect the established mapping.

History updated: `[..., {"referent": "moon", "symbol": "✦", "accepted": false, "speaker": "grace"}]`

### Round N+1 — Grace retries with ToM

Grace's `propose_with_tom` checks `predict_acceptance("moon", "✦", rocky_lex, history)`:
- Finds the rejection in history → score **0.0**
- Coins a new symbol via `coin_smart` (avoids "✦" and all rejected symbols)
- Gets "☆" → predict score 0.5

**Grace → Rocky:**
```json
{
  "metadata": {
    "https://example.com/ext/emergent-lang/v1/context": {
      "grace_lex": {"moon": "☆", "fire": "○"},
      "rocky_lex": {"moon": "◆", "fire": "✦"},
      "round": 6,
      "history": [
        {"referent": "fire", "symbol": "✦", "accepted": true, "speaker": "rocky"},
        {"referent": "moon", "symbol": "✦", "accepted": false, "speaker": "grace"}
      ]
    },
    "https://example.com/ext/emergent-lang/v1/message": "☆",
    "https://example.com/ext/emergent-lang/v1/referent": "moon"
  }
}
```

Rocky: "☆" doesn't conflict with anything → **accepts**.

History learned from the rejection and avoided repeating it.

---

## Scenario 3: Prediction avoids conflict entirely

Starting state: Grace has `"star" → "○"`, Rocky has `"wind" → "○"`. Without ToM, Grace might propose "○" for `star` causing a collision.

### Grace's ToM evaluation

```
predict_acceptance("star", "○", rocky_lex, history):
  → "○" is already mapped to "wind" in Rocky's lexicon
  → Score: 0.3 (symbol taken — likely reject)

predict_acceptance("star", "☆", rocky_lex, history):
  → "☆" not in Rocky's lexicon
  → Score: 1.0 (no mapping — will definitely accept)
```

Grace coins "☆" instead of sending "○". Rocky accepts immediately.

**Without ToM**: Grace sends "○" → Rocky adopts but loses `wind=○` → extra round to re-coin wind.
**With ToM**: Grace avoids the conflict entirely → saves 2 rounds.

---

## Scenario 4: Max rounds (timeout)

After 60 rounds with persistent disagreements:

```json
{
  "message": {
    "parts": [{"text": "done | rounds: 60 | alignment: 70% | grace: {...} | rocky: {...}"}],
    "metadata": {
      "https://example.com/ext/emergent-lang/v1/context": {
        "grace_lex": {"apple": "✦", "dance": "≈", "river": "△", ...},
        "rocky_lex": {"apple": "✦", "dance": "≈", "river": "○", ...},
        "round": 60,
        "history": [...]
      }
    }
  }
}
```

Game stops at round 60. History shows which proposals failed and why.

---

## Summary

| Scenario | Rounds | What happens |
|----------|--------|-------------|
| ToM-guided agreement | ~N rounds for N meanings | Predicts acceptance, avoids bad proposals |
| Rejection + history | +1 round per rejection | Learns from failure, never repeats |
| Conflict avoidance | 0 extra rounds | ToM predicts low acceptance, coins alternative |
| Timeout | 60 (max) | Game stops, full history preserved in metadata |
