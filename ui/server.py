"""Interlingua UI — a minimal static web server.

Serves the space-themed dashboard that animates two agents (Grace + Rocky)
inventing a shared language. The negotiation streams entirely in the browser
(mock data), so this server just hands out the page and its assets.

Run:
    python -m ui.server          # http://127.0.0.1:8000
"""
from __future__ import annotations

import os

import uvicorn
from starlette.applications import Starlette
from starlette.responses import FileResponse
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles

_STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


async def index(request):
    return FileResponse(os.path.join(_STATIC, "index.html"))


async def favicon(request):
    return FileResponse(os.path.join(_STATIC, "alien.jpeg"))


app = Starlette(routes=[
    Route("/", index),
    Route("/favicon.ico", favicon),
    Mount("/static", app=StaticFiles(directory=_STATIC), name="static"),
])


def main() -> None:
    print("Interlingua UI on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
