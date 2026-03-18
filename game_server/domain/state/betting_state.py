# game_server/domain/state/betting_state.py
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BettingState:
    """
    Tracks one betting round.
    Owned by Room during the BETTING phase; discarded when betting is locked.
    """
    room_id: str
    min_bet: int
    max_bet: int
    timeout_seconds: int
    opened_at: datetime = field(default_factory=datetime.now)

    # player_id → amount (only players who submitted)
    bets: dict[str, int] = field(default_factory=dict)
    locked: bool = False

    # ── Queries ───────────────────────────────────────────────────────────

    @property
    def pot(self) -> int:
        return sum(self.bets.values())

    def has_bet(self, player_id: str) -> bool:
        return player_id in self.bets

    def all_placed(self, player_ids: list[str]) -> bool:
        """True when every active player has submitted a bet."""
        return all(pid in self.bets for pid in player_ids)

    # ── Commands ──────────────────────────────────────────────────────────

    def place(self, player_id: str, amount: int) -> None:
        if self.locked:
            raise ValueError("BETTING_LOCKED")
        if self.has_bet(player_id):
            raise ValueError("BET_ALREADY_PLACED")
        if amount < self.min_bet:
            raise ValueError(f"BET_BELOW_MIN_{self.min_bet}")
        if amount > self.max_bet:
            raise ValueError(f"BET_ABOVE_MAX_{self.max_bet}")
        self.bets[player_id] = amount

    def lock(self, all_player_ids: list[str]) -> list[str]:
        """
        Finalise the betting round.
        Returns list of player_ids who did NOT bet (folded).
        """
        self.locked = True
        folded = [pid for pid in all_player_ids if pid not in self.bets]
        return folded

    # ── Serialization ─────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "room_id": self.room_id,
            "min_bet": self.min_bet,
            "max_bet": self.max_bet,
            "timeout_seconds": self.timeout_seconds,
            "opened_at": self.opened_at.isoformat(),
            "bets": self.bets,
            "locked": self.locked,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BettingState":
        obj = cls(
            room_id=data["room_id"],
            min_bet=data["min_bet"],
            max_bet=data["max_bet"],
            timeout_seconds=data["timeout_seconds"],
            opened_at=datetime.fromisoformat(data["opened_at"]),
        )
        obj.bets = data.get("bets", {})
        obj.locked = data.get("locked", False)
        return obj