import socketio
from fastapi import FastAPI,Body
from room_manager import create_room, get_room, remove_room
from models import PlayerState
from game_engine import GameEngine
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = FastAPI()
socket_app = socketio.ASGIApp(sio, app)

@sio.event
async def connect(sid, environ):
    print("CONNECT", sid)


@sio.event
async def disconnect(sid):
    print("DISCONNECT", sid)
    for room_id, room in list(getattr(__import__("room_manager"), "rooms").items()):
        if sid in room.players:
            player = room.remove_player(sid)

            if player.is_dealer:
                await sio.emit("room_closed", room=room_id)
                remove_room(room_id)
            else:
                await sio.emit("player_out", player.sid, room=room_id)
            break
        

@sio.event
async def create_room_event(sid, data):
    try:
        room = create_room(sid, data["name"])
    except ValueError:
        return await sio.emit(
            "error",
            {"message": "Dealer đang có room hoạt động, không thể tạo room mới"},
            to=sid,
        )

    print("ROOM CREATED:", room.room_id, "DEALER:", data["name"])
    await sio.enter_room(sid, room.room_id)

    await sio.emit(
        "room_created",
        {"room_id": room.room_id, "dealer": data["name"]},
        to=sid,
    )


@sio.event
async def join_room(sid, data):
    room = get_room(data["room_id"])
    if not room:
        return await sio.emit("error", "ROOM_NOT_FOUND", to=sid)

    if room.player_count() >= 9:
        return await sio.emit("error", "ROOM_FULL", to=sid)

    player = PlayerState(sid, data["name"])
    room.add_player(player)
    room.phase = "WAITING_FOR_PLAYERS"
    room.turn_order.append(sid)
    await sio.enter_room(sid, room.room_id)

    await sio.emit(
        "player_joined",
        [{"sid": sid, "name": p.name} for sid, p in room.players.items()],
        # room.players,
        room=room.room_id,
    )

@sio.event
async def leave_room(sid, data):
    room = get_room(data["room_id"])
    if not room:
        return await sio.emit("error", "ROOM_NOT_FOUND", to=sid)

    # Check if room is in game
    if room.started:
        return await sio.emit("error", "GAME_IN_PROGRESS", to=sid)
    
    player = room.remove_player(sid)
    if not player:
        return await sio.emit("error", "PLAYER_NOT_IN_ROOM", to=sid)

    await sio.leave_room(sid, room.room_id)

    if player.is_dealer:
        #remove memeber còn lại trong room
        for sid in room.players.keys():
            await sio.leave_room(sid, room.room_id)
            await sio.emit("room_closed",room=room.room_id,to=sid)
        await sio.emit("room_closed", room=room.room_id)
        remove_room(room.room_id)
        print("Dealer left, room closed:", room.room_id)
    else:
        await sio.emit("player_out", player.sid, room=room.room_id)
        
@sio.event
async def player_ready(sid, data):
    room = get_room(data["room_id"])
    if not room:
        return await sio.emit("error", "ROOM_NOT_FOUND", to=sid)

    player = room.players.get(sid)
    if not player:
        return await sio.emit("error", "PLAYER_NOT_IN_ROOM", to=sid)

    player.ready = True
    await sio.emit(
        "player_ready",
        {"sid": sid, "name": player.name},
        room=room.room_id,
    )
    

@sio.event
async def start_game(sid, data):
    
    #check total player >= 2
    room = get_room(data["room_id"])
    if not room:
        return await sio.emit("error", "ROOM_NOT_FOUND", to=sid)
    if room.player_count() < 2:
        return await sio.emit("error", "NOT_ENOUGH_PLAYERS", to=sid)
    
    if not room or room.dealer_sid != sid:
        return

    # Prevent starting game multiple times
    if room.started:
        return await sio.emit("error", "GAME_ALREADY_STARTED", to=sid)
    
    # Check all players ready
    player_ready = all(p.ready for p in room.players.values())
    if not player_ready:
        return await sio.emit("error", "NOT_ALL_PLAYERS_READY", to=sid)

    # Set room started before initializing game engine to prevent join/leave during game
    room.started = True

    room.turn_order += [room.dealer_sid]
    room.current_turn = 0
    room.engine = GameEngine(room)
    room.engine.initial_deal()
    room.engine.init_turn()
    print("Turn order:", room.turn_order)
    await sio.emit(
            "game_started",
            room.engine.public_state(),
            room=room.room_id
        )
    await sio.emit(
        "turn_state",
        {
            "phase": room.phase,
            "current_sid": room.turn_order[room.current_turn],
            "state": room.engine.public_state(),
        },
        room=room.room_id,
        )
    
