# presentation/sockets/handlers/system_handler.py
from presentation.sockets.server import sio

@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

@sio.event
async def ping(sid):
    await sio.emit("pong", room=sid)