# game_server/domain/entities/game.py
from datetime import datetime
from domain.value_objects.deck import Deck
from domain.entities.player import Player
from domain.entities.dealer import Dealer
from domain.rules.xidach.hand_type import (
    is_bust, is_ngu_linh, can_stand, can_draw,
    dealer_should_draw, calc_point
)
from domain.rules.xidach.compare import compare


class Game:
    def __init__(self, dealer: Dealer, players: list[Player]):
        self.deck = Deck()
        self.players = players
        self.dealer = dealer
        self.turn_index = 0
        self.phase = "PLAYER_TURN"  # PLAYER_TURN | DEALER_TURN | FINISHED
        self.compared_players: set[Player] = set()
        self.started_at = datetime.now()
        self.updated_at: datetime | None = None
        self.ended_at: datetime | None = None

    # ── Setup ─────────────────────────────────────────────────────────────

    def initial_deal(self):
        """Chia 2 lá cho mỗi player và dealer."""
        for _ in range(2):
            for p in self.players:
                self._draw_for(p)
            self._draw_for(self.dealer)
            
    def init_turn(self):
        self.turn_index = 0
        self.phase = "PLAYER_TURN"

    # ── Turn control ──────────────────────────────────────────────────────

    def current_player(self) -> Player:
        return self.players[self.turn_index]

    def next_player(self):
        self.turn_index += 1
        if self.turn_index >= len(self.players):
            self.phase = "DEALER_TURN"
        self.updated_at = datetime.now()

    # ── Player actions ────────────────────────────────────────────────────

    def player_hit(self, player_id: str) -> Player:
        player = self._get_player_or_raise(player_id)

        if self.phase != "PLAYER_TURN":
            raise ValueError("NOT_PLAYER_PHASE")
        if player_id != self.current_player().id:
            raise ValueError("NOT_YOUR_TURN")
        if not can_draw(player.hand):
            raise ValueError("CANNOT_DRAW")

        self._draw_for(player)

        if is_bust(player.hand):
            player.busted == True
            self.next_player()
        elif is_ngu_linh(player.hand):
            self.next_player()

        return player

    def player_stand(self, player_id: str) -> Player:
        player = self._get_player_or_raise(player_id)

        if self.phase != "PLAYER_TURN":
            raise ValueError("NOT_PLAYER_PHASE")
        if player_id != self.current_player().id:
            raise ValueError("NOT_YOUR_TURN")
        if not can_stand(player.hand):
            raise ValueError("CANNOT_STAND")

        player.standing == True
        self.next_player()
        return player

    # ── Dealer actions ────────────────────────────────────────────────────

    def dealer_hit(self, dealer_id: str) -> bool:
        """Trả về True nếu dealer thực sự rút bài."""
        if self.dealer.id != dealer_id:
            raise ValueError("NOT_DEALER")
        if self.phase != "DEALER_TURN":
            raise ValueError("NOT_DEALER_PHASE")
        should = dealer_should_draw(self.dealer.hand)
        if should:
            self._draw_for(self.dealer)
            self.updated_at = datetime.now()
            return True
        return False

    def dealer_compare(self, dealer_id: str, player_id: str) -> dict:
        if self.dealer.id != dealer_id:
            raise ValueError("NOT_DEALER")

        should = dealer_should_draw(self.dealer.hand)
        if should:
            raise ValueError("Dealer Cannot Compare")
        player = self._get_player_or_raise(player_id)

        if player in self.compared_players:
            raise ValueError("ALREADY_COMPARED")

        result = compare(player.hand, self.dealer.hand)
        self.compared_players.add(player)

        if len(self.compared_players) == len(self.players):
            self.phase = "FINISHED"
            self.ended_at = datetime.now()

        self.updated_at = datetime.now()
        return result

    def dealer_compare_all(self, dealer_id: str) -> dict:
        """So sánh tất cả player chưa được compare."""
        return {
            p.id: self.dealer_compare(dealer_id, p.id)
            for p in self.players
            if p not in self.compared_players
        }

    # ── Internal ──────────────────────────────────────────────────────────

    def _draw_for(self, target: Player) -> None:
        card = self.deck.draw()
        target.receive_card(card)

    def _get_player_or_raise(self, player_id: str) -> Player:
        player = self.get_player_by_id(player_id)
        if not player:
            raise ValueError("PLAYER_NOT_FOUND")
        return player

    def get_player_by_id(self, player_id: str) -> Player | None:
        return next((p for p in self.players if p.id == player_id), None)

    # ── Reset ─────────────────────────────────────────────────────────────

    def reset(self):
        self.deck.reset()
        for p in self.players:
            p.reset()
        self.dealer.reset()
        self.turn_index = 0
        self.phase = "PLAYER_TURN"
        self.compared_players.clear()
        self.started_at = datetime.now()
        self.updated_at = None
        self.ended_at = None

    # ── Serialization ─────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "dealer": self.dealer.to_dict() if self.dealer else None,
            "players": {p.id: p.to_dict() for p in self.players},
            "deck_drawn": self.deck.drawn_indices, 
            "turn_index": self.turn_index,
            "phase": self.phase,
            "compared_players": {p.id: p.to_dict() for p in self.compared_players},
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
        }