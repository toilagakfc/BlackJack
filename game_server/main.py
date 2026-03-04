"""DDD-style game server main entrypoint.

This module exposes `app` ASGI object so you can run:

    uvicorn game_server.main:app --reload

It delegates to the existing `server.app` ASGI application.
"""

# main.py

from fastapi import FastAPI
from presentation.sockets.server import socket_app

app = FastAPI()

# gắn socket.io vào FastAPI
app.mount("/ws", socket_app)


@app.get("/health")
def health():
    return {"status": "ok"}