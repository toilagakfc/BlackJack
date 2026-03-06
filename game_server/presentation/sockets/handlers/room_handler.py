# presentation/sockets/handler/room_handler.py
from application.room_service import RoomService
from presentation.sockets.server import sio

@sio.event
async def create_room(sid, data):
    try:
        print(f"Request to create room by dealer SID: {sid}, name: {data['name']}")
        room = RoomService.create_room(dealer_sid=sid, name=data['name'])
        await sio.enter_room(sid, room.id)
        await sio.emit(
            "room_created",
            {"room_id": room.id, "dealer_name": room.dealer.name},
            room=sid,
        )
    except ValueError as e:
        await sio.emit(
            "error",
            {"code": str(e)},
            to=sid,
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
        if not room:
            raise ValueError("ROOM_NOT_FOUND")
        await sio.enter_room(sid, room.id)
        await sio.emit(
            "joined_room",
            {
                "room_id": room.id,
                "players": [player.name for player in room.players.values()],
            },
            to=sid,
        )

        await sio.emit(
            "player_joined",
            {
                "room_id": room.id,
                "players": {room.dealer.id: room.dealer.name, **{player.id: player.name for player in room.players.values()}}
            },
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
        if room.dealer is None:
            # Broadcast to Players in room
            await sio.emit(
                "room_closed",
                {"room_id": data["room_id"]},
                room=data["room_id"],
            )
            await sio.close_room(data["room_id"])
        await sio.leave_room(sid, data["room_id"])
        await sio.emit(
            "left_room",
            {"room_id": data["room_id"]},
            to=sid,
        )

        if room:  # room is None if dealer left and room was deleted
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
        
@sio.event
async def kick_player(sid, data):
    """
    data = { "room_id": "AB12CD", "target_sid": "XYZ789" }
    """
    try:
        room = RoomService.kick_player(
            room_id=data["room_id"],
            dealer_sid=sid,
            target_sid=data["target_sid"],
        )
        await sio.leave_room(data["target_sid"], data["room_id"])
        await sio.emit(
            "kicked",
            {"room_id": room.id},
            to=data["target_sid"],
        )

        
        await sio.emit(
            "player_kicked",
            {"sid": data["target_sid"]},
            room=room.id
        )
            
    except ValueError as e:
        await sio.emit(
            "error",
            {"code": str(e)},
            room=sid,
        )

@sio.event
async def player_ready(sid, data):
    """
    data = { room_id }
    """
    try:
        room = RoomService.ready(data["room_id"], sid)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")

        await sio.emit(
            "player_ready",
            {"sid": sid},
            room=room.id,
        )
        
    except ValueError as e:
        await sio.emit(
            "error",
            {"code": str(e)},
            room=sid,
        )

@sio.event
async def unready(sid, data):
    """
    data = { room_id }
    """
    try:
        room = RoomService.unready(data["room_id"], sid)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")

        await sio.emit(
            "player_unready",
            {"sid": sid},
            room=room.id,
        )
        
    except ValueError as e:
        await sio.emit(
            "error",
            {"code": str(e)},
            room=sid,
        )
        
@sio.event
async def room_list(sid):
    rooms = RoomService.room_list(sid)
    print(f"Rooms: {rooms}")
    if not rooms:
        await sio.emit(
            "error",
            {"code": "NO_ROOMS_AVAILABLE"},
            room=sid,
        )
        return
    
    await sio.emit(
        "room_list",
        {"rooms": rooms},
        room=sid,
    )