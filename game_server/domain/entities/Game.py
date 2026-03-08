# game_server/domain/entities/Game.py
from domain.value_objects.deck import Deck
from domain.entities.player import Player
from domain.entities.dealer import Dealer
from domain.rules.blackjack_compare_rule import XiDachHandRule, XiDachCompareRule
from presentation.serializers.card_serializer import serialize_hand

class Game:
    def __init__(self, dealer: Dealer,players: list[Player]):
        self.deck = Deck()
        self.xidach_rule = XiDachHandRule()
        self.xidach_compare_rule = XiDachCompareRule()
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
                print(f"Player {p.name} Hand on: {p.hand.cards()}")
            self._draw_for(self.dealer)
            print(f"Dealer Hand on: {self.dealer.hand.cards()}")
        

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

    def player_hit(self, player_id):
        player = self.get_player_by_id(player_id)
        if self.phase != "PLAYER_TURN":
            raise ValueError("NOT_PLAYER_PHASE")

        if player_id is not self.current_player().id:
            raise ValueError("NOT_YOUR_TURN")

        if not self.xidach_rule.can_draw(player.hand):
            raise ValueError("CANNOT_DRAW")

        self._draw_for(player)

        if (self.xidach_rule.is_bust(player.hand) or self.xidach_rule.is_ngu_linh(player.hand)):
            self.next_player()

    def player_stand(self, player_id):
        player = self.get_player_by_id(player_id)
        if self.phase != "PLAYER_TURN":
            raise ValueError("NOT_PLAYER_PHASE")

        if player_id is not self.current_player().id:
            raise ValueError("NOT_YOUR_TURN")
        
        if not self.xidach_rule.can_stand(player.hand):
            raise ValueError("CANNOT_STAND")

        player.stand()
        self.next_player()

    # ---------- dealer actions ----------

    def dealer_hit(self,dealer_id):
        if self.dealer.id != dealer_id:
            raise ValueError("NOT_DEALER")
        if self.phase != "DEALER_TURN":
            raise ValueError("NOT_DEALER_PHASE")

        if self.xidach_rule.dealer_should_draw(self.dealer.hand):
            self._draw_for(self.dealer)

    def dealer_compare(self, dealer_id,player_id):
        if self.dealer.id != dealer_id:
            raise ValueError("NOT_DEALER")
        player = self.get_player_by_id(player_id)
        if player in self.compared_players:
            raise ValueError("ALREADY_COMPARED")

        result = self.xidach_compare_rule.compare(
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
                    # "cards": p.hand.cards(),
                    "point": self.xidach_rule.calc_point(p.hand),
                    "index":i
                }
                for i,p in enumerate(self.players)
            ],
            "dealer": {
                # "cards": (
                #     self.dealer.hand.cards()
                #     if not hide_dealer_cards
                #     else [self.dealer.hand.cards()[0]] + [{"rank": "Hidden", "suit": "Hidden"}]
                # ),
                # "cards": self.dealer.hand.cards(),
                "point": (
                    self.xidach_rule.calc_point(self.dealer.hand)
                    if not hide_dealer_cards
                    else None
                ),
            },
            "phase": self.phase,
        }
    
    def get_player_by_id(self,player_id):
        for player in self.players:
            if player.id == player_id:
                return player