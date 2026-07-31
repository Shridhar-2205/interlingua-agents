"""Depth-B Human — structured emergence agent on :9201 (peer: alien).

Speaks the L9 emergence extension: exchanges {object → word} proposals in a
structured DataPart instead of free-form prose, so there is no channel to derail
in. Run alongside alien_agent_structured.py, then trigger with trigger_structured.py.
"""
from emergence_structured import serve

if __name__ == "__main__":
    serve("human", "alien")
