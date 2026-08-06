window.DEMO_DATA = {
  "meta": {
    "title": "Interlingua — Emergent Compression Protocol",
    "seed": 1,
    "total": 20,
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
    "generatedUtc": "2026-08-06T17:28:40+00:00"
  },
  "rounds": [
    {
      "r": 0,
      "record": {
        "loc": "cargo hold nine",
        "act": "seal the hull breach",
        "stat": "status nominal",
        "crew": "two crew aboard"
      },
      "phase": "plaintext",
      "plaintext": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "phrase": "cargo hold nine",
            "tokens": 3
          },
          {
            "field": "act",
            "label": "action",
            "phrase": "seal the hull breach",
            "tokens": 4
          },
          {
            "field": "stat",
            "label": "status",
            "phrase": "status nominal",
            "tokens": 2
          },
          {
            "field": "crew",
            "label": "crew",
            "phrase": "two crew aboard",
            "tokens": 3
          }
        ],
        "tokens": 12
      },
      "protocol": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "kind": "define",
            "phrase": "cargo hold nine",
            "code": "$1",
            "tokens": 3
          },
          {
            "field": "act",
            "label": "action",
            "kind": "define",
            "phrase": "seal the hull breach",
            "code": "$2",
            "tokens": 4
          },
          {
            "field": "stat",
            "label": "status",
            "kind": "define",
            "phrase": "status nominal",
            "code": "$3",
            "tokens": 2
          },
          {
            "field": "crew",
            "label": "crew",
            "kind": "define",
            "phrase": "two crew aboard",
            "code": "$4",
            "tokens": 3
          }
        ],
        "tokens": 12,
        "newCodes": [
          {
            "code": "$1",
            "phrase": "cargo hold nine",
            "field": "loc",
            "label": "location"
          },
          {
            "code": "$2",
            "phrase": "seal the hull breach",
            "field": "act",
            "label": "action"
          },
          {
            "code": "$3",
            "phrase": "status nominal",
            "field": "stat",
            "label": "status"
          },
          {
            "code": "$4",
            "phrase": "two crew aboard",
            "field": "crew",
            "label": "crew"
          }
        ],
        "defines": 4,
        "refers": 0
      },
      "codebookAfter": [
        {
          "code": "$1",
          "phrase": "cargo hold nine"
        },
        {
          "code": "$2",
          "phrase": "seal the hull breach"
        },
        {
          "code": "$3",
          "phrase": "status nominal"
        },
        {
          "code": "$4",
          "phrase": "two crew aboard"
        }
      ],
      "reconstruction": {
        "loc": "cargo hold nine",
        "act": "seal the hull breach",
        "stat": "status nominal",
        "crew": "two crew aboard"
      },
      "correct": true,
      "cumPlaintext": 12,
      "cumProtocol": 12,
      "savedPct": 0
    },
    {
      "r": 1,
      "record": {
        "loc": "docking bay seven",
        "act": "purge the outer airlock",
        "stat": "status degraded",
        "crew": "one crew aboard"
      },
      "phase": "plaintext",
      "plaintext": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "phrase": "docking bay seven",
            "tokens": 3
          },
          {
            "field": "act",
            "label": "action",
            "phrase": "purge the outer airlock",
            "tokens": 4
          },
          {
            "field": "stat",
            "label": "status",
            "phrase": "status degraded",
            "tokens": 2
          },
          {
            "field": "crew",
            "label": "crew",
            "phrase": "one crew aboard",
            "tokens": 3
          }
        ],
        "tokens": 12
      },
      "protocol": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "kind": "define",
            "phrase": "docking bay seven",
            "code": "$5",
            "tokens": 3
          },
          {
            "field": "act",
            "label": "action",
            "kind": "define",
            "phrase": "purge the outer airlock",
            "code": "$6",
            "tokens": 4
          },
          {
            "field": "stat",
            "label": "status",
            "kind": "define",
            "phrase": "status degraded",
            "code": "$7",
            "tokens": 2
          },
          {
            "field": "crew",
            "label": "crew",
            "kind": "define",
            "phrase": "one crew aboard",
            "code": "$8",
            "tokens": 3
          }
        ],
        "tokens": 12,
        "newCodes": [
          {
            "code": "$5",
            "phrase": "docking bay seven",
            "field": "loc",
            "label": "location"
          },
          {
            "code": "$6",
            "phrase": "purge the outer airlock",
            "field": "act",
            "label": "action"
          },
          {
            "code": "$7",
            "phrase": "status degraded",
            "field": "stat",
            "label": "status"
          },
          {
            "code": "$8",
            "phrase": "one crew aboard",
            "field": "crew",
            "label": "crew"
          }
        ],
        "defines": 4,
        "refers": 0
      },
      "codebookAfter": [
        {
          "code": "$1",
          "phrase": "cargo hold nine"
        },
        {
          "code": "$2",
          "phrase": "seal the hull breach"
        },
        {
          "code": "$3",
          "phrase": "status nominal"
        },
        {
          "code": "$4",
          "phrase": "two crew aboard"
        },
        {
          "code": "$5",
          "phrase": "docking bay seven"
        },
        {
          "code": "$6",
          "phrase": "purge the outer airlock"
        },
        {
          "code": "$7",
          "phrase": "status degraded"
        },
        {
          "code": "$8",
          "phrase": "one crew aboard"
        }
      ],
      "reconstruction": {
        "loc": "docking bay seven",
        "act": "purge the outer airlock",
        "stat": "status degraded",
        "crew": "one crew aboard"
      },
      "correct": true,
      "cumPlaintext": 24,
      "cumProtocol": 24,
      "savedPct": 0
    },
    {
      "r": 2,
      "record": {
        "loc": "docking bay seven",
        "act": "reroute the main power",
        "stat": "status critical",
        "crew": "three crew aboard"
      },
      "phase": "establishing",
      "plaintext": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "phrase": "docking bay seven",
            "tokens": 3
          },
          {
            "field": "act",
            "label": "action",
            "phrase": "reroute the main power",
            "tokens": 4
          },
          {
            "field": "stat",
            "label": "status",
            "phrase": "status critical",
            "tokens": 2
          },
          {
            "field": "crew",
            "label": "crew",
            "phrase": "three crew aboard",
            "tokens": 3
          }
        ],
        "tokens": 12
      },
      "protocol": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "kind": "refer",
            "phrase": "docking bay seven",
            "code": "$5",
            "tokens": 1
          },
          {
            "field": "act",
            "label": "action",
            "kind": "define",
            "phrase": "reroute the main power",
            "code": "$9",
            "tokens": 4
          },
          {
            "field": "stat",
            "label": "status",
            "kind": "define",
            "phrase": "status critical",
            "code": "$10",
            "tokens": 2
          },
          {
            "field": "crew",
            "label": "crew",
            "kind": "define",
            "phrase": "three crew aboard",
            "code": "$11",
            "tokens": 3
          }
        ],
        "tokens": 10,
        "newCodes": [
          {
            "code": "$9",
            "phrase": "reroute the main power",
            "field": "act",
            "label": "action"
          },
          {
            "code": "$10",
            "phrase": "status critical",
            "field": "stat",
            "label": "status"
          },
          {
            "code": "$11",
            "phrase": "three crew aboard",
            "field": "crew",
            "label": "crew"
          }
        ],
        "defines": 3,
        "refers": 1
      },
      "codebookAfter": [
        {
          "code": "$1",
          "phrase": "cargo hold nine"
        },
        {
          "code": "$2",
          "phrase": "seal the hull breach"
        },
        {
          "code": "$3",
          "phrase": "status nominal"
        },
        {
          "code": "$4",
          "phrase": "two crew aboard"
        },
        {
          "code": "$5",
          "phrase": "docking bay seven"
        },
        {
          "code": "$6",
          "phrase": "purge the outer airlock"
        },
        {
          "code": "$7",
          "phrase": "status degraded"
        },
        {
          "code": "$8",
          "phrase": "one crew aboard"
        },
        {
          "code": "$9",
          "phrase": "reroute the main power"
        },
        {
          "code": "$10",
          "phrase": "status critical"
        },
        {
          "code": "$11",
          "phrase": "three crew aboard"
        }
      ],
      "reconstruction": {
        "loc": "docking bay seven",
        "act": "reroute the main power",
        "stat": "status critical",
        "crew": "three crew aboard"
      },
      "correct": true,
      "cumPlaintext": 36,
      "cumProtocol": 34,
      "savedPct": 17
    },
    {
      "r": 3,
      "record": {
        "loc": "medical bay two",
        "act": "reroute the main power",
        "stat": "status nominal",
        "crew": "two crew aboard"
      },
      "phase": "establishing",
      "plaintext": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "phrase": "medical bay two",
            "tokens": 3
          },
          {
            "field": "act",
            "label": "action",
            "phrase": "reroute the main power",
            "tokens": 4
          },
          {
            "field": "stat",
            "label": "status",
            "phrase": "status nominal",
            "tokens": 2
          },
          {
            "field": "crew",
            "label": "crew",
            "phrase": "two crew aboard",
            "tokens": 3
          }
        ],
        "tokens": 12
      },
      "protocol": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "kind": "define",
            "phrase": "medical bay two",
            "code": "$12",
            "tokens": 3
          },
          {
            "field": "act",
            "label": "action",
            "kind": "refer",
            "phrase": "reroute the main power",
            "code": "$9",
            "tokens": 1
          },
          {
            "field": "stat",
            "label": "status",
            "kind": "refer",
            "phrase": "status nominal",
            "code": "$3",
            "tokens": 1
          },
          {
            "field": "crew",
            "label": "crew",
            "kind": "refer",
            "phrase": "two crew aboard",
            "code": "$4",
            "tokens": 1
          }
        ],
        "tokens": 6,
        "newCodes": [
          {
            "code": "$12",
            "phrase": "medical bay two",
            "field": "loc",
            "label": "location"
          }
        ],
        "defines": 1,
        "refers": 3
      },
      "codebookAfter": [
        {
          "code": "$1",
          "phrase": "cargo hold nine"
        },
        {
          "code": "$2",
          "phrase": "seal the hull breach"
        },
        {
          "code": "$3",
          "phrase": "status nominal"
        },
        {
          "code": "$4",
          "phrase": "two crew aboard"
        },
        {
          "code": "$5",
          "phrase": "docking bay seven"
        },
        {
          "code": "$6",
          "phrase": "purge the outer airlock"
        },
        {
          "code": "$7",
          "phrase": "status degraded"
        },
        {
          "code": "$8",
          "phrase": "one crew aboard"
        },
        {
          "code": "$9",
          "phrase": "reroute the main power"
        },
        {
          "code": "$10",
          "phrase": "status critical"
        },
        {
          "code": "$11",
          "phrase": "three crew aboard"
        },
        {
          "code": "$12",
          "phrase": "medical bay two"
        }
      ],
      "reconstruction": {
        "loc": "medical bay two",
        "act": "reroute the main power",
        "stat": "status nominal",
        "crew": "two crew aboard"
      },
      "correct": true,
      "cumPlaintext": 48,
      "cumProtocol": 40,
      "savedPct": 50
    },
    {
      "r": 4,
      "record": {
        "loc": "engine room four",
        "act": "purge the outer airlock",
        "stat": "status critical",
        "crew": "three crew aboard"
      },
      "phase": "establishing",
      "plaintext": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "phrase": "engine room four",
            "tokens": 3
          },
          {
            "field": "act",
            "label": "action",
            "phrase": "purge the outer airlock",
            "tokens": 4
          },
          {
            "field": "stat",
            "label": "status",
            "phrase": "status critical",
            "tokens": 2
          },
          {
            "field": "crew",
            "label": "crew",
            "phrase": "three crew aboard",
            "tokens": 3
          }
        ],
        "tokens": 12
      },
      "protocol": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "kind": "define",
            "phrase": "engine room four",
            "code": "$13",
            "tokens": 3
          },
          {
            "field": "act",
            "label": "action",
            "kind": "refer",
            "phrase": "purge the outer airlock",
            "code": "$6",
            "tokens": 1
          },
          {
            "field": "stat",
            "label": "status",
            "kind": "refer",
            "phrase": "status critical",
            "code": "$10",
            "tokens": 1
          },
          {
            "field": "crew",
            "label": "crew",
            "kind": "refer",
            "phrase": "three crew aboard",
            "code": "$11",
            "tokens": 1
          }
        ],
        "tokens": 6,
        "newCodes": [
          {
            "code": "$13",
            "phrase": "engine room four",
            "field": "loc",
            "label": "location"
          }
        ],
        "defines": 1,
        "refers": 3
      },
      "codebookAfter": [
        {
          "code": "$1",
          "phrase": "cargo hold nine"
        },
        {
          "code": "$2",
          "phrase": "seal the hull breach"
        },
        {
          "code": "$3",
          "phrase": "status nominal"
        },
        {
          "code": "$4",
          "phrase": "two crew aboard"
        },
        {
          "code": "$5",
          "phrase": "docking bay seven"
        },
        {
          "code": "$6",
          "phrase": "purge the outer airlock"
        },
        {
          "code": "$7",
          "phrase": "status degraded"
        },
        {
          "code": "$8",
          "phrase": "one crew aboard"
        },
        {
          "code": "$9",
          "phrase": "reroute the main power"
        },
        {
          "code": "$10",
          "phrase": "status critical"
        },
        {
          "code": "$11",
          "phrase": "three crew aboard"
        },
        {
          "code": "$12",
          "phrase": "medical bay two"
        },
        {
          "code": "$13",
          "phrase": "engine room four"
        }
      ],
      "reconstruction": {
        "loc": "engine room four",
        "act": "purge the outer airlock",
        "stat": "status critical",
        "crew": "three crew aboard"
      },
      "correct": true,
      "cumPlaintext": 60,
      "cumProtocol": 46,
      "savedPct": 50
    },
    {
      "r": 5,
      "record": {
        "loc": "medical bay two",
        "act": "vent the plasma coolant",
        "stat": "status critical",
        "crew": "one crew aboard"
      },
      "phase": "establishing",
      "plaintext": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "phrase": "medical bay two",
            "tokens": 3
          },
          {
            "field": "act",
            "label": "action",
            "phrase": "vent the plasma coolant",
            "tokens": 4
          },
          {
            "field": "stat",
            "label": "status",
            "phrase": "status critical",
            "tokens": 2
          },
          {
            "field": "crew",
            "label": "crew",
            "phrase": "one crew aboard",
            "tokens": 3
          }
        ],
        "tokens": 12
      },
      "protocol": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "kind": "refer",
            "phrase": "medical bay two",
            "code": "$12",
            "tokens": 1
          },
          {
            "field": "act",
            "label": "action",
            "kind": "define",
            "phrase": "vent the plasma coolant",
            "code": "$14",
            "tokens": 4
          },
          {
            "field": "stat",
            "label": "status",
            "kind": "refer",
            "phrase": "status critical",
            "code": "$10",
            "tokens": 1
          },
          {
            "field": "crew",
            "label": "crew",
            "kind": "refer",
            "phrase": "one crew aboard",
            "code": "$8",
            "tokens": 1
          }
        ],
        "tokens": 7,
        "newCodes": [
          {
            "code": "$14",
            "phrase": "vent the plasma coolant",
            "field": "act",
            "label": "action"
          }
        ],
        "defines": 1,
        "refers": 3
      },
      "codebookAfter": [
        {
          "code": "$1",
          "phrase": "cargo hold nine"
        },
        {
          "code": "$2",
          "phrase": "seal the hull breach"
        },
        {
          "code": "$3",
          "phrase": "status nominal"
        },
        {
          "code": "$4",
          "phrase": "two crew aboard"
        },
        {
          "code": "$5",
          "phrase": "docking bay seven"
        },
        {
          "code": "$6",
          "phrase": "purge the outer airlock"
        },
        {
          "code": "$7",
          "phrase": "status degraded"
        },
        {
          "code": "$8",
          "phrase": "one crew aboard"
        },
        {
          "code": "$9",
          "phrase": "reroute the main power"
        },
        {
          "code": "$10",
          "phrase": "status critical"
        },
        {
          "code": "$11",
          "phrase": "three crew aboard"
        },
        {
          "code": "$12",
          "phrase": "medical bay two"
        },
        {
          "code": "$13",
          "phrase": "engine room four"
        },
        {
          "code": "$14",
          "phrase": "vent the plasma coolant"
        }
      ],
      "reconstruction": {
        "loc": "medical bay two",
        "act": "vent the plasma coolant",
        "stat": "status critical",
        "crew": "one crew aboard"
      },
      "correct": true,
      "cumPlaintext": 72,
      "cumProtocol": 53,
      "savedPct": 42
    },
    {
      "r": 6,
      "record": {
        "loc": "medical bay two",
        "act": "purge the outer airlock",
        "stat": "status nominal",
        "crew": "three crew aboard"
      },
      "phase": "emerged",
      "plaintext": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "phrase": "medical bay two",
            "tokens": 3
          },
          {
            "field": "act",
            "label": "action",
            "phrase": "purge the outer airlock",
            "tokens": 4
          },
          {
            "field": "stat",
            "label": "status",
            "phrase": "status nominal",
            "tokens": 2
          },
          {
            "field": "crew",
            "label": "crew",
            "phrase": "three crew aboard",
            "tokens": 3
          }
        ],
        "tokens": 12
      },
      "protocol": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "kind": "refer",
            "phrase": "medical bay two",
            "code": "$12",
            "tokens": 1
          },
          {
            "field": "act",
            "label": "action",
            "kind": "refer",
            "phrase": "purge the outer airlock",
            "code": "$6",
            "tokens": 1
          },
          {
            "field": "stat",
            "label": "status",
            "kind": "refer",
            "phrase": "status nominal",
            "code": "$3",
            "tokens": 1
          },
          {
            "field": "crew",
            "label": "crew",
            "kind": "refer",
            "phrase": "three crew aboard",
            "code": "$11",
            "tokens": 1
          }
        ],
        "tokens": 4,
        "newCodes": [],
        "defines": 0,
        "refers": 4
      },
      "codebookAfter": [
        {
          "code": "$1",
          "phrase": "cargo hold nine"
        },
        {
          "code": "$2",
          "phrase": "seal the hull breach"
        },
        {
          "code": "$3",
          "phrase": "status nominal"
        },
        {
          "code": "$4",
          "phrase": "two crew aboard"
        },
        {
          "code": "$5",
          "phrase": "docking bay seven"
        },
        {
          "code": "$6",
          "phrase": "purge the outer airlock"
        },
        {
          "code": "$7",
          "phrase": "status degraded"
        },
        {
          "code": "$8",
          "phrase": "one crew aboard"
        },
        {
          "code": "$9",
          "phrase": "reroute the main power"
        },
        {
          "code": "$10",
          "phrase": "status critical"
        },
        {
          "code": "$11",
          "phrase": "three crew aboard"
        },
        {
          "code": "$12",
          "phrase": "medical bay two"
        },
        {
          "code": "$13",
          "phrase": "engine room four"
        },
        {
          "code": "$14",
          "phrase": "vent the plasma coolant"
        }
      ],
      "reconstruction": {
        "loc": "medical bay two",
        "act": "purge the outer airlock",
        "stat": "status nominal",
        "crew": "three crew aboard"
      },
      "correct": true,
      "cumPlaintext": 84,
      "cumProtocol": 57,
      "savedPct": 67
    },
    {
      "r": 7,
      "record": {
        "loc": "medical bay two",
        "act": "purge the outer airlock",
        "stat": "status degraded",
        "crew": "three crew aboard"
      },
      "phase": "emerged",
      "plaintext": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "phrase": "medical bay two",
            "tokens": 3
          },
          {
            "field": "act",
            "label": "action",
            "phrase": "purge the outer airlock",
            "tokens": 4
          },
          {
            "field": "stat",
            "label": "status",
            "phrase": "status degraded",
            "tokens": 2
          },
          {
            "field": "crew",
            "label": "crew",
            "phrase": "three crew aboard",
            "tokens": 3
          }
        ],
        "tokens": 12
      },
      "protocol": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "kind": "refer",
            "phrase": "medical bay two",
            "code": "$12",
            "tokens": 1
          },
          {
            "field": "act",
            "label": "action",
            "kind": "refer",
            "phrase": "purge the outer airlock",
            "code": "$6",
            "tokens": 1
          },
          {
            "field": "stat",
            "label": "status",
            "kind": "refer",
            "phrase": "status degraded",
            "code": "$7",
            "tokens": 1
          },
          {
            "field": "crew",
            "label": "crew",
            "kind": "refer",
            "phrase": "three crew aboard",
            "code": "$11",
            "tokens": 1
          }
        ],
        "tokens": 4,
        "newCodes": [],
        "defines": 0,
        "refers": 4
      },
      "codebookAfter": [
        {
          "code": "$1",
          "phrase": "cargo hold nine"
        },
        {
          "code": "$2",
          "phrase": "seal the hull breach"
        },
        {
          "code": "$3",
          "phrase": "status nominal"
        },
        {
          "code": "$4",
          "phrase": "two crew aboard"
        },
        {
          "code": "$5",
          "phrase": "docking bay seven"
        },
        {
          "code": "$6",
          "phrase": "purge the outer airlock"
        },
        {
          "code": "$7",
          "phrase": "status degraded"
        },
        {
          "code": "$8",
          "phrase": "one crew aboard"
        },
        {
          "code": "$9",
          "phrase": "reroute the main power"
        },
        {
          "code": "$10",
          "phrase": "status critical"
        },
        {
          "code": "$11",
          "phrase": "three crew aboard"
        },
        {
          "code": "$12",
          "phrase": "medical bay two"
        },
        {
          "code": "$13",
          "phrase": "engine room four"
        },
        {
          "code": "$14",
          "phrase": "vent the plasma coolant"
        }
      ],
      "reconstruction": {
        "loc": "medical bay two",
        "act": "purge the outer airlock",
        "stat": "status degraded",
        "crew": "three crew aboard"
      },
      "correct": true,
      "cumPlaintext": 96,
      "cumProtocol": 61,
      "savedPct": 67
    },
    {
      "r": 8,
      "record": {
        "loc": "engine room four",
        "act": "purge the outer airlock",
        "stat": "status critical",
        "crew": "one crew aboard"
      },
      "phase": "emerged",
      "plaintext": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "phrase": "engine room four",
            "tokens": 3
          },
          {
            "field": "act",
            "label": "action",
            "phrase": "purge the outer airlock",
            "tokens": 4
          },
          {
            "field": "stat",
            "label": "status",
            "phrase": "status critical",
            "tokens": 2
          },
          {
            "field": "crew",
            "label": "crew",
            "phrase": "one crew aboard",
            "tokens": 3
          }
        ],
        "tokens": 12
      },
      "protocol": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "kind": "refer",
            "phrase": "engine room four",
            "code": "$13",
            "tokens": 1
          },
          {
            "field": "act",
            "label": "action",
            "kind": "refer",
            "phrase": "purge the outer airlock",
            "code": "$6",
            "tokens": 1
          },
          {
            "field": "stat",
            "label": "status",
            "kind": "refer",
            "phrase": "status critical",
            "code": "$10",
            "tokens": 1
          },
          {
            "field": "crew",
            "label": "crew",
            "kind": "refer",
            "phrase": "one crew aboard",
            "code": "$8",
            "tokens": 1
          }
        ],
        "tokens": 4,
        "newCodes": [],
        "defines": 0,
        "refers": 4
      },
      "codebookAfter": [
        {
          "code": "$1",
          "phrase": "cargo hold nine"
        },
        {
          "code": "$2",
          "phrase": "seal the hull breach"
        },
        {
          "code": "$3",
          "phrase": "status nominal"
        },
        {
          "code": "$4",
          "phrase": "two crew aboard"
        },
        {
          "code": "$5",
          "phrase": "docking bay seven"
        },
        {
          "code": "$6",
          "phrase": "purge the outer airlock"
        },
        {
          "code": "$7",
          "phrase": "status degraded"
        },
        {
          "code": "$8",
          "phrase": "one crew aboard"
        },
        {
          "code": "$9",
          "phrase": "reroute the main power"
        },
        {
          "code": "$10",
          "phrase": "status critical"
        },
        {
          "code": "$11",
          "phrase": "three crew aboard"
        },
        {
          "code": "$12",
          "phrase": "medical bay two"
        },
        {
          "code": "$13",
          "phrase": "engine room four"
        },
        {
          "code": "$14",
          "phrase": "vent the plasma coolant"
        }
      ],
      "reconstruction": {
        "loc": "engine room four",
        "act": "purge the outer airlock",
        "stat": "status critical",
        "crew": "one crew aboard"
      },
      "correct": true,
      "cumPlaintext": 108,
      "cumProtocol": 65,
      "savedPct": 67
    },
    {
      "r": 9,
      "record": {
        "loc": "engine room four",
        "act": "seal the hull breach",
        "stat": "status degraded",
        "crew": "one crew aboard"
      },
      "phase": "emerged",
      "plaintext": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "phrase": "engine room four",
            "tokens": 3
          },
          {
            "field": "act",
            "label": "action",
            "phrase": "seal the hull breach",
            "tokens": 4
          },
          {
            "field": "stat",
            "label": "status",
            "phrase": "status degraded",
            "tokens": 2
          },
          {
            "field": "crew",
            "label": "crew",
            "phrase": "one crew aboard",
            "tokens": 3
          }
        ],
        "tokens": 12
      },
      "protocol": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "kind": "refer",
            "phrase": "engine room four",
            "code": "$13",
            "tokens": 1
          },
          {
            "field": "act",
            "label": "action",
            "kind": "refer",
            "phrase": "seal the hull breach",
            "code": "$2",
            "tokens": 1
          },
          {
            "field": "stat",
            "label": "status",
            "kind": "refer",
            "phrase": "status degraded",
            "code": "$7",
            "tokens": 1
          },
          {
            "field": "crew",
            "label": "crew",
            "kind": "refer",
            "phrase": "one crew aboard",
            "code": "$8",
            "tokens": 1
          }
        ],
        "tokens": 4,
        "newCodes": [],
        "defines": 0,
        "refers": 4
      },
      "codebookAfter": [
        {
          "code": "$1",
          "phrase": "cargo hold nine"
        },
        {
          "code": "$2",
          "phrase": "seal the hull breach"
        },
        {
          "code": "$3",
          "phrase": "status nominal"
        },
        {
          "code": "$4",
          "phrase": "two crew aboard"
        },
        {
          "code": "$5",
          "phrase": "docking bay seven"
        },
        {
          "code": "$6",
          "phrase": "purge the outer airlock"
        },
        {
          "code": "$7",
          "phrase": "status degraded"
        },
        {
          "code": "$8",
          "phrase": "one crew aboard"
        },
        {
          "code": "$9",
          "phrase": "reroute the main power"
        },
        {
          "code": "$10",
          "phrase": "status critical"
        },
        {
          "code": "$11",
          "phrase": "three crew aboard"
        },
        {
          "code": "$12",
          "phrase": "medical bay two"
        },
        {
          "code": "$13",
          "phrase": "engine room four"
        },
        {
          "code": "$14",
          "phrase": "vent the plasma coolant"
        }
      ],
      "reconstruction": {
        "loc": "engine room four",
        "act": "seal the hull breach",
        "stat": "status degraded",
        "crew": "one crew aboard"
      },
      "correct": true,
      "cumPlaintext": 120,
      "cumProtocol": 69,
      "savedPct": 67
    },
    {
      "r": 10,
      "record": {
        "loc": "engine room four",
        "act": "purge the outer airlock",
        "stat": "status degraded",
        "crew": "three crew aboard"
      },
      "phase": "emerged",
      "plaintext": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "phrase": "engine room four",
            "tokens": 3
          },
          {
            "field": "act",
            "label": "action",
            "phrase": "purge the outer airlock",
            "tokens": 4
          },
          {
            "field": "stat",
            "label": "status",
            "phrase": "status degraded",
            "tokens": 2
          },
          {
            "field": "crew",
            "label": "crew",
            "phrase": "three crew aboard",
            "tokens": 3
          }
        ],
        "tokens": 12
      },
      "protocol": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "kind": "refer",
            "phrase": "engine room four",
            "code": "$13",
            "tokens": 1
          },
          {
            "field": "act",
            "label": "action",
            "kind": "refer",
            "phrase": "purge the outer airlock",
            "code": "$6",
            "tokens": 1
          },
          {
            "field": "stat",
            "label": "status",
            "kind": "refer",
            "phrase": "status degraded",
            "code": "$7",
            "tokens": 1
          },
          {
            "field": "crew",
            "label": "crew",
            "kind": "refer",
            "phrase": "three crew aboard",
            "code": "$11",
            "tokens": 1
          }
        ],
        "tokens": 4,
        "newCodes": [],
        "defines": 0,
        "refers": 4
      },
      "codebookAfter": [
        {
          "code": "$1",
          "phrase": "cargo hold nine"
        },
        {
          "code": "$2",
          "phrase": "seal the hull breach"
        },
        {
          "code": "$3",
          "phrase": "status nominal"
        },
        {
          "code": "$4",
          "phrase": "two crew aboard"
        },
        {
          "code": "$5",
          "phrase": "docking bay seven"
        },
        {
          "code": "$6",
          "phrase": "purge the outer airlock"
        },
        {
          "code": "$7",
          "phrase": "status degraded"
        },
        {
          "code": "$8",
          "phrase": "one crew aboard"
        },
        {
          "code": "$9",
          "phrase": "reroute the main power"
        },
        {
          "code": "$10",
          "phrase": "status critical"
        },
        {
          "code": "$11",
          "phrase": "three crew aboard"
        },
        {
          "code": "$12",
          "phrase": "medical bay two"
        },
        {
          "code": "$13",
          "phrase": "engine room four"
        },
        {
          "code": "$14",
          "phrase": "vent the plasma coolant"
        }
      ],
      "reconstruction": {
        "loc": "engine room four",
        "act": "purge the outer airlock",
        "stat": "status degraded",
        "crew": "three crew aboard"
      },
      "correct": true,
      "cumPlaintext": 132,
      "cumProtocol": 73,
      "savedPct": 67
    },
    {
      "r": 11,
      "record": {
        "loc": "docking bay seven",
        "act": "purge the outer airlock",
        "stat": "status critical",
        "crew": "three crew aboard"
      },
      "phase": "emerged",
      "plaintext": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "phrase": "docking bay seven",
            "tokens": 3
          },
          {
            "field": "act",
            "label": "action",
            "phrase": "purge the outer airlock",
            "tokens": 4
          },
          {
            "field": "stat",
            "label": "status",
            "phrase": "status critical",
            "tokens": 2
          },
          {
            "field": "crew",
            "label": "crew",
            "phrase": "three crew aboard",
            "tokens": 3
          }
        ],
        "tokens": 12
      },
      "protocol": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "kind": "refer",
            "phrase": "docking bay seven",
            "code": "$5",
            "tokens": 1
          },
          {
            "field": "act",
            "label": "action",
            "kind": "refer",
            "phrase": "purge the outer airlock",
            "code": "$6",
            "tokens": 1
          },
          {
            "field": "stat",
            "label": "status",
            "kind": "refer",
            "phrase": "status critical",
            "code": "$10",
            "tokens": 1
          },
          {
            "field": "crew",
            "label": "crew",
            "kind": "refer",
            "phrase": "three crew aboard",
            "code": "$11",
            "tokens": 1
          }
        ],
        "tokens": 4,
        "newCodes": [],
        "defines": 0,
        "refers": 4
      },
      "codebookAfter": [
        {
          "code": "$1",
          "phrase": "cargo hold nine"
        },
        {
          "code": "$2",
          "phrase": "seal the hull breach"
        },
        {
          "code": "$3",
          "phrase": "status nominal"
        },
        {
          "code": "$4",
          "phrase": "two crew aboard"
        },
        {
          "code": "$5",
          "phrase": "docking bay seven"
        },
        {
          "code": "$6",
          "phrase": "purge the outer airlock"
        },
        {
          "code": "$7",
          "phrase": "status degraded"
        },
        {
          "code": "$8",
          "phrase": "one crew aboard"
        },
        {
          "code": "$9",
          "phrase": "reroute the main power"
        },
        {
          "code": "$10",
          "phrase": "status critical"
        },
        {
          "code": "$11",
          "phrase": "three crew aboard"
        },
        {
          "code": "$12",
          "phrase": "medical bay two"
        },
        {
          "code": "$13",
          "phrase": "engine room four"
        },
        {
          "code": "$14",
          "phrase": "vent the plasma coolant"
        }
      ],
      "reconstruction": {
        "loc": "docking bay seven",
        "act": "purge the outer airlock",
        "stat": "status critical",
        "crew": "three crew aboard"
      },
      "correct": true,
      "cumPlaintext": 144,
      "cumProtocol": 77,
      "savedPct": 67
    },
    {
      "r": 12,
      "record": {
        "loc": "medical bay two",
        "act": "vent the plasma coolant",
        "stat": "status nominal",
        "crew": "one crew aboard"
      },
      "phase": "emerged",
      "plaintext": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "phrase": "medical bay two",
            "tokens": 3
          },
          {
            "field": "act",
            "label": "action",
            "phrase": "vent the plasma coolant",
            "tokens": 4
          },
          {
            "field": "stat",
            "label": "status",
            "phrase": "status nominal",
            "tokens": 2
          },
          {
            "field": "crew",
            "label": "crew",
            "phrase": "one crew aboard",
            "tokens": 3
          }
        ],
        "tokens": 12
      },
      "protocol": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "kind": "refer",
            "phrase": "medical bay two",
            "code": "$12",
            "tokens": 1
          },
          {
            "field": "act",
            "label": "action",
            "kind": "refer",
            "phrase": "vent the plasma coolant",
            "code": "$14",
            "tokens": 1
          },
          {
            "field": "stat",
            "label": "status",
            "kind": "refer",
            "phrase": "status nominal",
            "code": "$3",
            "tokens": 1
          },
          {
            "field": "crew",
            "label": "crew",
            "kind": "refer",
            "phrase": "one crew aboard",
            "code": "$8",
            "tokens": 1
          }
        ],
        "tokens": 4,
        "newCodes": [],
        "defines": 0,
        "refers": 4
      },
      "codebookAfter": [
        {
          "code": "$1",
          "phrase": "cargo hold nine"
        },
        {
          "code": "$2",
          "phrase": "seal the hull breach"
        },
        {
          "code": "$3",
          "phrase": "status nominal"
        },
        {
          "code": "$4",
          "phrase": "two crew aboard"
        },
        {
          "code": "$5",
          "phrase": "docking bay seven"
        },
        {
          "code": "$6",
          "phrase": "purge the outer airlock"
        },
        {
          "code": "$7",
          "phrase": "status degraded"
        },
        {
          "code": "$8",
          "phrase": "one crew aboard"
        },
        {
          "code": "$9",
          "phrase": "reroute the main power"
        },
        {
          "code": "$10",
          "phrase": "status critical"
        },
        {
          "code": "$11",
          "phrase": "three crew aboard"
        },
        {
          "code": "$12",
          "phrase": "medical bay two"
        },
        {
          "code": "$13",
          "phrase": "engine room four"
        },
        {
          "code": "$14",
          "phrase": "vent the plasma coolant"
        }
      ],
      "reconstruction": {
        "loc": "medical bay two",
        "act": "vent the plasma coolant",
        "stat": "status nominal",
        "crew": "one crew aboard"
      },
      "correct": true,
      "cumPlaintext": 156,
      "cumProtocol": 81,
      "savedPct": 67
    },
    {
      "r": 13,
      "record": {
        "loc": "docking bay seven",
        "act": "seal the hull breach",
        "stat": "status degraded",
        "crew": "two crew aboard"
      },
      "phase": "emerged",
      "plaintext": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "phrase": "docking bay seven",
            "tokens": 3
          },
          {
            "field": "act",
            "label": "action",
            "phrase": "seal the hull breach",
            "tokens": 4
          },
          {
            "field": "stat",
            "label": "status",
            "phrase": "status degraded",
            "tokens": 2
          },
          {
            "field": "crew",
            "label": "crew",
            "phrase": "two crew aboard",
            "tokens": 3
          }
        ],
        "tokens": 12
      },
      "protocol": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "kind": "refer",
            "phrase": "docking bay seven",
            "code": "$5",
            "tokens": 1
          },
          {
            "field": "act",
            "label": "action",
            "kind": "refer",
            "phrase": "seal the hull breach",
            "code": "$2",
            "tokens": 1
          },
          {
            "field": "stat",
            "label": "status",
            "kind": "refer",
            "phrase": "status degraded",
            "code": "$7",
            "tokens": 1
          },
          {
            "field": "crew",
            "label": "crew",
            "kind": "refer",
            "phrase": "two crew aboard",
            "code": "$4",
            "tokens": 1
          }
        ],
        "tokens": 4,
        "newCodes": [],
        "defines": 0,
        "refers": 4
      },
      "codebookAfter": [
        {
          "code": "$1",
          "phrase": "cargo hold nine"
        },
        {
          "code": "$2",
          "phrase": "seal the hull breach"
        },
        {
          "code": "$3",
          "phrase": "status nominal"
        },
        {
          "code": "$4",
          "phrase": "two crew aboard"
        },
        {
          "code": "$5",
          "phrase": "docking bay seven"
        },
        {
          "code": "$6",
          "phrase": "purge the outer airlock"
        },
        {
          "code": "$7",
          "phrase": "status degraded"
        },
        {
          "code": "$8",
          "phrase": "one crew aboard"
        },
        {
          "code": "$9",
          "phrase": "reroute the main power"
        },
        {
          "code": "$10",
          "phrase": "status critical"
        },
        {
          "code": "$11",
          "phrase": "three crew aboard"
        },
        {
          "code": "$12",
          "phrase": "medical bay two"
        },
        {
          "code": "$13",
          "phrase": "engine room four"
        },
        {
          "code": "$14",
          "phrase": "vent the plasma coolant"
        }
      ],
      "reconstruction": {
        "loc": "docking bay seven",
        "act": "seal the hull breach",
        "stat": "status degraded",
        "crew": "two crew aboard"
      },
      "correct": true,
      "cumPlaintext": 168,
      "cumProtocol": 85,
      "savedPct": 67
    },
    {
      "r": 14,
      "record": {
        "loc": "docking bay seven",
        "act": "purge the outer airlock",
        "stat": "status degraded",
        "crew": "one crew aboard"
      },
      "phase": "emerged",
      "plaintext": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "phrase": "docking bay seven",
            "tokens": 3
          },
          {
            "field": "act",
            "label": "action",
            "phrase": "purge the outer airlock",
            "tokens": 4
          },
          {
            "field": "stat",
            "label": "status",
            "phrase": "status degraded",
            "tokens": 2
          },
          {
            "field": "crew",
            "label": "crew",
            "phrase": "one crew aboard",
            "tokens": 3
          }
        ],
        "tokens": 12
      },
      "protocol": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "kind": "refer",
            "phrase": "docking bay seven",
            "code": "$5",
            "tokens": 1
          },
          {
            "field": "act",
            "label": "action",
            "kind": "refer",
            "phrase": "purge the outer airlock",
            "code": "$6",
            "tokens": 1
          },
          {
            "field": "stat",
            "label": "status",
            "kind": "refer",
            "phrase": "status degraded",
            "code": "$7",
            "tokens": 1
          },
          {
            "field": "crew",
            "label": "crew",
            "kind": "refer",
            "phrase": "one crew aboard",
            "code": "$8",
            "tokens": 1
          }
        ],
        "tokens": 4,
        "newCodes": [],
        "defines": 0,
        "refers": 4
      },
      "codebookAfter": [
        {
          "code": "$1",
          "phrase": "cargo hold nine"
        },
        {
          "code": "$2",
          "phrase": "seal the hull breach"
        },
        {
          "code": "$3",
          "phrase": "status nominal"
        },
        {
          "code": "$4",
          "phrase": "two crew aboard"
        },
        {
          "code": "$5",
          "phrase": "docking bay seven"
        },
        {
          "code": "$6",
          "phrase": "purge the outer airlock"
        },
        {
          "code": "$7",
          "phrase": "status degraded"
        },
        {
          "code": "$8",
          "phrase": "one crew aboard"
        },
        {
          "code": "$9",
          "phrase": "reroute the main power"
        },
        {
          "code": "$10",
          "phrase": "status critical"
        },
        {
          "code": "$11",
          "phrase": "three crew aboard"
        },
        {
          "code": "$12",
          "phrase": "medical bay two"
        },
        {
          "code": "$13",
          "phrase": "engine room four"
        },
        {
          "code": "$14",
          "phrase": "vent the plasma coolant"
        }
      ],
      "reconstruction": {
        "loc": "docking bay seven",
        "act": "purge the outer airlock",
        "stat": "status degraded",
        "crew": "one crew aboard"
      },
      "correct": true,
      "cumPlaintext": 180,
      "cumProtocol": 89,
      "savedPct": 67
    },
    {
      "r": 15,
      "record": {
        "loc": "docking bay seven",
        "act": "purge the outer airlock",
        "stat": "status critical",
        "crew": "one crew aboard"
      },
      "phase": "emerged",
      "plaintext": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "phrase": "docking bay seven",
            "tokens": 3
          },
          {
            "field": "act",
            "label": "action",
            "phrase": "purge the outer airlock",
            "tokens": 4
          },
          {
            "field": "stat",
            "label": "status",
            "phrase": "status critical",
            "tokens": 2
          },
          {
            "field": "crew",
            "label": "crew",
            "phrase": "one crew aboard",
            "tokens": 3
          }
        ],
        "tokens": 12
      },
      "protocol": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "kind": "refer",
            "phrase": "docking bay seven",
            "code": "$5",
            "tokens": 1
          },
          {
            "field": "act",
            "label": "action",
            "kind": "refer",
            "phrase": "purge the outer airlock",
            "code": "$6",
            "tokens": 1
          },
          {
            "field": "stat",
            "label": "status",
            "kind": "refer",
            "phrase": "status critical",
            "code": "$10",
            "tokens": 1
          },
          {
            "field": "crew",
            "label": "crew",
            "kind": "refer",
            "phrase": "one crew aboard",
            "code": "$8",
            "tokens": 1
          }
        ],
        "tokens": 4,
        "newCodes": [],
        "defines": 0,
        "refers": 4
      },
      "codebookAfter": [
        {
          "code": "$1",
          "phrase": "cargo hold nine"
        },
        {
          "code": "$2",
          "phrase": "seal the hull breach"
        },
        {
          "code": "$3",
          "phrase": "status nominal"
        },
        {
          "code": "$4",
          "phrase": "two crew aboard"
        },
        {
          "code": "$5",
          "phrase": "docking bay seven"
        },
        {
          "code": "$6",
          "phrase": "purge the outer airlock"
        },
        {
          "code": "$7",
          "phrase": "status degraded"
        },
        {
          "code": "$8",
          "phrase": "one crew aboard"
        },
        {
          "code": "$9",
          "phrase": "reroute the main power"
        },
        {
          "code": "$10",
          "phrase": "status critical"
        },
        {
          "code": "$11",
          "phrase": "three crew aboard"
        },
        {
          "code": "$12",
          "phrase": "medical bay two"
        },
        {
          "code": "$13",
          "phrase": "engine room four"
        },
        {
          "code": "$14",
          "phrase": "vent the plasma coolant"
        }
      ],
      "reconstruction": {
        "loc": "docking bay seven",
        "act": "purge the outer airlock",
        "stat": "status critical",
        "crew": "one crew aboard"
      },
      "correct": true,
      "cumPlaintext": 192,
      "cumProtocol": 93,
      "savedPct": 67
    },
    {
      "r": 16,
      "record": {
        "loc": "medical bay two",
        "act": "purge the outer airlock",
        "stat": "status critical",
        "crew": "two crew aboard"
      },
      "phase": "emerged",
      "plaintext": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "phrase": "medical bay two",
            "tokens": 3
          },
          {
            "field": "act",
            "label": "action",
            "phrase": "purge the outer airlock",
            "tokens": 4
          },
          {
            "field": "stat",
            "label": "status",
            "phrase": "status critical",
            "tokens": 2
          },
          {
            "field": "crew",
            "label": "crew",
            "phrase": "two crew aboard",
            "tokens": 3
          }
        ],
        "tokens": 12
      },
      "protocol": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "kind": "refer",
            "phrase": "medical bay two",
            "code": "$12",
            "tokens": 1
          },
          {
            "field": "act",
            "label": "action",
            "kind": "refer",
            "phrase": "purge the outer airlock",
            "code": "$6",
            "tokens": 1
          },
          {
            "field": "stat",
            "label": "status",
            "kind": "refer",
            "phrase": "status critical",
            "code": "$10",
            "tokens": 1
          },
          {
            "field": "crew",
            "label": "crew",
            "kind": "refer",
            "phrase": "two crew aboard",
            "code": "$4",
            "tokens": 1
          }
        ],
        "tokens": 4,
        "newCodes": [],
        "defines": 0,
        "refers": 4
      },
      "codebookAfter": [
        {
          "code": "$1",
          "phrase": "cargo hold nine"
        },
        {
          "code": "$2",
          "phrase": "seal the hull breach"
        },
        {
          "code": "$3",
          "phrase": "status nominal"
        },
        {
          "code": "$4",
          "phrase": "two crew aboard"
        },
        {
          "code": "$5",
          "phrase": "docking bay seven"
        },
        {
          "code": "$6",
          "phrase": "purge the outer airlock"
        },
        {
          "code": "$7",
          "phrase": "status degraded"
        },
        {
          "code": "$8",
          "phrase": "one crew aboard"
        },
        {
          "code": "$9",
          "phrase": "reroute the main power"
        },
        {
          "code": "$10",
          "phrase": "status critical"
        },
        {
          "code": "$11",
          "phrase": "three crew aboard"
        },
        {
          "code": "$12",
          "phrase": "medical bay two"
        },
        {
          "code": "$13",
          "phrase": "engine room four"
        },
        {
          "code": "$14",
          "phrase": "vent the plasma coolant"
        }
      ],
      "reconstruction": {
        "loc": "medical bay two",
        "act": "purge the outer airlock",
        "stat": "status critical",
        "crew": "two crew aboard"
      },
      "correct": true,
      "cumPlaintext": 204,
      "cumProtocol": 97,
      "savedPct": 67
    },
    {
      "r": 17,
      "record": {
        "loc": "engine room four",
        "act": "reroute the main power",
        "stat": "status nominal",
        "crew": "two crew aboard"
      },
      "phase": "emerged",
      "plaintext": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "phrase": "engine room four",
            "tokens": 3
          },
          {
            "field": "act",
            "label": "action",
            "phrase": "reroute the main power",
            "tokens": 4
          },
          {
            "field": "stat",
            "label": "status",
            "phrase": "status nominal",
            "tokens": 2
          },
          {
            "field": "crew",
            "label": "crew",
            "phrase": "two crew aboard",
            "tokens": 3
          }
        ],
        "tokens": 12
      },
      "protocol": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "kind": "refer",
            "phrase": "engine room four",
            "code": "$13",
            "tokens": 1
          },
          {
            "field": "act",
            "label": "action",
            "kind": "refer",
            "phrase": "reroute the main power",
            "code": "$9",
            "tokens": 1
          },
          {
            "field": "stat",
            "label": "status",
            "kind": "refer",
            "phrase": "status nominal",
            "code": "$3",
            "tokens": 1
          },
          {
            "field": "crew",
            "label": "crew",
            "kind": "refer",
            "phrase": "two crew aboard",
            "code": "$4",
            "tokens": 1
          }
        ],
        "tokens": 4,
        "newCodes": [],
        "defines": 0,
        "refers": 4
      },
      "codebookAfter": [
        {
          "code": "$1",
          "phrase": "cargo hold nine"
        },
        {
          "code": "$2",
          "phrase": "seal the hull breach"
        },
        {
          "code": "$3",
          "phrase": "status nominal"
        },
        {
          "code": "$4",
          "phrase": "two crew aboard"
        },
        {
          "code": "$5",
          "phrase": "docking bay seven"
        },
        {
          "code": "$6",
          "phrase": "purge the outer airlock"
        },
        {
          "code": "$7",
          "phrase": "status degraded"
        },
        {
          "code": "$8",
          "phrase": "one crew aboard"
        },
        {
          "code": "$9",
          "phrase": "reroute the main power"
        },
        {
          "code": "$10",
          "phrase": "status critical"
        },
        {
          "code": "$11",
          "phrase": "three crew aboard"
        },
        {
          "code": "$12",
          "phrase": "medical bay two"
        },
        {
          "code": "$13",
          "phrase": "engine room four"
        },
        {
          "code": "$14",
          "phrase": "vent the plasma coolant"
        }
      ],
      "reconstruction": {
        "loc": "engine room four",
        "act": "reroute the main power",
        "stat": "status nominal",
        "crew": "two crew aboard"
      },
      "correct": true,
      "cumPlaintext": 216,
      "cumProtocol": 101,
      "savedPct": 67
    },
    {
      "r": 18,
      "record": {
        "loc": "engine room four",
        "act": "reroute the main power",
        "stat": "status critical",
        "crew": "one crew aboard"
      },
      "phase": "emerged",
      "plaintext": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "phrase": "engine room four",
            "tokens": 3
          },
          {
            "field": "act",
            "label": "action",
            "phrase": "reroute the main power",
            "tokens": 4
          },
          {
            "field": "stat",
            "label": "status",
            "phrase": "status critical",
            "tokens": 2
          },
          {
            "field": "crew",
            "label": "crew",
            "phrase": "one crew aboard",
            "tokens": 3
          }
        ],
        "tokens": 12
      },
      "protocol": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "kind": "refer",
            "phrase": "engine room four",
            "code": "$13",
            "tokens": 1
          },
          {
            "field": "act",
            "label": "action",
            "kind": "refer",
            "phrase": "reroute the main power",
            "code": "$9",
            "tokens": 1
          },
          {
            "field": "stat",
            "label": "status",
            "kind": "refer",
            "phrase": "status critical",
            "code": "$10",
            "tokens": 1
          },
          {
            "field": "crew",
            "label": "crew",
            "kind": "refer",
            "phrase": "one crew aboard",
            "code": "$8",
            "tokens": 1
          }
        ],
        "tokens": 4,
        "newCodes": [],
        "defines": 0,
        "refers": 4
      },
      "codebookAfter": [
        {
          "code": "$1",
          "phrase": "cargo hold nine"
        },
        {
          "code": "$2",
          "phrase": "seal the hull breach"
        },
        {
          "code": "$3",
          "phrase": "status nominal"
        },
        {
          "code": "$4",
          "phrase": "two crew aboard"
        },
        {
          "code": "$5",
          "phrase": "docking bay seven"
        },
        {
          "code": "$6",
          "phrase": "purge the outer airlock"
        },
        {
          "code": "$7",
          "phrase": "status degraded"
        },
        {
          "code": "$8",
          "phrase": "one crew aboard"
        },
        {
          "code": "$9",
          "phrase": "reroute the main power"
        },
        {
          "code": "$10",
          "phrase": "status critical"
        },
        {
          "code": "$11",
          "phrase": "three crew aboard"
        },
        {
          "code": "$12",
          "phrase": "medical bay two"
        },
        {
          "code": "$13",
          "phrase": "engine room four"
        },
        {
          "code": "$14",
          "phrase": "vent the plasma coolant"
        }
      ],
      "reconstruction": {
        "loc": "engine room four",
        "act": "reroute the main power",
        "stat": "status critical",
        "crew": "one crew aboard"
      },
      "correct": true,
      "cumPlaintext": 228,
      "cumProtocol": 105,
      "savedPct": 67
    },
    {
      "r": 19,
      "record": {
        "loc": "medical bay two",
        "act": "reroute the main power",
        "stat": "status nominal",
        "crew": "one crew aboard"
      },
      "phase": "emerged",
      "plaintext": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "phrase": "medical bay two",
            "tokens": 3
          },
          {
            "field": "act",
            "label": "action",
            "phrase": "reroute the main power",
            "tokens": 4
          },
          {
            "field": "stat",
            "label": "status",
            "phrase": "status nominal",
            "tokens": 2
          },
          {
            "field": "crew",
            "label": "crew",
            "phrase": "one crew aboard",
            "tokens": 3
          }
        ],
        "tokens": 12
      },
      "protocol": {
        "segments": [
          {
            "field": "loc",
            "label": "location",
            "kind": "refer",
            "phrase": "medical bay two",
            "code": "$12",
            "tokens": 1
          },
          {
            "field": "act",
            "label": "action",
            "kind": "refer",
            "phrase": "reroute the main power",
            "code": "$9",
            "tokens": 1
          },
          {
            "field": "stat",
            "label": "status",
            "kind": "refer",
            "phrase": "status nominal",
            "code": "$3",
            "tokens": 1
          },
          {
            "field": "crew",
            "label": "crew",
            "kind": "refer",
            "phrase": "one crew aboard",
            "code": "$8",
            "tokens": 1
          }
        ],
        "tokens": 4,
        "newCodes": [],
        "defines": 0,
        "refers": 4
      },
      "codebookAfter": [
        {
          "code": "$1",
          "phrase": "cargo hold nine"
        },
        {
          "code": "$2",
          "phrase": "seal the hull breach"
        },
        {
          "code": "$3",
          "phrase": "status nominal"
        },
        {
          "code": "$4",
          "phrase": "two crew aboard"
        },
        {
          "code": "$5",
          "phrase": "docking bay seven"
        },
        {
          "code": "$6",
          "phrase": "purge the outer airlock"
        },
        {
          "code": "$7",
          "phrase": "status degraded"
        },
        {
          "code": "$8",
          "phrase": "one crew aboard"
        },
        {
          "code": "$9",
          "phrase": "reroute the main power"
        },
        {
          "code": "$10",
          "phrase": "status critical"
        },
        {
          "code": "$11",
          "phrase": "three crew aboard"
        },
        {
          "code": "$12",
          "phrase": "medical bay two"
        },
        {
          "code": "$13",
          "phrase": "engine room four"
        },
        {
          "code": "$14",
          "phrase": "vent the plasma coolant"
        }
      ],
      "reconstruction": {
        "loc": "medical bay two",
        "act": "reroute the main power",
        "stat": "status nominal",
        "crew": "one crew aboard"
      },
      "correct": true,
      "cumPlaintext": 240,
      "cumProtocol": 109,
      "savedPct": 67
    }
  ],
  "summary": {
    "totalPlaintext": 240,
    "totalProtocol": 109,
    "saved": 131,
    "reductionPct": 55,
    "ratio": 2.2,
    "steadyPlaintext": 12.0,
    "steadyProtocol": 4.0,
    "steadyReductionPct": 67,
    "vocabSize": 14
  }
};
