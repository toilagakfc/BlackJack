# game_server/presentation/sockets/handlers/game_handler.py
from presentation.sockets.server import sio
from application.room_service import RoomService
from infrastructure.repositories.room_repo_memory import InMemoryRoomRepository


@sio.event
async def start_game(sid, data):
    """
    data = { room_id }
    """
    try:
        room = RoomService.start_game(data["room_id"], sid)
        
        # await sio.emit(
        #     "game_started",
        #     room.game.public_state(hide_dealer_cards=True),
        #     room=room.id,
        # )
        await sio.emit(
            "player_turn",
            {"player_id": room.game.current_player().id},
            room=room.id,
        )
    except ValueError as e:
        await sio.emit(
            "error",
            {"code": str(e)},
            room=sid,
        )
        
@sio.event
async def end_game(sid, data): 
    """
    data = { room_id }
    """
    room = RoomService.get_room(data["room_id"])
    if not room or not room.game:
        await sio.emit(
            "error",
            {"code": "GAME_NOT_FOUND"},
            room=sid,
        )
        return

    RoomService.start_game(room.id, room.game)

    await sio.emit(
        "game_ended",
        room.game.public_state(hide_dealer_cards=False),
        room=room.id,
    )

@sio.event
async def reset_game(sid, data):
    """
    data = { room_id }
    """
    try:
        room = RoomService.reset_game(data["room_id"])

        await sio.emit(
            "game_reset",
            room.game.public_state(hide_dealer_cards=True),
            room=room.id,
        )

    except ValueError as e:
        await sio.emit(
            "error",
            {"code": str(e)},
            room=sid,
        )
        
@sio.event
async def player_action(sid, data):
    """
    data = { room_id, action }
    action = "hit" | "stand"
    """
    room = RoomService.get_room(data["room_id"])
    if not room or not room.game:
        await sio.emit(
            "error",
            {"code": "GAME_NOT_FOUND"},
            room=sid,
        )
        return

    try:
        if data["action"] == "hit":
            room.game.player_hit(sid)
        elif data["action"] == "stand":
            room.game.player_stand(sid)
        else:
            raise ValueError("INVALID_ACTION")

        RoomService.start_game(room.id, room.game)

        await sio.emit(
            "game_updated",
            room.game.public_state(hide_dealer_cards=True),
            room=room.id,
        )

    except ValueError as e:
        await sio.emit(
            "error",
            {"code": str(e)},
            room=sid,
        )

@sio.event
async def dealer_compare(sid, data):
    """
    data = { room_id, target_sid }
    """
    room = RoomService.get_room(data["room_id"])

    if sid != room.dealer_id:
        raise ValueError("NOT_DEALER")

    result = room.game.dealer_compare(data["target_sid"])

    await sio.emit(
        "compare_result",
        result,
        room=room.id,
    )