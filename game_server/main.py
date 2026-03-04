# main.py

from fastapi import FastAPI
from presentation.sockets.server import socket_app
from presentation.sockets.handlers import *
app = FastAPI()

# gắn socket.io vào FastAPI
app.mount("/", socket_app)


@app.get("/health")
def health():
    return {"status": "ok"}