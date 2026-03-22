# game_server/presentation/sockets/handlers/system_handler.py
"""
system_handler.py

The connect event is handled by socket_auth middleware (registered in main.py).
This file handles disconnect and ping only.
After auth middleware runs, every handler can get the real player_id with:

    from presentation.middleware.socket_auth import get_player_id
    player_id = await get_player_id(sio, sid)
"""
from presentation.sockets.server import sio
import logging

logger = logging.getLogger("socket")


@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")


@sio.event
async def ping(sid):
    await sio.emit("pong", room=sid)