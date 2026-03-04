# presentation/sockets/handler/room_handler.py

from application.room_service import RoomService
from presentation.sockets.server import sio

@sio.event
async def create_room(sid, data):
    room = RoomService.create_room(dealer_sid=sid)

    await sio.emit(
        "room_created",
        {"room_id": room.id},
        room=sid,
    )


@sio.event
async def join_room(sid, data):
    """
    data = { "room_id": "AB12CD", "name": "Phong" }
    """
    try:
        room = RoomService.join_room(
            room_id=data["room_id"],
            sid=sid,
            name=data["name"],
        )

        await sio.emit(
            "joined_room",
            {
                "room_id": room.id,
                "players": room.players,
            },
            room=sid,
        )

        await sio.emit(
            "player_joined",
            {"name": data["name"]},
            room=room.id,
        )

    except ValueError as e:
        await sio.emit(
            "error",
            {"code": str(e)},
            room=sid,
        )
        
@sio.event
async def leave_room(sid, data):
    """
    data = { "room_id": "AB12CD" }
    """
    try:
        room = RoomService.leave_room(
            room_id=data["room_id"],
            sid=sid,
        )

        await sio.emit(
            "left_room",
            {"room_id": room.id},
            room=sid,
        )

        if room.has_players():
            await sio.emit(
                "player_left",
                {"sid": sid},
                room=room.id,
            )

    except ValueError as e:
        await sio.emit(
            "error",
            {"code": str(e)},
            room=sid,
        )