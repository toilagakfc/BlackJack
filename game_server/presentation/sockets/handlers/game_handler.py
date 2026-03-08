# game_server/presentation/sockets/handlers/game_handler.py
from presentation.sockets.server import sio
from application.room_service import RoomService
from application.game_service import GameService
from infrastructure.repositories.room_repo_memory import InMemoryRoomRepository


@sio.event
async def start_game(sid, data):
    """
    data = { room_id }
    """
    try:
        room = RoomService.start_game(data["room_id"], sid)
        await sio.emit(
            "game_started",
            room.game.public_state(),
            room=room.id,
        )
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
    try:
        room = RoomService.get_room(data["room_id"])
        game = GameService(room.id)
        if data["action"] == "hit":
            game.player_hit(sid)
        elif data["action"] == "stand":
            game.player_stand(sid)
        else:
            raise ValueError("INVALID_ACTION")

        print(room.game.public_state())
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
async def dealer_action(sid, data):
    """
    data = { room_id, target_sid }
    """
    try:
        room = RoomService.get_room(data["room_id"])
        game = GameService(room.id)
        if data["action"] == "hit":
            game.dealer_hit(sid)
        elif data["action"] == "compare":
            result = game.dealer_compare(sid,data["target_sid"])
            await sio.emit(
                "compare_result",
                {"result":result},
                room=room.id,
            )
        else:
            raise ValueError("INVALID_ACTION")

        print(room.game.public_state())
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
    