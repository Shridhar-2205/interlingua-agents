"""Depth-B Alien — structured emergence agent on :9202 (peer: human).

Speaks the L9 emergence extension: exchanges {object → word} proposals in a
structured DataPart instead of free-form prose. Run alongside
human_agent_structured.py, then trigger with trigger_structured.py.
"""
from emergence_structured import serve

if __name__ == "__main__":
    serve("alien", "human")