@sio.event
async def game_end(sid, data):
    room = get_room(data["room_id"])
    if not room:
        return await sio.emit("error", "ROOM_NOT_FOUND", to=sid)

    if room.dealer_sid != sid:
        return await sio.emit("error", "NOT_DEALER", to=sid)
    
    
    # End game and reset room state
    room.phase = "FINISHED"
    room.started = False
    await sio.emit("game_ended", room=room.room_id)
@sio.event
async def player_action(sid, data):
    room = get_room(data["room_id"])
    engine = room.engine

    if room.phase != "PLAYER_TURN":
        return await sio.emit("error", "NOT_PLAYER_PHASE", to=sid)

    try:
        engine.player_action(sid, data["action"])
    except ValueError as e:
        return await sio.emit("error", str(e), to=sid)

    await sio.emit(
        "turn_state",
        {
            "phase": room.phase,
            "current_sid": (
                engine.current_player_sid()
                if room.phase == "PLAYER_TURN"
                else room.dealer_sid
            ),
        },
        room=room.room_id,
    )

@sio.event
async def kick_player(sid, data):
    room = get_room(data["room_id"])
    if not room:
        return await sio.emit("error", "ROOM_NOT_FOUND", to=sid)

    if room.dealer_sid != sid:
        return await sio.emit("error", "NOT_DEALER", to=sid)

    target_sid = data["target_sid"]
    if target_sid not in room.players:
        return await sio.emit("error", "PLAYER_NOT_IN_ROOM", to=sid)

    if target_sid == room.dealer_sid:
        return await sio.emit("error", "CANNOT_KICK_DEALER", to=sid)

    room.remove_player(target_sid)
    print(f"Player {target_sid} kicked by dealer")
    await sio.leave_room(target_sid, room.room_id)
    await sio.emit("player_kicked", {"kicked_by": sid}, room=room.room_id, to=target_sid)
    print(f"Player {target_sid} kicked and removed from room {room.room_id}")

@sio.event
async def rooms_list(sid):
    rooms = [
        {
            "room_id": room_id,
            "dealer": room.players[room.dealer_sid].name,
            "player_count": room.player_count(),
        }
        for room_id, room in getattr(__import__("room_manager"), "rooms").items()
    ]
    await sio.emit("rooms_list", rooms, to=sid)

@sio.event
async def dealer_action(sid, data):
    room = get_room(data["room_id"])
    if not room:
        return

    if sid != room.dealer_sid:
        await sio.emit("error", "NOT_DEALER", to=sid)
        return

    engine = room.engine
    action = data["action"]
    
    if action == "compare":
        target_sid = data["target_sid"]
        print(f"Dealer compare {target_sid}")

        try:
            result = engine.dealer_compare(target_sid)
        except ValueError as e:
            await sio.emit("error", str(e), to=sid)
            return

        await sio.emit(
            "compare_result",
            result,
            room=room.room_id
        )
        
    # ----- DEALER HIT -----
    elif action == "hit":
        state = engine.dealer_hit()
        print("Dealer hit:", state)
        # PUBLIC điểm dealer cho tất cả player
        await sio.emit(
            "dealer_public_state",
            {
                "phase": room.phase,
                "current_sid": room.dealer_sid,
                "state": engine.public_state(True),
            },
            room=room.room_id
        )
        return
    
    elif action == "compare_all":
        results = engine.compare_all()
        room.phase = "FINISHED"
        room.started = False
        await sio.emit(
            "compare_result",
            results,
            room=room.room_id
        )
    