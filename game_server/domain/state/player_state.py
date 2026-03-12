# game_server/domain/state/player_state.py
from __future__ import annotations
from dataclasses import dataclass, field

from domain.entities.player import Player


@dataclass
class PlayerState:
    """
    DTO dùng để emit qua socket.
    Tách biệt hoàn toàn với domain entity Player.
    """
    id: str
    name: str
    balance: int
    ready: bool
    is_dealer: bool
    standing: bool
    busted: bool
    bet: int
    cards: list[dict]           # public — gửi cho chính player đó
    cards_hidden: list[dict]    # ẩn cards — gửi broadcast cho người khác
    card_count: int

    @classmethod
    def from_player(cls, player: Player) -> PlayerState:
        cards = player.hand.to_dict()["cards"]
        return cls(
            id=player.id,
            name=player.name,
            balance=player.balance,
            ready=player.ready,
            is_dealer=player.is_dealer,
            standing=player.standing,
            busted=player.busted,
            bet=player.bet,
            cards=cards,
            cards_hidden=[{"rank": "?", "suit": "?"} for _ in cards],
            card_count=player.hand.count(),
        )

    def to_public(self) -> dict:
        """Broadcast — ẩn bài của player."""
        return {
            "id": self.id,
            "name": self.name,
            "balance": self.balance,
            "standing": self.standing,
            "busted": self.busted,
            "bet": self.bet,
            "cards": self.cards_hidden,
            "card_count": self.card_count,
        }

    def to_private(self) -> dict:
        """Gửi riêng cho chính player đó — show bài thật."""
        return {
            **self.to_public(),
            "cards": self.cards,
            "ready": self.ready,
        }