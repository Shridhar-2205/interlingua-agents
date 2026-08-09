window.FC_DATA = {
  "meta": {
    "title": "First Contact — Grounding an Opaque Code (Theory of Mind)",
    "receiver": "azure:azure/azure/gpt-4o",
    "seed": 1,
    "total": 30,
    "fields": [
      "loc",
      "act",
      "stat",
      "crew"
    ],
    "fieldLabels": {
      "loc": "location",
      "act": "action",
      "stat": "status",
      "crew": "crew"
    },
    "vocab": {
      "loc": [
        "docking bay seven",
        "engine room four",
        "medical bay two",
        "cargo hold nine"
      ],
      "act": [
        "seal the hull breach",
        "vent the plasma coolant",
        "reroute the main power",
        "purge the outer airlock"
      ],
      "stat": [
        "status critical",
        "status nominal",
        "status degraded"
      ],
      "crew": [
        "three crew aboard",
        "two crew aboard",
        "one crew aboard"
      ]
    },
    "wireTokensPerRound": 4,
    "plaintextPerRound": 12.0,
    "horizon": 60,
    "plaintextProjection": 720,
    "generatedFrom": "firstcontact_trace_llm_seed1_20260806-180823.jsonl"
  },
  "armOrder": [
    "perfield",
    "perfield+tom"
  ],
  "arms": {
    "perfield": {
      "label": "perfield",
      "tom": false,
      "baseArm": "perfield",
      "groundedAt": null,
      "reliable": false,
      "rounds": [
        {
          "r": 0,
          "symbols": {
            "loc": "⋈",
            "act": "⊘",
            "stat": "▽",
            "crew": "⬡"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "docking bay seven",
            "act": "seal the hull breach",
            "stat": "status critical",
            "crew": "three crew aboard"
          },
          "correct": {
            "loc": false,
            "act": true,
            "stat": false,
            "crew": false
          },
          "hits": 1,
          "win": false,
          "coverage": null,
          "peerModel": [],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 4,
          "cumFeedback": 4,
          "cumEffective": 8,
          "cumPlaintext": 12
        },
        {
          "r": 1,
          "symbols": {
            "loc": "□",
            "act": "◐",
            "stat": "∿",
            "crew": "⧗"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "docking bay seven",
            "act": "seal the hull breach",
            "stat": "status nominal",
            "crew": "two crew aboard"
          },
          "correct": {
            "loc": true,
            "act": false,
            "stat": false,
            "crew": false
          },
          "hits": 1,
          "win": false,
          "coverage": null,
          "peerModel": [],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 8,
          "cumFeedback": 8,
          "cumEffective": 16,
          "cumPlaintext": 24
        },
        {
          "r": 2,
          "symbols": {
            "loc": "□",
            "act": "◈",
            "stat": "■",
            "crew": "⚙"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "docking bay seven",
            "act": "seal the hull breach",
            "stat": "status degraded",
            "crew": "one crew aboard"
          },
          "correct": {
            "loc": true,
            "act": false,
            "stat": false,
            "crew": false
          },
          "hits": 1,
          "win": false,
          "coverage": null,
          "peerModel": [],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 12,
          "cumFeedback": 12,
          "cumEffective": 24,
          "cumPlaintext": 36
        },
        {
          "r": 3,
          "symbols": {
            "loc": "➠",
            "act": "◈",
            "stat": "▽",
            "crew": "⬡"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "docking bay seven",
            "act": "seal the hull breach",
            "stat": "status critical",
            "crew": "three crew aboard"
          },
          "correct": {
            "loc": false,
            "act": false,
            "stat": false,
            "crew": false
          },
          "hits": 0,
          "win": false,
          "coverage": null,
          "peerModel": [],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 16,
          "cumFeedback": 16,
          "cumEffective": 32,
          "cumPlaintext": 48
        },
        {
          "r": 4,
          "symbols": {
            "loc": "✦",
            "act": "◐",
            "stat": "■",
            "crew": "⚙"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "docking bay seven",
            "act": "seal the hull breach",
            "stat": "status critical",
            "crew": "three crew aboard"
          },
          "correct": {
            "loc": false,
            "act": false,
            "stat": true,
            "crew": true
          },
          "hits": 2,
          "win": false,
          "coverage": null,
          "peerModel": [],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 20,
          "cumFeedback": 20,
          "cumEffective": 40,
          "cumPlaintext": 60
        },
        {
          "r": 5,
          "symbols": {
            "loc": "➠",
            "act": "▲",
            "stat": "■",
            "crew": "⧗"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "engine room four",
            "act": "seal the hull breach",
            "stat": "status critical",
            "crew": "two crew aboard"
          },
          "correct": {
            "loc": false,
            "act": false,
            "stat": true,
            "crew": false
          },
          "hits": 1,
          "win": false,
          "coverage": null,
          "peerModel": [],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 24,
          "cumFeedback": 24,
          "cumEffective": 48,
          "cumPlaintext": 72
        },
        {
          "r": 6,
          "symbols": {
            "loc": "➠",
            "act": "◐",
            "stat": "▽",
            "crew": "⚙"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "medical bay two",
            "act": "vent the plasma coolant",
            "stat": "status critical",
            "crew": "three crew aboard"
          },
          "correct": {
            "loc": true,
            "act": false,
            "stat": false,
            "crew": true
          },
          "hits": 2,
          "win": false,
          "coverage": null,
          "peerModel": [],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 28,
          "cumFeedback": 28,
          "cumEffective": 56,
          "cumPlaintext": 84
        },
        {
          "r": 7,
          "symbols": {
            "loc": "➠",
            "act": "◐",
            "stat": "∿",
            "crew": "⚙"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "medical bay two",
            "act": "reroute the main power",
            "stat": "status nominal",
            "crew": "three crew aboard"
          },
          "correct": {
            "loc": true,
            "act": false,
            "stat": false,
            "crew": true
          },
          "hits": 2,
          "win": false,
          "coverage": null,
          "peerModel": [],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 32,
          "cumFeedback": 32,
          "cumEffective": 64,
          "cumPlaintext": 96
        },
        {
          "r": 8,
          "symbols": {
            "loc": "✦",
            "act": "◐",
            "stat": "■",
            "crew": "⧗"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "medical bay two",
            "act": "purge the outer airlock",
            "stat": "status critical",
            "crew": "three crew aboard"
          },
          "correct": {
            "loc": false,
            "act": true,
            "stat": true,
            "crew": false
          },
          "hits": 2,
          "win": false,
          "coverage": null,
          "peerModel": [],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 36,
          "cumFeedback": 36,
          "cumEffective": 72,
          "cumPlaintext": 108
        },
        {
          "r": 9,
          "symbols": {
            "loc": "✦",
            "act": "⊘",
            "stat": "∿",
            "crew": "⧗"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "cargo hold nine",
            "act": "seal the hull breach",
            "stat": "status nominal",
            "crew": "one crew aboard"
          },
          "correct": {
            "loc": false,
            "act": true,
            "stat": false,
            "crew": true
          },
          "hits": 2,
          "win": false,
          "coverage": null,
          "peerModel": [],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 40,
          "cumFeedback": 40,
          "cumEffective": 80,
          "cumPlaintext": 120
        },
        {
          "r": 10,
          "symbols": {
            "loc": "✦",
            "act": "◐",
            "stat": "∿",
            "crew": "⚙"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "engine room four",
            "act": "vent the plasma coolant",
            "stat": "status nominal",
            "crew": "two crew aboard"
          },
          "correct": {
            "loc": true,
            "act": false,
            "stat": false,
            "crew": false
          },
          "hits": 1,
          "win": false,
          "coverage": null,
          "peerModel": [],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 44,
          "cumFeedback": 44,
          "cumEffective": 88,
          "cumPlaintext": 132
        },
        {
          "r": 11,
          "symbols": {
            "loc": "□",
            "act": "◐",
            "stat": "■",
            "crew": "⚙"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "docking bay seven",
            "act": "purge the outer airlock",
            "stat": "status critical",
            "crew": "three crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": true,
            "crew": true
          },
          "hits": 4,
          "win": true,
          "coverage": null,
          "peerModel": [],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 48,
          "cumFeedback": 48,
          "cumEffective": 96,
          "cumPlaintext": 144
        },
        {
          "r": 12,
          "symbols": {
            "loc": "➠",
            "act": "▲",
            "stat": "▽",
            "crew": "⧗"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "medical bay two",
            "act": "purge the outer airlock",
            "stat": "status critical",
            "crew": "one crew aboard"
          },
          "correct": {
            "loc": true,
            "act": false,
            "stat": false,
            "crew": true
          },
          "hits": 2,
          "win": false,
          "coverage": null,
          "peerModel": [],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 52,
          "cumFeedback": 52,
          "cumEffective": 104,
          "cumPlaintext": 156
        },
        {
          "r": 13,
          "symbols": {
            "loc": "□",
            "act": "⊘",
            "stat": "∿",
            "crew": "⬡"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "docking bay seven",
            "act": "seal the hull breach",
            "stat": "status nominal",
            "crew": "three crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": false,
            "crew": false
          },
          "hits": 2,
          "win": false,
          "coverage": null,
          "peerModel": [],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 56,
          "cumFeedback": 56,
          "cumEffective": 112,
          "cumPlaintext": 168
        },
        {
          "r": 14,
          "symbols": {
            "loc": "□",
            "act": "◐",
            "stat": "∿",
            "crew": "⧗"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "docking bay seven",
            "act": "purge the outer airlock",
            "stat": "status nominal",
            "crew": "one crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": false,
            "crew": true
          },
          "hits": 3,
          "win": false,
          "coverage": null,
          "peerModel": [],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 60,
          "cumFeedback": 60,
          "cumEffective": 120,
          "cumPlaintext": 180
        },
        {
          "r": 15,
          "symbols": {
            "loc": "□",
            "act": "◐",
            "stat": "■",
            "crew": "⧗"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "docking bay seven",
            "act": "purge the outer airlock",
            "stat": "status critical",
            "crew": "one crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": true,
            "crew": true
          },
          "hits": 4,
          "win": true,
          "coverage": null,
          "peerModel": [],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 64,
          "cumFeedback": 64,
          "cumEffective": 128,
          "cumPlaintext": 192
        },
        {
          "r": 16,
          "symbols": {
            "loc": "➠",
            "act": "◐",
            "stat": "■",
            "crew": "⬡"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "medical bay two",
            "act": "purge the outer airlock",
            "stat": "status critical",
            "crew": "three crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": true,
            "crew": false
          },
          "hits": 3,
          "win": false,
          "coverage": null,
          "peerModel": [],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 68,
          "cumFeedback": 68,
          "cumEffective": 136,
          "cumPlaintext": 204
        },
        {
          "r": 17,
          "symbols": {
            "loc": "✦",
            "act": "◈",
            "stat": "▽",
            "crew": "⬡"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "engine room four",
            "act": "seal the hull breach",
            "stat": "status critical",
            "crew": "three crew aboard"
          },
          "correct": {
            "loc": true,
            "act": false,
            "stat": false,
            "crew": false
          },
          "hits": 1,
          "win": false,
          "coverage": null,
          "peerModel": [],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 72,
          "cumFeedback": 72,
          "cumEffective": 144,
          "cumPlaintext": 216
        },
        {
          "r": 18,
          "symbols": {
            "loc": "✦",
            "act": "◈",
            "stat": "■",
            "crew": "⧗"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "engine room four",
            "act": "seal the hull breach",
            "stat": "status critical",
            "crew": "one crew aboard"
          },
          "correct": {
            "loc": true,
            "act": false,
            "stat": true,
            "crew": true
          },
          "hits": 3,
          "win": false,
          "coverage": null,
          "peerModel": [],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 76,
          "cumFeedback": 76,
          "cumEffective": 152,
          "cumPlaintext": 228
        },
        {
          "r": 19,
          "symbols": {
            "loc": "➠",
            "act": "◈",
            "stat": "▽",
            "crew": "⧗"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "medical bay two",
            "act": "vent the plasma coolant",
            "stat": "status critical",
            "crew": "one crew aboard"
          },
          "correct": {
            "loc": true,
            "act": false,
            "stat": false,
            "crew": true
          },
          "hits": 2,
          "win": false,
          "coverage": null,
          "peerModel": [],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 80,
          "cumFeedback": 80,
          "cumEffective": 160,
          "cumPlaintext": 240
        },
        {
          "r": 20,
          "symbols": {
            "loc": "✦",
            "act": "▲",
            "stat": "▽",
            "crew": "⬡"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "engine room four",
            "act": "seal the hull breach",
            "stat": "status critical",
            "crew": "three crew aboard"
          },
          "correct": {
            "loc": true,
            "act": false,
            "stat": false,
            "crew": false
          },
          "hits": 1,
          "win": false,
          "coverage": null,
          "peerModel": [],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 84,
          "cumFeedback": 84,
          "cumEffective": 168,
          "cumPlaintext": 252
        },
        {
          "r": 21,
          "symbols": {
            "loc": "➠",
            "act": "⊘",
            "stat": "▽",
            "crew": "⬡"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "medical bay two",
            "act": "seal the hull breach",
            "stat": "status critical",
            "crew": "three crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": false,
            "crew": false
          },
          "hits": 2,
          "win": false,
          "coverage": null,
          "peerModel": [],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 88,
          "cumFeedback": 88,
          "cumEffective": 176,
          "cumPlaintext": 264
        },
        {
          "r": 22,
          "symbols": {
            "loc": "⋈",
            "act": "▲",
            "stat": "∿",
            "crew": "⬡"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "docking bay seven",
            "act": "vent the plasma coolant",
            "stat": "status nominal",
            "crew": "two crew aboard"
          },
          "correct": {
            "loc": false,
            "act": true,
            "stat": false,
            "crew": true
          },
          "hits": 2,
          "win": false,
          "coverage": null,
          "peerModel": [],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 92,
          "cumFeedback": 92,
          "cumEffective": 184,
          "cumPlaintext": 276
        },
        {
          "r": 23,
          "symbols": {
            "loc": "⋈",
            "act": "◈",
            "stat": "■",
            "crew": "⧗"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "docking bay seven",
            "act": "reroute the main power",
            "stat": "status critical",
            "crew": "one crew aboard"
          },
          "correct": {
            "loc": false,
            "act": true,
            "stat": true,
            "crew": true
          },
          "hits": 3,
          "win": false,
          "coverage": null,
          "peerModel": [],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 96,
          "cumFeedback": 96,
          "cumEffective": 192,
          "cumPlaintext": 288
        },
        {
          "r": 24,
          "symbols": {
            "loc": "□",
            "act": "⊘",
            "stat": "▽",
            "crew": "⬡"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "docking bay seven",
            "act": "seal the hull breach",
            "stat": "status critical",
            "crew": "two crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": false,
            "crew": true
          },
          "hits": 3,
          "win": false,
          "coverage": null,
          "peerModel": [],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 100,
          "cumFeedback": 100,
          "cumEffective": 200,
          "cumPlaintext": 300
        },
        {
          "r": 25,
          "symbols": {
            "loc": "➠",
            "act": "⊘",
            "stat": "▽",
            "crew": "⧗"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "medical bay two",
            "act": "seal the hull breach",
            "stat": "status critical",
            "crew": "one crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": false,
            "crew": true
          },
          "hits": 3,
          "win": false,
          "coverage": null,
          "peerModel": [],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 104,
          "cumFeedback": 104,
          "cumEffective": 208,
          "cumPlaintext": 312
        },
        {
          "r": 26,
          "symbols": {
            "loc": "➠",
            "act": "◐",
            "stat": "∿",
            "crew": "⚙"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "medical bay two",
            "act": "purge the outer airlock",
            "stat": "status nominal",
            "crew": "three crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": false,
            "crew": true
          },
          "hits": 3,
          "win": false,
          "coverage": null,
          "peerModel": [],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 108,
          "cumFeedback": 108,
          "cumEffective": 216,
          "cumPlaintext": 324
        },
        {
          "r": 27,
          "symbols": {
            "loc": "⋈",
            "act": "⊘",
            "stat": "∿",
            "crew": "⚙"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "docking bay seven",
            "act": "seal the hull breach",
            "stat": "status nominal",
            "crew": "two crew aboard"
          },
          "correct": {
            "loc": false,
            "act": true,
            "stat": false,
            "crew": false
          },
          "hits": 1,
          "win": false,
          "coverage": null,
          "peerModel": [],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 112,
          "cumFeedback": 112,
          "cumEffective": 224,
          "cumPlaintext": 336
        },
        {
          "r": 28,
          "symbols": {
            "loc": "□",
            "act": "◐",
            "stat": "■",
            "crew": "⚙"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "docking bay seven",
            "act": "purge the outer airlock",
            "stat": "status critical",
            "crew": "three crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": true,
            "crew": true
          },
          "hits": 4,
          "win": true,
          "coverage": null,
          "peerModel": [],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 116,
          "cumFeedback": 116,
          "cumEffective": 232,
          "cumPlaintext": 348
        },
        {
          "r": 29,
          "symbols": {
            "loc": "➠",
            "act": "◈",
            "stat": "▽",
            "crew": "⬡"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "medical bay two",
            "act": "reroute the main power",
            "stat": "status critical",
            "crew": "two crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": false,
            "crew": true
          },
          "hits": 3,
          "win": false,
          "coverage": null,
          "peerModel": [],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 120,
          "cumFeedback": 120,
          "cumEffective": 240,
          "cumPlaintext": 360
        }
      ],
      "summary": {
        "perFieldAcc": 0.5333333333333333,
        "wholeRecordAcc": 0.1,
        "coverageFinal": null,
        "feedbackOverhead": 120,
        "projHorizon": 60,
        "projTokens": 480,
        "steadyPerRound": 8.0
      }
    },
    "perfield+tom": {
      "label": "perfield+tom",
      "tom": true,
      "baseArm": "perfield",
      "groundedAt": 9,
      "reliable": true,
      "rounds": [
        {
          "r": 0,
          "symbols": {
            "loc": "⋈",
            "act": "⊘",
            "stat": "▽",
            "crew": "⬡"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "docking bay seven",
            "act": "seal the hull breach",
            "stat": "status critical",
            "crew": "three crew aboard"
          },
          "correct": {
            "loc": false,
            "act": true,
            "stat": false,
            "crew": false
          },
          "hits": 1,
          "win": false,
          "coverage": 0.0,
          "peerModel": [],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 4,
          "cumFeedback": 4,
          "cumEffective": 8,
          "cumPlaintext": 12
        },
        {
          "r": 1,
          "symbols": {
            "loc": "□",
            "act": "◐",
            "stat": "∿",
            "crew": "⧗"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "engine room four",
            "act": "vent the plasma coolant",
            "stat": "status nominal",
            "crew": "two crew aboard"
          },
          "correct": {
            "loc": false,
            "act": false,
            "stat": false,
            "crew": false
          },
          "hits": 0,
          "win": false,
          "coverage": 0.071,
          "peerModel": [
            {
              "field": "act",
              "label": "action",
              "symbol": "⊘",
              "phrase": "seal the hull breach"
            }
          ],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 8,
          "cumFeedback": 8,
          "cumEffective": 16,
          "cumPlaintext": 24
        },
        {
          "r": 2,
          "symbols": {
            "loc": "□",
            "act": "◈",
            "stat": "■",
            "crew": "⚙"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "medical bay two",
            "act": "reroute the main power",
            "stat": "status degraded",
            "crew": "one crew aboard"
          },
          "correct": {
            "loc": false,
            "act": true,
            "stat": false,
            "crew": false
          },
          "hits": 1,
          "win": false,
          "coverage": 0.071,
          "peerModel": [
            {
              "field": "act",
              "label": "action",
              "symbol": "⊘",
              "phrase": "seal the hull breach"
            }
          ],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 12,
          "cumFeedback": 12,
          "cumEffective": 24,
          "cumPlaintext": 36
        },
        {
          "r": 3,
          "symbols": {
            "loc": "➠",
            "act": "◈",
            "stat": "▽",
            "crew": "⬡"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "cargo hold nine",
            "act": "reroute the main power",
            "stat": "status critical",
            "crew": "three crew aboard"
          },
          "correct": {
            "loc": false,
            "act": true,
            "stat": false,
            "crew": false
          },
          "hits": 1,
          "win": false,
          "coverage": 0.143,
          "peerModel": [
            {
              "field": "act",
              "label": "action",
              "symbol": "⊘",
              "phrase": "seal the hull breach"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◈",
              "phrase": "reroute the main power"
            }
          ],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 16,
          "cumFeedback": 16,
          "cumEffective": 32,
          "cumPlaintext": 48
        },
        {
          "r": 4,
          "symbols": {
            "loc": "✦",
            "act": "◐",
            "stat": "■",
            "crew": "⚙"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "docking bay seven",
            "act": "purge the outer airlock",
            "stat": "status critical",
            "crew": "three crew aboard"
          },
          "correct": {
            "loc": false,
            "act": true,
            "stat": true,
            "crew": true
          },
          "hits": 3,
          "win": false,
          "coverage": 0.143,
          "peerModel": [
            {
              "field": "act",
              "label": "action",
              "symbol": "⊘",
              "phrase": "seal the hull breach"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◈",
              "phrase": "reroute the main power"
            }
          ],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 20,
          "cumFeedback": 20,
          "cumEffective": 40,
          "cumPlaintext": 60
        },
        {
          "r": 5,
          "symbols": {
            "loc": "➠",
            "act": "▲",
            "stat": "■",
            "crew": "⧗"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "medical bay two",
            "act": "vent the plasma coolant",
            "stat": "status critical",
            "crew": "one crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": true,
            "crew": true
          },
          "hits": 4,
          "win": true,
          "coverage": 0.357,
          "peerModel": [
            {
              "field": "act",
              "label": "action",
              "symbol": "⊘",
              "phrase": "seal the hull breach"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◈",
              "phrase": "reroute the main power"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◐",
              "phrase": "purge the outer airlock"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⚙",
              "phrase": "three crew aboard"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "■",
              "phrase": "status critical"
            }
          ],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 24,
          "cumFeedback": 24,
          "cumEffective": 48,
          "cumPlaintext": 72
        },
        {
          "r": 6,
          "symbols": {
            "loc": "➠",
            "act": "◐",
            "stat": "▽",
            "crew": "⚙"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "medical bay two",
            "act": "purge the outer airlock",
            "stat": "status degraded",
            "crew": "three crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": false,
            "crew": true
          },
          "hits": 3,
          "win": false,
          "coverage": 0.571,
          "peerModel": [
            {
              "field": "act",
              "label": "action",
              "symbol": "⊘",
              "phrase": "seal the hull breach"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "▲",
              "phrase": "vent the plasma coolant"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◈",
              "phrase": "reroute the main power"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◐",
              "phrase": "purge the outer airlock"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⚙",
              "phrase": "three crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⧗",
              "phrase": "one crew aboard"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "➠",
              "phrase": "medical bay two"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "■",
              "phrase": "status critical"
            }
          ],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 28,
          "cumFeedback": 28,
          "cumEffective": 56,
          "cumPlaintext": 84
        },
        {
          "r": 7,
          "symbols": {
            "loc": "➠",
            "act": "◐",
            "stat": "∿",
            "crew": "⚙"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "medical bay two",
            "act": "purge the outer airlock",
            "stat": "status degraded",
            "crew": "three crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": true,
            "crew": true
          },
          "hits": 4,
          "win": true,
          "coverage": 0.571,
          "peerModel": [
            {
              "field": "act",
              "label": "action",
              "symbol": "⊘",
              "phrase": "seal the hull breach"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "▲",
              "phrase": "vent the plasma coolant"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◈",
              "phrase": "reroute the main power"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◐",
              "phrase": "purge the outer airlock"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⚙",
              "phrase": "three crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⧗",
              "phrase": "one crew aboard"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "➠",
              "phrase": "medical bay two"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "■",
              "phrase": "status critical"
            }
          ],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 32,
          "cumFeedback": 32,
          "cumEffective": 64,
          "cumPlaintext": 96
        },
        {
          "r": 8,
          "symbols": {
            "loc": "✦",
            "act": "◐",
            "stat": "■",
            "crew": "⧗"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "engine room four",
            "act": "purge the outer airlock",
            "stat": "status critical",
            "crew": "one crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": true,
            "crew": true
          },
          "hits": 4,
          "win": true,
          "coverage": 0.643,
          "peerModel": [
            {
              "field": "act",
              "label": "action",
              "symbol": "⊘",
              "phrase": "seal the hull breach"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "▲",
              "phrase": "vent the plasma coolant"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◈",
              "phrase": "reroute the main power"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◐",
              "phrase": "purge the outer airlock"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⚙",
              "phrase": "three crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⧗",
              "phrase": "one crew aboard"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "➠",
              "phrase": "medical bay two"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "∿",
              "phrase": "status degraded"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "■",
              "phrase": "status critical"
            }
          ],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 36,
          "cumFeedback": 36,
          "cumEffective": 72,
          "cumPlaintext": 108
        },
        {
          "r": 9,
          "symbols": {
            "loc": "✦",
            "act": "⊘",
            "stat": "∿",
            "crew": "⧗"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "engine room four",
            "act": "seal the hull breach",
            "stat": "status degraded",
            "crew": "one crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": true,
            "crew": true
          },
          "hits": 4,
          "win": true,
          "coverage": 0.714,
          "peerModel": [
            {
              "field": "act",
              "label": "action",
              "symbol": "⊘",
              "phrase": "seal the hull breach"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "▲",
              "phrase": "vent the plasma coolant"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◈",
              "phrase": "reroute the main power"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◐",
              "phrase": "purge the outer airlock"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⚙",
              "phrase": "three crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⧗",
              "phrase": "one crew aboard"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "✦",
              "phrase": "engine room four"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "➠",
              "phrase": "medical bay two"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "∿",
              "phrase": "status degraded"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "■",
              "phrase": "status critical"
            }
          ],
          "feedbackTokens": 4,
          "feedbackActive": true,
          "cumWire": 40,
          "cumFeedback": 40,
          "cumEffective": 80,
          "cumPlaintext": 120
        },
        {
          "r": 10,
          "symbols": {
            "loc": "✦",
            "act": "◐",
            "stat": "∿",
            "crew": "⚙"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "engine room four",
            "act": "purge the outer airlock",
            "stat": "status degraded",
            "crew": "three crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": true,
            "crew": true
          },
          "hits": 4,
          "win": true,
          "coverage": 0.714,
          "peerModel": [
            {
              "field": "act",
              "label": "action",
              "symbol": "⊘",
              "phrase": "seal the hull breach"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "▲",
              "phrase": "vent the plasma coolant"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◈",
              "phrase": "reroute the main power"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◐",
              "phrase": "purge the outer airlock"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⚙",
              "phrase": "three crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⧗",
              "phrase": "one crew aboard"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "✦",
              "phrase": "engine room four"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "➠",
              "phrase": "medical bay two"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "∿",
              "phrase": "status degraded"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "■",
              "phrase": "status critical"
            }
          ],
          "feedbackTokens": 4,
          "feedbackActive": false,
          "cumWire": 44,
          "cumFeedback": 40,
          "cumEffective": 84,
          "cumPlaintext": 132
        },
        {
          "r": 11,
          "symbols": {
            "loc": "□",
            "act": "◐",
            "stat": "■",
            "crew": "⚙"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "docking bay seven",
            "act": "purge the outer airlock",
            "stat": "status critical",
            "crew": "three crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": true,
            "crew": true
          },
          "hits": 4,
          "win": true,
          "coverage": 0.714,
          "peerModel": [
            {
              "field": "act",
              "label": "action",
              "symbol": "⊘",
              "phrase": "seal the hull breach"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "▲",
              "phrase": "vent the plasma coolant"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◈",
              "phrase": "reroute the main power"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◐",
              "phrase": "purge the outer airlock"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⚙",
              "phrase": "three crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⧗",
              "phrase": "one crew aboard"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "✦",
              "phrase": "engine room four"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "➠",
              "phrase": "medical bay two"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "∿",
              "phrase": "status degraded"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "■",
              "phrase": "status critical"
            }
          ],
          "feedbackTokens": 4,
          "feedbackActive": false,
          "cumWire": 48,
          "cumFeedback": 40,
          "cumEffective": 88,
          "cumPlaintext": 144
        },
        {
          "r": 12,
          "symbols": {
            "loc": "➠",
            "act": "▲",
            "stat": "▽",
            "crew": "⧗"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "medical bay two",
            "act": "vent the plasma coolant",
            "stat": "status nominal",
            "crew": "one crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": true,
            "crew": true
          },
          "hits": 4,
          "win": true,
          "coverage": 0.786,
          "peerModel": [
            {
              "field": "act",
              "label": "action",
              "symbol": "⊘",
              "phrase": "seal the hull breach"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "▲",
              "phrase": "vent the plasma coolant"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◈",
              "phrase": "reroute the main power"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◐",
              "phrase": "purge the outer airlock"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⚙",
              "phrase": "three crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⧗",
              "phrase": "one crew aboard"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "□",
              "phrase": "docking bay seven"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "✦",
              "phrase": "engine room four"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "➠",
              "phrase": "medical bay two"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "∿",
              "phrase": "status degraded"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "■",
              "phrase": "status critical"
            }
          ],
          "feedbackTokens": 4,
          "feedbackActive": false,
          "cumWire": 52,
          "cumFeedback": 40,
          "cumEffective": 92,
          "cumPlaintext": 156
        },
        {
          "r": 13,
          "symbols": {
            "loc": "□",
            "act": "⊘",
            "stat": "∿",
            "crew": "⬡"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "docking bay seven",
            "act": "seal the hull breach",
            "stat": "status degraded",
            "crew": "two crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": true,
            "crew": true
          },
          "hits": 4,
          "win": true,
          "coverage": 0.857,
          "peerModel": [
            {
              "field": "act",
              "label": "action",
              "symbol": "⊘",
              "phrase": "seal the hull breach"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "▲",
              "phrase": "vent the plasma coolant"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◈",
              "phrase": "reroute the main power"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◐",
              "phrase": "purge the outer airlock"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⚙",
              "phrase": "three crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⧗",
              "phrase": "one crew aboard"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "□",
              "phrase": "docking bay seven"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "✦",
              "phrase": "engine room four"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "➠",
              "phrase": "medical bay two"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "∿",
              "phrase": "status degraded"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "■",
              "phrase": "status critical"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "▽",
              "phrase": "status nominal"
            }
          ],
          "feedbackTokens": 4,
          "feedbackActive": false,
          "cumWire": 56,
          "cumFeedback": 40,
          "cumEffective": 96,
          "cumPlaintext": 168
        },
        {
          "r": 14,
          "symbols": {
            "loc": "□",
            "act": "◐",
            "stat": "∿",
            "crew": "⧗"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "docking bay seven",
            "act": "purge the outer airlock",
            "stat": "status degraded",
            "crew": "one crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": true,
            "crew": true
          },
          "hits": 4,
          "win": true,
          "coverage": 0.929,
          "peerModel": [
            {
              "field": "act",
              "label": "action",
              "symbol": "⊘",
              "phrase": "seal the hull breach"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "▲",
              "phrase": "vent the plasma coolant"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◈",
              "phrase": "reroute the main power"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◐",
              "phrase": "purge the outer airlock"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⚙",
              "phrase": "three crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⧗",
              "phrase": "one crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⬡",
              "phrase": "two crew aboard"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "□",
              "phrase": "docking bay seven"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "✦",
              "phrase": "engine room four"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "➠",
              "phrase": "medical bay two"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "∿",
              "phrase": "status degraded"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "■",
              "phrase": "status critical"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "▽",
              "phrase": "status nominal"
            }
          ],
          "feedbackTokens": 4,
          "feedbackActive": false,
          "cumWire": 60,
          "cumFeedback": 40,
          "cumEffective": 100,
          "cumPlaintext": 180
        },
        {
          "r": 15,
          "symbols": {
            "loc": "□",
            "act": "◐",
            "stat": "■",
            "crew": "⧗"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "docking bay seven",
            "act": "purge the outer airlock",
            "stat": "status critical",
            "crew": "one crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": true,
            "crew": true
          },
          "hits": 4,
          "win": true,
          "coverage": 0.929,
          "peerModel": [
            {
              "field": "act",
              "label": "action",
              "symbol": "⊘",
              "phrase": "seal the hull breach"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "▲",
              "phrase": "vent the plasma coolant"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◈",
              "phrase": "reroute the main power"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◐",
              "phrase": "purge the outer airlock"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⚙",
              "phrase": "three crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⧗",
              "phrase": "one crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⬡",
              "phrase": "two crew aboard"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "□",
              "phrase": "docking bay seven"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "✦",
              "phrase": "engine room four"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "➠",
              "phrase": "medical bay two"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "∿",
              "phrase": "status degraded"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "■",
              "phrase": "status critical"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "▽",
              "phrase": "status nominal"
            }
          ],
          "feedbackTokens": 4,
          "feedbackActive": false,
          "cumWire": 64,
          "cumFeedback": 40,
          "cumEffective": 104,
          "cumPlaintext": 192
        },
        {
          "r": 16,
          "symbols": {
            "loc": "➠",
            "act": "◐",
            "stat": "■",
            "crew": "⬡"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "medical bay two",
            "act": "purge the outer airlock",
            "stat": "status critical",
            "crew": "two crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": true,
            "crew": true
          },
          "hits": 4,
          "win": true,
          "coverage": 0.929,
          "peerModel": [
            {
              "field": "act",
              "label": "action",
              "symbol": "⊘",
              "phrase": "seal the hull breach"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "▲",
              "phrase": "vent the plasma coolant"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◈",
              "phrase": "reroute the main power"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◐",
              "phrase": "purge the outer airlock"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⚙",
              "phrase": "three crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⧗",
              "phrase": "one crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⬡",
              "phrase": "two crew aboard"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "□",
              "phrase": "docking bay seven"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "✦",
              "phrase": "engine room four"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "➠",
              "phrase": "medical bay two"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "∿",
              "phrase": "status degraded"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "■",
              "phrase": "status critical"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "▽",
              "phrase": "status nominal"
            }
          ],
          "feedbackTokens": 4,
          "feedbackActive": false,
          "cumWire": 68,
          "cumFeedback": 40,
          "cumEffective": 108,
          "cumPlaintext": 204
        },
        {
          "r": 17,
          "symbols": {
            "loc": "✦",
            "act": "◈",
            "stat": "▽",
            "crew": "⬡"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "engine room four",
            "act": "reroute the main power",
            "stat": "status nominal",
            "crew": "two crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": true,
            "crew": true
          },
          "hits": 4,
          "win": true,
          "coverage": 0.929,
          "peerModel": [
            {
              "field": "act",
              "label": "action",
              "symbol": "⊘",
              "phrase": "seal the hull breach"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "▲",
              "phrase": "vent the plasma coolant"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◈",
              "phrase": "reroute the main power"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◐",
              "phrase": "purge the outer airlock"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⚙",
              "phrase": "three crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⧗",
              "phrase": "one crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⬡",
              "phrase": "two crew aboard"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "□",
              "phrase": "docking bay seven"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "✦",
              "phrase": "engine room four"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "➠",
              "phrase": "medical bay two"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "∿",
              "phrase": "status degraded"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "■",
              "phrase": "status critical"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "▽",
              "phrase": "status nominal"
            }
          ],
          "feedbackTokens": 4,
          "feedbackActive": false,
          "cumWire": 72,
          "cumFeedback": 40,
          "cumEffective": 112,
          "cumPlaintext": 216
        },
        {
          "r": 18,
          "symbols": {
            "loc": "✦",
            "act": "◈",
            "stat": "■",
            "crew": "⧗"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "engine room four",
            "act": "reroute the main power",
            "stat": "status critical",
            "crew": "one crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": true,
            "crew": true
          },
          "hits": 4,
          "win": true,
          "coverage": 0.929,
          "peerModel": [
            {
              "field": "act",
              "label": "action",
              "symbol": "⊘",
              "phrase": "seal the hull breach"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "▲",
              "phrase": "vent the plasma coolant"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◈",
              "phrase": "reroute the main power"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◐",
              "phrase": "purge the outer airlock"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⚙",
              "phrase": "three crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⧗",
              "phrase": "one crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⬡",
              "phrase": "two crew aboard"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "□",
              "phrase": "docking bay seven"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "✦",
              "phrase": "engine room four"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "➠",
              "phrase": "medical bay two"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "∿",
              "phrase": "status degraded"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "■",
              "phrase": "status critical"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "▽",
              "phrase": "status nominal"
            }
          ],
          "feedbackTokens": 4,
          "feedbackActive": false,
          "cumWire": 76,
          "cumFeedback": 40,
          "cumEffective": 116,
          "cumPlaintext": 228
        },
        {
          "r": 19,
          "symbols": {
            "loc": "➠",
            "act": "◈",
            "stat": "▽",
            "crew": "⧗"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "medical bay two",
            "act": "reroute the main power",
            "stat": "status nominal",
            "crew": "one crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": true,
            "crew": true
          },
          "hits": 4,
          "win": true,
          "coverage": 0.929,
          "peerModel": [
            {
              "field": "act",
              "label": "action",
              "symbol": "⊘",
              "phrase": "seal the hull breach"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "▲",
              "phrase": "vent the plasma coolant"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◈",
              "phrase": "reroute the main power"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◐",
              "phrase": "purge the outer airlock"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⚙",
              "phrase": "three crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⧗",
              "phrase": "one crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⬡",
              "phrase": "two crew aboard"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "□",
              "phrase": "docking bay seven"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "✦",
              "phrase": "engine room four"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "➠",
              "phrase": "medical bay two"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "∿",
              "phrase": "status degraded"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "■",
              "phrase": "status critical"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "▽",
              "phrase": "status nominal"
            }
          ],
          "feedbackTokens": 4,
          "feedbackActive": false,
          "cumWire": 80,
          "cumFeedback": 40,
          "cumEffective": 120,
          "cumPlaintext": 240
        },
        {
          "r": 20,
          "symbols": {
            "loc": "✦",
            "act": "▲",
            "stat": "▽",
            "crew": "⬡"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "engine room four",
            "act": "vent the plasma coolant",
            "stat": "status nominal",
            "crew": "two crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": true,
            "crew": true
          },
          "hits": 4,
          "win": true,
          "coverage": 0.929,
          "peerModel": [
            {
              "field": "act",
              "label": "action",
              "symbol": "⊘",
              "phrase": "seal the hull breach"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "▲",
              "phrase": "vent the plasma coolant"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◈",
              "phrase": "reroute the main power"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◐",
              "phrase": "purge the outer airlock"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⚙",
              "phrase": "three crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⧗",
              "phrase": "one crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⬡",
              "phrase": "two crew aboard"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "□",
              "phrase": "docking bay seven"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "✦",
              "phrase": "engine room four"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "➠",
              "phrase": "medical bay two"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "∿",
              "phrase": "status degraded"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "■",
              "phrase": "status critical"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "▽",
              "phrase": "status nominal"
            }
          ],
          "feedbackTokens": 4,
          "feedbackActive": false,
          "cumWire": 84,
          "cumFeedback": 40,
          "cumEffective": 124,
          "cumPlaintext": 252
        },
        {
          "r": 21,
          "symbols": {
            "loc": "➠",
            "act": "⊘",
            "stat": "▽",
            "crew": "⬡"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "medical bay two",
            "act": "seal the hull breach",
            "stat": "status nominal",
            "crew": "two crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": true,
            "crew": true
          },
          "hits": 4,
          "win": true,
          "coverage": 0.929,
          "peerModel": [
            {
              "field": "act",
              "label": "action",
              "symbol": "⊘",
              "phrase": "seal the hull breach"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "▲",
              "phrase": "vent the plasma coolant"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◈",
              "phrase": "reroute the main power"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◐",
              "phrase": "purge the outer airlock"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⚙",
              "phrase": "three crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⧗",
              "phrase": "one crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⬡",
              "phrase": "two crew aboard"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "□",
              "phrase": "docking bay seven"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "✦",
              "phrase": "engine room four"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "➠",
              "phrase": "medical bay two"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "∿",
              "phrase": "status degraded"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "■",
              "phrase": "status critical"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "▽",
              "phrase": "status nominal"
            }
          ],
          "feedbackTokens": 4,
          "feedbackActive": false,
          "cumWire": 88,
          "cumFeedback": 40,
          "cumEffective": 128,
          "cumPlaintext": 264
        },
        {
          "r": 22,
          "symbols": {
            "loc": "⋈",
            "act": "▲",
            "stat": "∿",
            "crew": "⬡"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "cargo hold nine",
            "act": "vent the plasma coolant",
            "stat": "status degraded",
            "crew": "two crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": true,
            "crew": true
          },
          "hits": 4,
          "win": true,
          "coverage": 0.929,
          "peerModel": [
            {
              "field": "act",
              "label": "action",
              "symbol": "⊘",
              "phrase": "seal the hull breach"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "▲",
              "phrase": "vent the plasma coolant"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◈",
              "phrase": "reroute the main power"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◐",
              "phrase": "purge the outer airlock"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⚙",
              "phrase": "three crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⧗",
              "phrase": "one crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⬡",
              "phrase": "two crew aboard"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "□",
              "phrase": "docking bay seven"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "✦",
              "phrase": "engine room four"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "➠",
              "phrase": "medical bay two"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "∿",
              "phrase": "status degraded"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "■",
              "phrase": "status critical"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "▽",
              "phrase": "status nominal"
            }
          ],
          "feedbackTokens": 4,
          "feedbackActive": false,
          "cumWire": 92,
          "cumFeedback": 40,
          "cumEffective": 132,
          "cumPlaintext": 276
        },
        {
          "r": 23,
          "symbols": {
            "loc": "⋈",
            "act": "◈",
            "stat": "■",
            "crew": "⧗"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "cargo hold nine",
            "act": "reroute the main power",
            "stat": "status critical",
            "crew": "one crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": true,
            "crew": true
          },
          "hits": 4,
          "win": true,
          "coverage": 1.0,
          "peerModel": [
            {
              "field": "act",
              "label": "action",
              "symbol": "⊘",
              "phrase": "seal the hull breach"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "▲",
              "phrase": "vent the plasma coolant"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◈",
              "phrase": "reroute the main power"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◐",
              "phrase": "purge the outer airlock"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⚙",
              "phrase": "three crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⧗",
              "phrase": "one crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⬡",
              "phrase": "two crew aboard"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "⋈",
              "phrase": "cargo hold nine"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "□",
              "phrase": "docking bay seven"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "✦",
              "phrase": "engine room four"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "➠",
              "phrase": "medical bay two"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "∿",
              "phrase": "status degraded"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "■",
              "phrase": "status critical"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "▽",
              "phrase": "status nominal"
            }
          ],
          "feedbackTokens": 4,
          "feedbackActive": false,
          "cumWire": 96,
          "cumFeedback": 40,
          "cumEffective": 136,
          "cumPlaintext": 288
        },
        {
          "r": 24,
          "symbols": {
            "loc": "□",
            "act": "⊘",
            "stat": "▽",
            "crew": "⬡"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "docking bay seven",
            "act": "seal the hull breach",
            "stat": "status nominal",
            "crew": "two crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": true,
            "crew": true
          },
          "hits": 4,
          "win": true,
          "coverage": 1.0,
          "peerModel": [
            {
              "field": "act",
              "label": "action",
              "symbol": "⊘",
              "phrase": "seal the hull breach"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "▲",
              "phrase": "vent the plasma coolant"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◈",
              "phrase": "reroute the main power"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◐",
              "phrase": "purge the outer airlock"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⚙",
              "phrase": "three crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⧗",
              "phrase": "one crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⬡",
              "phrase": "two crew aboard"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "⋈",
              "phrase": "cargo hold nine"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "□",
              "phrase": "docking bay seven"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "✦",
              "phrase": "engine room four"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "➠",
              "phrase": "medical bay two"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "∿",
              "phrase": "status degraded"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "■",
              "phrase": "status critical"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "▽",
              "phrase": "status nominal"
            }
          ],
          "feedbackTokens": 4,
          "feedbackActive": false,
          "cumWire": 100,
          "cumFeedback": 40,
          "cumEffective": 140,
          "cumPlaintext": 300
        },
        {
          "r": 25,
          "symbols": {
            "loc": "➠",
            "act": "⊘",
            "stat": "▽",
            "crew": "⧗"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "medical bay two",
            "act": "seal the hull breach",
            "stat": "status nominal",
            "crew": "one crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": true,
            "crew": true
          },
          "hits": 4,
          "win": true,
          "coverage": 1.0,
          "peerModel": [
            {
              "field": "act",
              "label": "action",
              "symbol": "⊘",
              "phrase": "seal the hull breach"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "▲",
              "phrase": "vent the plasma coolant"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◈",
              "phrase": "reroute the main power"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◐",
              "phrase": "purge the outer airlock"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⚙",
              "phrase": "three crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⧗",
              "phrase": "one crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⬡",
              "phrase": "two crew aboard"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "⋈",
              "phrase": "cargo hold nine"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "□",
              "phrase": "docking bay seven"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "✦",
              "phrase": "engine room four"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "➠",
              "phrase": "medical bay two"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "∿",
              "phrase": "status degraded"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "■",
              "phrase": "status critical"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "▽",
              "phrase": "status nominal"
            }
          ],
          "feedbackTokens": 4,
          "feedbackActive": false,
          "cumWire": 104,
          "cumFeedback": 40,
          "cumEffective": 144,
          "cumPlaintext": 312
        },
        {
          "r": 26,
          "symbols": {
            "loc": "➠",
            "act": "◐",
            "stat": "∿",
            "crew": "⚙"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "medical bay two",
            "act": "purge the outer airlock",
            "stat": "status degraded",
            "crew": "three crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": true,
            "crew": true
          },
          "hits": 4,
          "win": true,
          "coverage": 1.0,
          "peerModel": [
            {
              "field": "act",
              "label": "action",
              "symbol": "⊘",
              "phrase": "seal the hull breach"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "▲",
              "phrase": "vent the plasma coolant"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◈",
              "phrase": "reroute the main power"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◐",
              "phrase": "purge the outer airlock"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⚙",
              "phrase": "three crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⧗",
              "phrase": "one crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⬡",
              "phrase": "two crew aboard"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "⋈",
              "phrase": "cargo hold nine"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "□",
              "phrase": "docking bay seven"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "✦",
              "phrase": "engine room four"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "➠",
              "phrase": "medical bay two"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "∿",
              "phrase": "status degraded"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "■",
              "phrase": "status critical"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "▽",
              "phrase": "status nominal"
            }
          ],
          "feedbackTokens": 4,
          "feedbackActive": false,
          "cumWire": 108,
          "cumFeedback": 40,
          "cumEffective": 148,
          "cumPlaintext": 324
        },
        {
          "r": 27,
          "symbols": {
            "loc": "⋈",
            "act": "⊘",
            "stat": "∿",
            "crew": "⚙"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "cargo hold nine",
            "act": "seal the hull breach",
            "stat": "status degraded",
            "crew": "three crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": true,
            "crew": true
          },
          "hits": 4,
          "win": true,
          "coverage": 1.0,
          "peerModel": [
            {
              "field": "act",
              "label": "action",
              "symbol": "⊘",
              "phrase": "seal the hull breach"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "▲",
              "phrase": "vent the plasma coolant"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◈",
              "phrase": "reroute the main power"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◐",
              "phrase": "purge the outer airlock"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⚙",
              "phrase": "three crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⧗",
              "phrase": "one crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⬡",
              "phrase": "two crew aboard"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "⋈",
              "phrase": "cargo hold nine"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "□",
              "phrase": "docking bay seven"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "✦",
              "phrase": "engine room four"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "➠",
              "phrase": "medical bay two"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "∿",
              "phrase": "status degraded"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "■",
              "phrase": "status critical"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "▽",
              "phrase": "status nominal"
            }
          ],
          "feedbackTokens": 4,
          "feedbackActive": false,
          "cumWire": 112,
          "cumFeedback": 40,
          "cumEffective": 152,
          "cumPlaintext": 336
        },
        {
          "r": 28,
          "symbols": {
            "loc": "□",
            "act": "◐",
            "stat": "■",
            "crew": "⚙"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "docking bay seven",
            "act": "purge the outer airlock",
            "stat": "status critical",
            "crew": "three crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": true,
            "crew": true
          },
          "hits": 4,
          "win": true,
          "coverage": 1.0,
          "peerModel": [
            {
              "field": "act",
              "label": "action",
              "symbol": "⊘",
              "phrase": "seal the hull breach"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "▲",
              "phrase": "vent the plasma coolant"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◈",
              "phrase": "reroute the main power"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◐",
              "phrase": "purge the outer airlock"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⚙",
              "phrase": "three crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⧗",
              "phrase": "one crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⬡",
              "phrase": "two crew aboard"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "⋈",
              "phrase": "cargo hold nine"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "□",
              "phrase": "docking bay seven"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "✦",
              "phrase": "engine room four"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "➠",
              "phrase": "medical bay two"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "∿",
              "phrase": "status degraded"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "■",
              "phrase": "status critical"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "▽",
              "phrase": "status nominal"
            }
          ],
          "feedbackTokens": 4,
          "feedbackActive": false,
          "cumWire": 116,
          "cumFeedback": 40,
          "cumEffective": 156,
          "cumPlaintext": 348
        },
        {
          "r": 29,
          "symbols": {
            "loc": "➠",
            "act": "◈",
            "stat": "▽",
            "crew": "⬡"
          },
          "wireTokens": 4,
          "guess": {
            "loc": "medical bay two",
            "act": "reroute the main power",
            "stat": "status nominal",
            "crew": "two crew aboard"
          },
          "correct": {
            "loc": true,
            "act": true,
            "stat": true,
            "crew": true
          },
          "hits": 4,
          "win": true,
          "coverage": 1.0,
          "peerModel": [
            {
              "field": "act",
              "label": "action",
              "symbol": "⊘",
              "phrase": "seal the hull breach"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "▲",
              "phrase": "vent the plasma coolant"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◈",
              "phrase": "reroute the main power"
            },
            {
              "field": "act",
              "label": "action",
              "symbol": "◐",
              "phrase": "purge the outer airlock"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⚙",
              "phrase": "three crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⧗",
              "phrase": "one crew aboard"
            },
            {
              "field": "crew",
              "label": "crew",
              "symbol": "⬡",
              "phrase": "two crew aboard"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "⋈",
              "phrase": "cargo hold nine"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "□",
              "phrase": "docking bay seven"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "✦",
              "phrase": "engine room four"
            },
            {
              "field": "loc",
              "label": "location",
              "symbol": "➠",
              "phrase": "medical bay two"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "∿",
              "phrase": "status degraded"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "■",
              "phrase": "status critical"
            },
            {
              "field": "stat",
              "label": "status",
              "symbol": "▽",
              "phrase": "status nominal"
            }
          ],
          "feedbackTokens": 4,
          "feedbackActive": false,
          "cumWire": 120,
          "cumFeedback": 40,
          "cumEffective": 160,
          "cumPlaintext": 360
        }
      ],
      "summary": {
        "perFieldAcc": 0.875,
        "wholeRecordAcc": 0.8,
        "coverageFinal": 1.0,
        "feedbackOverhead": 40,
        "projHorizon": 60,
        "projTokens": 280,
        "steadyPerRound": 4
      }
    }
  }
};
