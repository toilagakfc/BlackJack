# tests/test_betting.py
"""
Unit tests for the betting system.
Run with: pytest tests/test_betting.py -v
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game_server"))

from game_server.domain.state.betting_state import BettingState
from game_server.application.betting_service import BettingService


# ── BettingState unit tests ───────────────────────────────────────────────

class TestBettingState:

    def _make_state(self, player_ids=("p1", "p2", "p3")) -> BettingState:
        return BettingState(
            room_id="ROOM01",
            player_balance={pid: 1000 for pid in player_ids},
            min_bet=10,
            max_bet=500,
        )

    def test_place_bet_success(self):
        state = self._make_state()
        state.place_bet("p1", 100)
        assert state.player_bets["p1"] == 100
        assert state.pot == 100

    def test_place_bet_below_minimum(self):
        state = self._make_state()
        with pytest.raises(ValueError, match="BET_BELOW_MINIMUM"):
            state.place_bet("p1", 5)

    def test_place_bet_above_maximum(self):
        state = self._make_state()
        with pytest.raises(ValueError, match="BET_ABOVE_MAXIMUM"):
            state.place_bet("p1", 600)

    def test_place_bet_insufficient_balance(self):
        state = self._make_state()
        with pytest.raises(ValueError, match="INSUFFICIENT_BALANCE"):
            state.place_bet("p1", 1001)

    def test_double_bet_rejected(self):
        state = self._make_state()
        state.place_bet("p1", 100)
        with pytest.raises(ValueError, match="BET_ALREADY_PLACED"):
            state.place_bet("p1", 200)

    def test_bet_locked_raises(self):
        state = self._make_state()
        state.lock()
        with pytest.raises(ValueError, match="BETTING_LOCKED"):
            state.place_bet("p1", 100)

    def test_fold_player_removes_bet(self):
        state = self._make_state()
        state.player_bets["p1"] = 100
        state.pot = 100
        state.fold_player("p1")
        assert "p1" not in state.player_bets
        assert state.pot == 0
        assert "p1" in state.folded_players

    def test_fold_player_no_bet(self):
        state = self._make_state()
        state.fold_player("p1")
        assert "p1" in state.folded_players
        assert state.pot == 0

    def test_all_active_players_bet_true(self):
        state = self._make_state(["p1", "p2"])
        state.place_bet("p1", 50)
        state.place_bet("p2", 75)
        assert state.all_active_players_bet(["p1", "p2"]) is True

    def test_all_active_players_bet_false(self):
        state = self._make_state(["p1", "p2"])
        state.place_bet("p1", 50)
        assert state.all_active_players_bet(["p1", "p2"]) is False

    def test_folded_player_excluded_from_all_bet_check(self):
        state = self._make_state(["p1", "p2"])
        state.place_bet("p1", 50)
        state.fold_player("p2")
        # p2 is folded — p1 has bet — should be True
        assert state.all_active_players_bet(["p1", "p2"]) is True

    def test_pot_accumulates(self):
        state = self._make_state()
        state.place_bet("p1", 100)
        state.place_bet("p2", 200)
        state.place_bet("p3", 50)
        assert state.pot == 350

    def test_serialization_roundtrip(self):
        state = self._make_state()
        state.place_bet("p1", 100)
        state.fold_player("p3")
        state.deadline = datetime.now(timezone.utc) + timedelta(seconds=30)
        data = state.to_dict()
        restored = BettingState.from_dict(data)
        assert restored.pot == state.pot
        assert restored.player_bets == state.player_bets
        assert restored.folded_players == state.folded_players
        assert restored.min_bet == state.min_bet

    def test_is_expired_false(self):
        state = self._make_state()
        state.deadline = datetime.now(timezone.utc) + timedelta(seconds=30)
        assert state.is_expired() is False

    def test_is_expired_true(self):
        state = self._make_state()
        state.deadline = datetime.now(timezone.utc) - timedelta(seconds=1)
        assert state.is_expired() is True


# ── BettingService unit tests (mocked repos) ─────────────────────────────

class TestBettingService:

    def _make_service(self, state=None, room=None):
        betting_repo = AsyncMock()
        betting_repo.get = AsyncMock(return_value=state)
        betting_repo.save = AsyncMock()
        betting_repo.delete = AsyncMock()

        room_repo = AsyncMock()
        if room:
            room_repo.get = AsyncMock(return_value=room)

        player_repo = AsyncMock()
        player_repo.get_many = AsyncMock(return_value={
            "p1": MagicMock(balance=500),
            "p2": MagicMock(balance=800),
        })

        service = BettingService(
            betting_repo=betting_repo,
            room_repo=room_repo,
            player_repo=player_repo,
            timeout_seconds=1,
            min_bet=10,
            max_bet=1000,
        )
        return service, betting_repo, room_repo

    def _make_room(self, dealer_id="dealer1", player_ids=("p1", "p2")):
        room = MagicMock()
        room.id = "ROOM01"
        room.dealer.id = dealer_id
        room.phase = "waiting"
        room.has_players.return_value = True
        room.all_ready.return_value = True
        room.players = {pid: MagicMock(id=pid) for pid in player_ids}
        return room

    @pytest.mark.asyncio
    async def test_start_betting_success(self):
        room = self._make_room()
        service, betting_repo, _ = self._make_service(room=room)
        on_timeout = AsyncMock()

        state = await service.start_betting("ROOM01", "dealer1", on_timeout)
        assert state.room_id == "ROOM01"
        assert "p1" in state.player_balance
        betting_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_betting_not_dealer_raises(self):
        room = self._make_room()
        service, _, _ = self._make_service(room=room)
        with pytest.raises(ValueError, match="ONLY_DEALER"):
            await service.start_betting("ROOM01", "not_dealer", AsyncMock())

    @pytest.mark.asyncio
    async def test_place_bet_success(self):
        room = self._make_room()
        existing_state = BettingState(
            room_id="ROOM01",
            player_balance={"p1": 500, "p2": 800},
        )
        service, betting_repo, _ = self._make_service(state=existing_state, room=room)

        state, all_in = await service.place_bet("ROOM01", "p1", 100)
        assert state.player_bets["p1"] == 100
        assert state.pot == 100
        assert all_in is False
        betting_repo.save.assert_called()

    @pytest.mark.asyncio
    async def test_place_bet_both_players_triggers_all_in(self):
        room = self._make_room()
        existing_state = BettingState(
            room_id="ROOM01",
            player_balance={"p1": 500, "p2": 800},
        )
        existing_state.place_bet("p1", 100)  # p1 already bet

        service, _, _ = self._make_service(state=existing_state, room=room)
        _, all_in = await service.place_bet("ROOM01", "p2", 200)
        assert all_in is True

    @pytest.mark.asyncio
    async def test_handle_timeout_folds_non_bettors(self):
        room = self._make_room()
        existing_state = BettingState(
            room_id="ROOM01",
            player_balance={"p1": 500, "p2": 800},
        )
        existing_state.place_bet("p1", 100)  # only p1 bet

        service, betting_repo, _ = self._make_service(state=existing_state, room=room)
        state = await service.handle_timeout("ROOM01")

        assert "p2" in state.folded_players
        assert "p1" not in state.folded_players
        assert state.betting_locked is True

    @pytest.mark.asyncio
    async def test_fold_disconnected_player(self):
        existing_state = BettingState(
            room_id="ROOM01",
            player_balance={"p1": 500},
        )
        room = self._make_room()
        service, betting_repo, _ = self._make_service(state=existing_state, room=room)

        result = await service.fold_disconnected_player("ROOM01", "p1")
        assert "p1" in result.folded_players

    @pytest.mark.asyncio
    async def test_fold_disconnected_locked_state_returns_none(self):
        existing_state = BettingState(room_id="ROOM01")
        existing_state.lock()
        room = self._make_room()
        service, _, _ = self._make_service(state=existing_state, room=room)

        result = await service.fold_disconnected_player("ROOM01", "p1")
        assert result is None   # locked — no change

    @pytest.mark.asyncio
    async def test_check_balance(self):
        existing_state = BettingState(
            room_id="ROOM01",
            player_balance={"p1": 750},
        )
        service, _, _ = self._make_service(state=existing_state)
        balance = await service.check_balance("ROOM01", "p1")
        assert balance == 750