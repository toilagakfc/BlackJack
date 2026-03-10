# presentation/sockets/handlers/system_handler.py
from application.room_service import RoomService
from presentation.sockets.server import sio
import logging

logger = logging.getLogger("socket")
@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")
    
@sio.event
async def ping(sid):
    await sio.emit("pong", room=sid)
    
