# presentation/sockets/handlers/system_handler.py
from application.room_service import RoomService
from presentation.sockets.server import sio

@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")
    # await sio.leave_room(sid)
    room = RoomService.player_disconnect(sid)
    if not room:
        print(f"Dealer out room: {sid}")
        await sio.close_room(sid)
        await sio.emit(
            "left_room",
            {"player_id": sid},
            to=sid,
        )
    else:
        await sio.emit(
            "player_left",
            {"player_id": sid},
            room=room.id,
        )

@sio.event
async def ping(sid):
    await sio.emit("pong", room=sid)
    
