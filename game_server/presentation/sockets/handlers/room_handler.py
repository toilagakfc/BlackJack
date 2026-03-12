# presentation/sockets/handler/room_handler.py
from application.room_service import RoomService
from presentation.sockets.server import sio
import logging
logger = logging.getLogger("Socket")

def _require(data: dict, *keys: str):
    for key in keys:
        if not data.get(key):
            raise ValueError(f"MISSING_FIELD_{key.upper()}")

@sio.event
async def create_room(sid, data):
    try:
        _require(data, "name")
        room = await RoomService.create_room(dealer_sid=sid, name=data['name'])
        await sio.enter_room(sid, room.id)
        await sio.emit(
            "room_created",
            {
                "room_id": room.id, 
                "dealer_name": room.dealer.name
            },
            room=sid,
        )
        logger.info(f"Room Created {room.id}, Dealer_sid: {room.dealer.id}, Dealer_name: {room.dealer.name}")
    except ValueError as e:
        logger.error(e)
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
        _require(data, "room_id", "name")
        room = await RoomService.join_room(
            room_id=data["room_id"],
            sid=sid,
            name=data["name"],
        )

        await sio.enter_room(sid, room.id)
        await sio.emit(
            "joined_room",
            {
                "room_id": room.id,
                "dealer":{"id": room.dealer.id, "name": room.dealer.name},
                "players": {pid: p.name for pid, p in room.players.items()},
            },
            to=sid,
        )

        await sio.emit(
            "player_joined",
            {
                "room_id": room.id,
                "players": room.players[sid].name
            },
            room=room.id,
        )
        logger.info(f"Player join Room {room.id}, Player_sid: {sid}, Player_name: {room.players[sid].name}")
        
    except ValueError as e:
        logger.error(e)
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
        _require(data, "room_id")
        room_id = data["room_id"]
        room = await RoomService.leave_room(room_id= room_id, sid= sid,)
        if room is None:
            # Broadcast to Players in room
            await sio.emit(
                "room_closed",
                {
                    "room_id": room_id
                },
                room=data["room_id"],
            )
            await sio.close_room(data["room_id"])
        else:
            await sio.emit(
                "player_left",
                {"sid": sid},
                room=room.id,
            )
        await sio.leave_room(sid, data["room_id"])
        await sio.emit(
            "left_room",
            {"room_id": data["room_id"]},
            to=sid,
        )
        logger.info(f"Player {sid} left room {room_id}")    
    except ValueError as e:
        logger.error(e)
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
        _require(data, "room_id", "target_sid")
        room_id = data["room_id"]
        target_sid = data["target_sid"]
        
        room = await RoomService.kick_player(
            room_id=room_id,
            dealer_sid=sid,
            target_sid=target_sid,
        )
        await sio.leave_room(target_sid, room_id)
        await sio.emit(
            "kicked",
            {
                "room_id": room.id
            },
            to=target_sid,
        )

        await sio.emit(
            "player_kicked",
            {"sid": target_sid},
            room=room.id
        )
            
    except ValueError as e:
        logger.error(e)
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
        if not data["room_id"]:
            raise ValueError("ROOM_NOT_FOUND")
        room = await RoomService.ready(data["room_id"], sid)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")

        await sio.emit(
            "player_ready",
            {"sid": sid},
            room=room.id,
        )
        logger.info(f"Room ID: {room.id} Player Ready: {sid}")
        
    except ValueError as e:
        logger.error(e)
        await sio.emit(
            "error",
            {"code": str(e)},
            room=sid,
        )

@sio.event
async def player_unready(sid, data):
    """
    data = { room_id }
    """
    try:
        if not data["room_id"]:
            raise ValueError("ROOM_NOT_FOUND")
        room = await RoomService.unready(data["room_id"], sid)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")

        await sio.emit(
            "player_unready",
            {"sid": sid},
            room=room.id,
        )
        logger.info(f"Room ID: {room.id} Player Unready: {sid}")
    except ValueError as e:
        logger.error(e)
        await sio.emit(
            "error",
            {"code": str(e)},
            room=sid,
        )
        
@sio.event
async def room_list(sid):
    rooms = await RoomService.room_list(sid)
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
    logger.info(f"Rooms: {rooms}")