"""l9 — emergent-convention tooling over A2A.

Public API for other agents:

    from l9 import Mind, Advice        # drop-in Theory-of-Mind advisor (self-contained)

`Mind` has no dependency on the Grace/Rocky demo modules (world/lens/signaling/
agent), so importing it does not pull the demo in. The demo modules use flat
imports and are meant to be run from inside l9/ (python run.py, python grace.py).
"""
from .mind import Mind, Advice

__all__ = ["Mind", "Advice"]
