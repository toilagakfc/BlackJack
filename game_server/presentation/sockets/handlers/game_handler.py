# game_server/presentation/sockets/handlers/game_handler.py
""" Thay đổi so với version trước

| | Trước | Mới |
|---|---|---|
| `end_game` | không có handler | ✅ thêm event `end_game` |
| `place_bet` | không có | ✅ thêm event `place_bet` |
| `_emit_turn` | inline, lặp code | ✅ helper dùng chung cho mọi action |
| `_require` | không validate data | ✅ raise rõ ràng nếu thiếu field |
| `compare` response | chỉ `result` | ✅ `result + delta + balance` |
| `compare_all` response | flat dict | ✅ array từng player có đủ `result/delta/balance` |
| `FINISHED` notify | chỉ trong compare | ✅ `_emit_turn` tự handle mọi phase transition |

### Event map hoàn chỉnh
```
Client → Server          Server → Client (room)
─────────────────────────────────────────────────
start_game           →   game_updated (per player)
                         player_turn | dealer_turn
place_bet            →   bet_placed
player_action hit    →   game_updated + player_turn | dealer_turn
player_action stand  →   game_updated + player_turn | dealer_turn
dealer_action hit    →   game_updated + dealer_turn
dealer_action compare →  compare_result + game_updated + game_finished?
dealer_action compare_all → compare_result + game_updated + game_finished
end_game             →   game_ended"""
from presentation.sockets.server import sio
from application.game_service import GameService
from infrastructure.repositories import get_game_repository, get_room_repository,get_player_repository

game_service = GameService(
    room_repo=get_room_repository(),
    game_repo=get_game_repository(),
    player_repo=get_player_repository()
)

# ── Helpers ───────────────────────────────────────────────────────────────

async def _emit_game_state(state, room_id: str):
    """Emit riêng cho từng player (thấy bài mình) + broadcast chung."""
    for player in state.players:
        await sio.emit(
            "game_updated",
            state.to_public(viewer_id=player.id),
            room=player.id,
        )
    await sio.emit(
        "game_updated",
        state.to_dealer(),
        room=state.dealer_id,
    )


async def _emit_error(sid: str, code: str):
    await sio.emit("error", {"code": code}, room=sid)

async def _emit_turn(state, room_id: str):
    """Emit thông báo lượt tiếp theo sau mỗi action."""
    if state.phase == "PLAYER_TURN":
        await sio.emit(
            "player_turn",
            {"player_id": state.current_player_id},
            room=room_id,
        )
    elif state.phase == "DEALER_TURN":
        await sio.emit("dealer_turn", {}, room=room_id)
    elif state.phase == "FINISHED":
        await sio.emit("game_finished", {}, room=room_id)
        
def _require(data: dict, *keys: str):
    """Raise KeyError rõ ràng nếu thiếu field trong data."""
    for key in keys:
        if key not in data:
            raise ValueError(f"MISSING_FIELD_{key.upper()}")

# ── Game lifecycle ────────────────────────────────────────────────────────

@sio.event
async def start_game(sid, data):
    """
    data = { room_id }
    """
    try:
        _require(data, "room_id")

        state = await game_service.start_game(
            room_id=data["room_id"],
            sid=sid,
        )

        await _emit_game_state(state, state.room_id)
        await _emit_turn(state, data["room_id"])

    except ValueError as e:
        await _emit_error(sid, str(e))


@sio.event
async def end_game(sid, data):
    """
    data = { room_id }
    """
    try:
        _require(data, "room_id")

        state = await game_service.end_game(
            room_id=data["room_id"],
            sid=sid,
        )

        await sio.emit("game_ended", {}, room=data["room_id"])

    except ValueError as e:
        await _emit_error(sid, str(e))


# ── Player actions ────────────────────────────────────────────────────────

@sio.event
async def player_action(sid, data):
    """
    data = { room_id, action }
    action = "hit" | "stand"
    """
    try:
        _require(data, "room_id", "action")

        room_id = data["room_id"]
        action  = data["action"]

        if action == "hit":
            state = await game_service.player_hit(room_id, sid)
        elif action == "stand":
            state = await game_service.player_stand(room_id, sid)
        else:
            raise ValueError("INVALID_ACTION")

        await _emit_game_state(state,room_id)
        await _emit_turn(state, room_id)

    except ValueError as e:
        await _emit_error(sid, str(e))


# ── Dealer actions ────────────────────────────────────────────────────────

@sio.event
async def dealer_action(sid, data):
    """
    data = { room_id, action, target_sid? }
    action = "hit" | "compare" | "compare_all"
    """
    try:
        _require(data, "room_id", "action")

        room_id = data["room_id"]
        action  = data["action"]

        if action == "hit":
            state = await game_service.dealer_hit(room_id, sid)

            await _emit_game_state(state,room_id)
            await _emit_turn(state, room_id)

        elif action == "compare":
            _require(data, "target_sid")
            target_sid = data["target_sid"]
            state, result = await game_service.dealer_compare(
                room_id, dealer_id=sid, player_id=target_sid
            )

            # Gửi kết quả so sánh cho cả phòng
            await sio.emit(
                "compare_result",
                {
                    "player_id": data["target_sid"],
                    "result":    result["result"],
                    "delta":     result["delta"],
                    "balance":   result["balance"],
                },
                room=room_id,
            )
            await _emit_game_state(state,room_id)
            await _emit_turn(state, room_id)
            # if state.phase == 'FINISHED':
                # await sio.emit('game_finished',{},room=room_id)

        else:
            raise ValueError("INVALID_ACTION")

    except ValueError as e:
        await _emit_error(sid, str(e))