# game_server/presentation/sockets/handlers/betting_handler.py
"""
Client → Server
────────────────
  bet:open          { room_id, min_bet?, max_bet?, timeout? }
  bet:place         { room_id, amount }
  bet:lock          { room_id }
  bet:kick_folded   { room_id }          ← dealer kicks players who didn't bet
  bet:reset         { room_id }          ← dealer cancels round, back to waiting
  bet:check_balance { room_id }

Server → Client
────────────────
  bet:opened        { room_id, min_bet, max_bet, timeout_seconds, pot }
  bet:placed        { room_id, player_id, amount, pot }
  bet:locked        { room_id, pot, bets, folded }
  bet:timeout       { room_id, pot, bets, folded }
  bet:folded_kicked { room_id, kicked: [pid, …] }
  bet:reset         { room_id }
  pot:update            { room_id, pot }
  balance:info          { player_id, balance }
  error                 { code }
"""
import logging
from application.betting_service import BettingService
from infrastructure.repositories import get_room_repository, get_player_repository
from presentation.sockets.server import sio

logger = logging.getLogger("BettingHandler")

betting_service = BettingService(
    room_repo=get_room_repository(),
    player_repo=get_player_repository(),
)


# ── Timeout callback ──────────────────────────────────────────────────────

async def _on_betting_timeout(room_id: str, state, folded_ids: list[str]):
    payload = {
        "room_id": room_id,
        "pot": state.pot,
        "bets": state.bets,
        "folded": folded_ids,
    }
    # Send timeout notice first so the client can show a distinct message,
    # then send locked so the client transitions state identically to a manual lock.
    await sio.emit("bet:timeout", payload, room=room_id)
    await sio.emit("bet:locked", payload, room=room_id)
    logger.info(f"Emitted bet:timeout + bet:locked — room={room_id}")


betting_service.register_timeout_callback(_on_betting_timeout)


# ── Helpers ───────────────────────────────────────────────────────────────

def _require(data: dict, *keys: str):
    for key in keys:
        if key not in data or data[key] is None:
            raise ValueError(f"MISSING_FIELD_{key.upper()}")


async def _emit_error(sid: str, code: str):
    await sio.emit("error", {"code": code}, room=sid)


# ── Handlers ──────────────────────────────────────────────────────────────

@sio.event
async def bet_start(sid, data):
    """
    Dealer opens (or reopens) the betting phase.
    Works from phase 'waiting' and 'betting_locked' (after timeout or manual lock).
    data = { room_id, min_bet?, max_bet?, timeout? }
    """
    try:
        _require(data, "room_id")
        room_id = data["room_id"]

        kwargs = {}
        if "min_bet" in data:
            kwargs["min_bet"] = int(data["min_bet"])
        if "max_bet" in data:
            kwargs["max_bet"] = int(data["max_bet"])
        if "timeout" in data:
            kwargs["timeout_seconds"] = int(data["timeout"])

        state = await betting_service.open_betting(room_id, sid, **kwargs)

        await sio.emit(
            "bet:opened",
            {
                "room_id": room_id,
                "min_bet": state.min_bet,
                "max_bet": state.max_bet,
                "timeout_seconds": state.timeout_seconds,
                "pot": state.pot,
            },
            room=room_id,
        )
        logger.info(f"bet:opened emitted — room={room_id}")

    except (ValueError, TypeError) as exc:
        await _emit_error(sid, str(exc))


@sio.event
async def bet_place(sid, data):
    """
    Player submits a bet.
    data = { room_id, amount }
    """
    try:
        _require(data, "room_id", "amount")
        room_id = data["room_id"]
        amount = int(data["amount"])

        state, all_placed = await betting_service.place_bet(room_id, sid, amount)

        await sio.emit(
            "bet:placed",
            {"room_id": room_id, "player_id": sid, "amount": amount, "pot": state.pot},
            room=room_id,
        )
        await sio.emit("pot:update", {"room_id": room_id, "pot": state.pot}, room=room_id)

        if all_placed:
            locked_state, folded = await betting_service.lock_betting(
                room_id, triggered_by="all_placed"
            )
            await sio.emit(
                "bet:locked",
                {
                    "room_id": room_id,
                    "pot": locked_state.pot,
                    "bets": locked_state.bets,
                    "folded": folded,
                },
                room=room_id,
            )

    except (ValueError, TypeError) as exc:
        await _emit_error(sid, str(exc))


@sio.event
async def bet_lock(sid, data):
    """
    Dealer manually closes betting early.
    data = { room_id }
    """
    try:
        _require(data, "room_id")
        room_id = data["room_id"]

        state, folded = await betting_service.lock_betting(room_id, triggered_by="dealer")

        await sio.emit(
            "bet:locked",
            {"room_id": room_id, "pot": state.pot, "bets": state.bets, "folded": folded},
            room=room_id,
        )

    except (ValueError, TypeError) as exc:
        await _emit_error(sid, str(exc))


@sio.event
async def betting_kick_folded(sid, data):
    """
    Dealer removes all folded (timed-out) players from the room.
    Call this after betting:locked/timeout, before reopening.
    data = { room_id }
    """
    try:
        _require(data, "room_id")
        room_id = data["room_id"]

        kicked = await betting_service.kick_folded(room_id, dealer_sid=sid)

        # Notify kicked players individually so they know they've been removed
        for pid in kicked:
            await sio.emit("kicked", {"room_id": room_id}, to=pid)
            await sio.leave_room(pid, room_id)

        # Notify the room who was removed
        await sio.emit(
            "bet:folded_kicked",
            {"room_id": room_id, "kicked": kicked},
            room=room_id,
        )
        logger.info(f"Folded players kicked — room={room_id} kicked={kicked}")

    except (ValueError, TypeError) as exc:
        await _emit_error(sid, str(exc))


@sio.event
async def bet_reset(sid, data):
    """
    Dealer resets the room back to 'waiting' without starting a new bet round.
    Useful when the dealer wants to cancel the locked/timed-out state entirely.
    data = { room_id }
    """
    try:
        _require(data, "room_id")
        room_id = data["room_id"]

        await betting_service.reset_betting(room_id, dealer_sid=sid)

        await sio.emit("bet:reset", {"room_id": room_id}, room=room_id)
        logger.info(f"bet:reset emitted — room={room_id}")

    except (ValueError, TypeError) as exc:
        await _emit_error(sid, str(exc))


@sio.event
async def bet_check_balance(sid, data):
    """
    Player checks their own balance.
    data = { room_id }
    """
    try:
        balance = await betting_service.get_balance(sid)
        await sio.emit("balance:info", {"player_id": sid, "balance": balance}, room=sid)

    except ValueError as exc:
        await _emit_error(sid, str(exc))