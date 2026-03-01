# game_engine.py

from deck import Deck
from player import Player, Dealer
from rules import XiDachRules


class GameEngine:
    def __init__(self, room):
        """
        room:
          - room.players : dict[sid -> PlayerState]
          - room.dealer_sid
        """
        self.room = room
        self.deck = Deck()

        self.players = {}          # sid -> Player
        self.dealer = None         # Dealer instance

        self.finished_players = set()   # player stand / bust / ngu linh
        self.compared_players = set()   # player đã bị dealer compare

        self._init_players()

    # ---------- init player----------

    def _init_players(self):
        for sid, ps in self.room.players.items():
            if sid == self.room.dealer_sid:
                self.dealer = Dealer(ps.name)
            else:
                self.players[sid] = Player(ps.name)
        print("Initialized players:", self.players)
    
    # ---------- game flow ----------
    def initial_deal(self):
        """
        Chia 2 lá cho từng player theo thứ tự join,
        dealer chia cuối
        """
        order = [sid for sid in self.room.players if sid != self.room.dealer_sid]

        for _ in range(2):
            for sid in order:
                self.players[sid].draw(self.deck)
            self.dealer.draw(self.deck)
    #init turn: xác định thứ tự turn, reset trạng thái player finished / compared    
    def init_turn(self):
    # player theo thứ tự join, dealer cuối
        # self.room.turn_order = [sid for sid in self.room.players if sid != self.room.dealer_sid]
        self.room.turn_index = 0
        # self.room.turn_order = player_sids + [self.room.dealer_sid]
        self.room.phase = "PLAYER_TURN"

    # ---------- player actions ----------
    def current_player_sid(self):
        return self.room.turn_order[self.room.turn_index]
    
    def player_action(self, sid, action):
        # check đúng turn
        if self.current_player_sid() != sid:
            raise ValueError("NOT_YOUR_TURN")

        player = self.players[sid]

        if action == "hit":
            player.draw(self.deck)

            # nếu quắc / ngũ linh → auto kết thúc turn
            if player.is_bust() or player.is_ngu_linh():
                self._next_player()

        elif action == "stand":
            # chưa đủ 16 điểm thì không cho dừng
            if not player.can_stand():
                raise ValueError("CANNOT_STAND_BELOW_16")
            self._next_player()

        else:
            raise ValueError("INVALID_ACTION")
        
    def _next_player(self):
        self.room.turn_index += 1

        # hết player → sang dealer
        if self.room.turn_index >= len(self.room.turn_order)-1:
            print("All players finished, moving to dealer phase")
            self.room.phase = "DEALER_COMPARE"
    # ---------- dealer actions ----------
    def is_dealer_phase(self):
        return (
            self.room.phase == "DEALER_COMPARE"
            and self.current_player_sid() == self.room.dealer_sid
        )
    def dealer_hit(self):
        """
        Dealer rút thêm bài.
        PHẢI public điểm ra ngoài.
        """
        self.dealer.draw(self.deck)

    def dealer_compare(self, target_sid):
        """
        Dealer so bài với 1 player chỉ định
        """
        if target_sid in self.compared_players:
            raise ValueError("PLAYER_ALREADY_COMPARED")
        player = self.players[target_sid]

        print("Comparing dealer with player", player.name)
        result = XiDachRules.compare(player, self.dealer)

        self.compared_players.add(target_sid)

        return {
            "player_sid": target_sid,
            "player_name": player.name,
            "result": result,
        }

    def compare_all(self):
        """
        Dealer so bài với tất cả player chưa bị compare
        """
        results = {}

        for sid, player in self.players.items():
            if sid in self.compared_players:
                continue

            results[sid] = {
                "player_name": player.name,
                "result": XiDachRules.compare(player, self.dealer),
            }

        return results

    # ---------- public state ----------

    def public_state(self, hide_dealer_cards=True):
        """
        State gửi cho client (không lộ bài dealer nếu chưa muốn)
        """
        return {
            "players": {
                p.name: {
                    "cards": p.hand.to_public_dict(hide_dealer_cards=hide_dealer_cards),
                    "point": p.hand.calculate_point(hide_dealer_cards=hide_dealer_cards),
                    # "finished": sid in self.finished_players,
                    # "compared": sid in self.compared_players,
                }
                for sid, p in self.players.items()
            },
            "dealer": {
                "card_count": self.dealer.hand.to_public_dict(hide_dealer_cards=hide_dealer_cards),
                "point": self.dealer.hand.calculate_point(hide_dealer_cards=hide_dealer_cards),
            },
        }