# game_server/application/betting_service.py
"""
BettingService owns the BETTING phase lifecycle:

    open_betting  → players call place_bet → lock_betting  → (GameService.start_game)
                                ↑ timeout closes automatically

After a timeout, the dealer can:
  - Call open_betting again to start a fresh round (clears folded state)
  - Call kick_folded to remove players who did not bet before reopening

Timeout tasks are stored in-process (_timeout_tasks). This is intentional:
if the server restarts mid-betting, rooms will naturally time-out when
the client reconnects and sees the phase is still "betting".
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from domain.state.betting_state import BettingState

logger = logging.getLogger("BettingService")

DEFAULT_MIN_BET = 10
DEFAULT_MAX_BET = 10_000
DEFAULT_TIMEOUT = 30  # seconds


class BettingService:

    def __init__(self, room_repo, player_repo):
        self.room_repo = room_repo
        self.player_repo = player_repo
        self._timeout_tasks: dict[str, asyncio.Task] = {}
        self._on_timeout: list = []

    # ── Lifecycle ─────────────────────────────────────────────────────────

    async def open_betting(
        self,
        room_id: str,
        dealer_sid: str,
        *,
        min_bet: int = DEFAULT_MIN_BET,
        max_bet: int = DEFAULT_MAX_BET,
        timeout_seconds: int = DEFAULT_TIMEOUT,
    ) -> BettingState:
        room = await self._get_room(room_id)

        if room.dealer.id != dealer_sid:
            raise ValueError("ONLY_DEALER_CAN_OPEN_BETTING")
        # Accept "waiting" (fresh) OR "betting_locked" (reopen after timeout/early lock)
        if room.phase not in ("waiting", "betting_locked"):
            raise ValueError("ROOM_NOT_WAITING")
        if not room.has_players():
            raise ValueError("NOT_ENOUGH_PLAYERS")

        # Reset all players so folded/ready/bet flags are cleared for the new round
        for player in room.players.values():
            player.reset()

        state = BettingState(
            room_id=room_id,
            min_bet=min_bet,
            max_bet=max_bet,
            timeout_seconds=timeout_seconds,
        )
        room.betting_state = state
        room.phase = "betting"
        await self.room_repo.save(room)

        self._cancel_timeout(room_id)
        task = asyncio.create_task(self._timeout_task(room_id, timeout_seconds))
        self._timeout_tasks[room_id] = task

        logger.info(f"Betting opened — room={room_id} timeout={timeout_seconds}s")
        return state

    async def place_bet(
        self,
        room_id: str,
        player_id: str,
        amount: int,
    ) -> tuple[BettingState, bool]:
        """
        Returns (betting_state, all_placed).
        all_placed=True means every active player has bet → caller may auto-lock.
        """
        room = await self._get_room(room_id)

        if room.phase != "betting":
            raise ValueError("NOT_BETTING_PHASE")

        state: BettingState = room.betting_state
        if state is None:
            raise ValueError("NO_BETTING_STATE")

        if player_id not in room.players:
            raise ValueError("PLAYER_NOT_IN_ROOM")

        player = room.players[player_id]
        if player.ready:
            raise ValueError("PLAYER_ALREADY_READY")
        if amount > player.balance:
            raise ValueError("INSUFFICIENT_BALANCE")

        state.place(player_id, amount)
        await self.room_repo.save(room)

        active_ids = list(room.players.keys())
        all_placed = state.all_placed(active_ids)

        logger.info(
            f"Bet placed — room={room_id} player={player_id} amount={amount} "
            f"pot={state.pot} all_placed={all_placed}"
        )
        return state, all_placed

    async def lock_betting(
        self,
        room_id: str,
        *,
        triggered_by: str = "dealer",
    ) -> tuple[BettingState, list[str]]:
        """
        Lock betting and mark non-betting players as folded.
        Returns (state, folded_player_ids).
        """
        room = await self._get_room(room_id)

        if room.phase != "betting":
            raise ValueError("NOT_BETTING_PHASE")

        state: BettingState = room.betting_state
        if state is None:
            raise ValueError("NO_BETTING_STATE")
        if state.locked:
            raise ValueError("BETTING_ALREADY_LOCKED")

        active_ids = list(room.players.keys())
        folded_ids = state.lock(active_ids)

        # Apply bets → ready flag; mark non-bettors as folded
        for pid, amount in state.bets.items():
            player = room.players.get(pid)
            if player:
                player.bet = amount
                player.ready = True

        for pid in folded_ids:
            player = room.players.get(pid)
            if player:
                player.folded = True
                logger.info(f"Player folded (no bet) — room={room_id} player={pid}")

        room.phase = "betting_locked"
        await self.room_repo.save(room)

        self._cancel_timeout(room_id)
        logger.info(
            f"Betting locked — room={room_id} pot={state.pot} "
            f"folded={folded_ids} triggered_by={triggered_by}"
        )
        return state, folded_ids

    async def kick_folded(
        self,
        room_id: str,
        dealer_sid: str,
    ) -> list[str]:
        """
        Remove all folded players from the room.
        Dealer calls this after a timeout before reopening betting.
        Returns the list of kicked player_ids.
        """
        room = await self._get_room(room_id)

        if room.dealer.id != dealer_sid:
            raise ValueError("ONLY_DEALER_CAN_KICK_PLAYERS")
        if room.phase != "betting_locked":
            raise ValueError("NOT_BETTING_LOCKED_PHASE")

        kicked = [pid for pid, p in room.players.items() if p.folded]
        for pid in kicked:
            del room.players[pid]
            logger.info(f"Folded player kicked — room={room_id} player={pid}")

        if not room.has_players():
            # All players folded — reset straight to waiting
            room.phase = "waiting"
            room.betting_state = None

        await self.room_repo.save(room)
        return kicked

    async def reset_betting(
        self,
        room_id: str,
        dealer_sid: str,
    ) -> None:
        """
        Reset room back to 'waiting' without starting a new bet round.
        Clears folded flags so all remaining players can bet again.
        Useful when dealer wants to cancel the locked round entirely.
        """
        room = await self._get_room(room_id)

        if room.dealer.id != dealer_sid:
            raise ValueError("ONLY_DEALER_CAN_RESET_BETTING")
        if room.phase not in ("betting_locked", "betting"):
            raise ValueError("NOTHING_TO_RESET")

        self._cancel_timeout(room_id)

        for player in room.players.values():
            player.reset()

        room.betting_state = None
        room.phase = "waiting"
        await self.room_repo.save(room)
        logger.info(f"Betting reset to waiting — room={room_id}")

    async def get_balance(self, player_id: str) -> int:
        player = await self.player_repo.get(player_id)
        if not player:
            raise ValueError("PLAYER_NOT_FOUND")
        return player.balance

    # ── Timeout internals ─────────────────────────────────────────────────

    async def _timeout_task(self, room_id: str, seconds: int) -> None:
        try:
            await asyncio.sleep(seconds)
        except asyncio.CancelledError:
            return

        logger.info(f"Betting timeout fired — room={room_id}")
        try:
            state, folded = await self.lock_betting(room_id, triggered_by="timeout")
            for cb in self._on_timeout:
                await cb(room_id, state, folded)
        except ValueError as exc:
            logger.warning(f"Timeout lock failed — room={room_id} reason={exc}")

    def _cancel_timeout(self, room_id: str) -> None:
        task = self._timeout_tasks.pop(room_id, None)
        if task and not task.done():
            task.cancel()

    def register_timeout_callback(self, coro_fn) -> None:
        """Register an async callback: coro_fn(room_id, state, folded_ids)."""
        self._on_timeout.append(coro_fn)

    # ── Helpers ───────────────────────────────────────────────────────────

    async def _get_room(self, room_id: str):
        room = await self.room_repo.get(room_id)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")
        return room