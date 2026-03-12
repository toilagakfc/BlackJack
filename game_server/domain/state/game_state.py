# game_server/domain/state/game_state.py
from __future__ import annotations
from dataclasses import dataclass, field
from domain.state.player_state import PlayerState

from domain.entities.game import Game


@dataclass
class GameState:
    """
    DTO emit qua socket — tách biệt với Game entity.
    """
    room_id: str
    phase: str
    turn_index: int
    current_player_id: str | None
    dealer_id: str 
    dealer_cards: list[dict]
    dealer_card_count: int
    players: list[PlayerState] = field(default_factory=list)

    @classmethod
    def from_game(cls, room_id: str, game: Game) -> GameState:
        current = game.current_player() if game.phase == "PLAYER_TURN" else None
        return cls(
            room_id=room_id,
            dealer_id=game.dealer.id,
            phase=game.phase,
            turn_index=game.turn_index,
            current_player_id=current.id if current else None,
            dealer_cards=game.dealer.hand.to_dict()["cards"],
            dealer_card_count=game.dealer.hand.count(),
            players=[PlayerState.from_player(p) for p in game.players],
        )

    def to_public(self, viewer_id: str | None = None) -> dict:
        """
        Dùng để broadcast — ẩn bài của tất cả player.
        Nếu truyền viewer_id thì player đó thấy bài của mình.
        """
        return {
            "room_id": self.room_id,
            "phase": self.phase,
            "turn_index": self.turn_index,
            "current_player_id": self.current_player_id,
            "dealer": {
                "cards": [{"rank": "?", "suit": "?"}] * self.dealer_card_count
                if self.phase != "FINISHED" else self.dealer_cards,
                "card_count": self.dealer_card_count,
            },
            "players": [
                p.to_private() if p.id == viewer_id else p.to_public()
                for p in self.players
            ],
        }

    def to_dict(self) -> dict:
        """Full state — dùng nội bộ / debug."""
        return {
            "room_id": self.room_id,
            "phase": self.phase,
            "turn_index": self.turn_index,
            "current_player_id": self.current_player_id,
            "dealer_cards": self.dealer_cards,
            "players": [p.to_private() for p in self.players],
        }

    @staticmethod
    def from_dict(data: dict) -> "GameState":
        return GameState(
            room_id=data["room_id"],
            phase=data["phase"],
            turn_index=data["turn_index"],
            current_player_id=data.get("current_player_id"),
            dealer_cards=data["dealer_cards"],
            dealer_card_count=len(data["dealer_cards"]),
        )
        
    def to_dealer(self) -> dict:
        """Dealer thấy tất cả — bài mình + bài từng player."""
        return {
            "room_id": self.room_id,
            "phase": self.phase,
            "turn_index": self.turn_index,
            "current_player_id": self.current_player_id,
            "dealer": {
                "cards": self.dealer_cards,
                "card_count": self.dealer_card_count,
            },
            "players": [p.to_public() for p in self.players],  # ẩn bài player
        }