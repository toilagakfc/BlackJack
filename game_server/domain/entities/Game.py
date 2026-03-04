# game_server/domain/entities/Game.py
from domain.value_objects.deck import Deck
from domain.entities.player import Player
from domain.entities.dealer import Dealer
from domain.rules.blackjack_compare_rule import XiDachHandRule, XiDachCompareRule


class Game:
    def __init__(self, players: list[Player], dealer: Dealer):
        self.deck = Deck()

        self.players = players            # list[Player]
        self.dealer = dealer

        self.turn_index = 0
        self.phase = "PLAYER_TURN"         # PLAYER_TURN | DEALER_TURN | FINISHED

        self.compared_players = set()

    # ---------- setup ----------

    def initial_deal(self):
        for _ in range(2):
            for p in self.players:
                self._draw_for(p)
            self._draw_for(self.dealer)

    def init_turn(self):
        self.turn_index = 0
        self.phase = "PLAYER_TURN"
    # ---------- turn control ----------

    def current_player(self) -> Player:
        return self.players[self.turn_index]

    def next_player(self):
        self.turn_index += 1
        if self.turn_index >= len(self.players):
            self.phase = "DEALER_TURN"

    # ---------- player actions ----------

    def player_hit(self, player: Player):
        if self.phase != "PLAYER_TURN":
            raise ValueError("NOT_PLAYER_PHASE")

        if player is not self.current_player():
            raise ValueError("NOT_YOUR_TURN")

        if not XiDachHandRule.can_draw(player.hand):
            raise ValueError("CANNOT_DRAW")

        self._draw_for(player)

        if (
            XiDachHandRule.is_bust(player.hand)
            or XiDachHandRule.is_ngu_linh(player.hand)
        ):
            self.next_player()

    def player_stand(self, player: Player):
        if not XiDachHandRule.can_stand(player.hand):
            raise ValueError("CANNOT_STAND")

        player.stand()
        self.next_player()

    # ---------- dealer actions ----------

    def dealer_hit(self):
        if self.phase != "DEALER_TURN":
            raise ValueError("NOT_DEALER_PHASE")

        if XiDachHandRule.dealer_should_draw(self.dealer.hand):
            self._draw_for(self.dealer)

    def dealer_compare(self, player: Player):
        if player in self.compared_players:
            raise ValueError("ALREADY_COMPARED")

        result = XiDachCompareRule.compare(
            player.hand,
            self.dealer.hand
        )

        self.compared_players.add(player)

        if len(self.compared_players) == len(self.players):
            self.phase = "FINISHED"

        return result

    def dealer_compare_all(self):
        results = {}
        for p in self.players:
            if p not in self.compared_players:
                results[p.id] = self.dealer_compare(p)
        return results

    # ---------- internal ----------

    def _draw_for(self, target):
        card = self.deck.draw()
        target.receive_card(card)
        
    def reset(self):
        self.deck.reset()
        for p in self.players:
            p.reset()
        self.dealer.reset()
        self.turn_index = 0
        self.phase = "PLAYER_TURN"
        self.compared_players.clear()
    
    def public_state(self, hide_dealer_cards=False):
        return {
            "players": [
                {
                    "id": p.id,
                    "name": p.name,
                    "cards": [c.serialize() for c in p.hand.cards()],
                    "point": XiDachHandRule.calc_point(p.hand),
                }
                for p in self.players
            ],
            "dealer": {
                "cards": (
                    [c.serialize() for c in self.dealer.hand.cards()]
                    if not hide_dealer_cards
                    else [self.dealer.hand.cards()[0].serialize()] + [{"rank": "Hidden", "suit": "Hidden"}]
                ),
                "point": (
                    XiDachHandRule.calc_point(self.dealer.hand)
                    if not hide_dealer_cards
                    else None
                ),
            },
            "phase": self.phase,
        }