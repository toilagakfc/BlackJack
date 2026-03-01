# models.py

from typing import Dict, List


class PlayerState:
    def __init__(self, sid: str, name: str, is_dealer=False,ready=False):
        self.sid = sid
        self.name = name
        self.is_dealer = is_dealer
        self.ready = ready
        self.in_game = True


class Room:
    def __init__(self, room_id: str, dealer: PlayerState):
        self.room_id = room_id
        self.dealer_sid = dealer.sid
        self.players: Dict[str, PlayerState] = {dealer.sid: dealer}
        self.started = False
        self.turn_order = []        # [sid1, sid2, ..., dealer_sid]
        self.turn_index = 0
        self.phase = "PLAYER_TURN"  # PLAYER | DEALER | FINISHED
        self.finished_players = set()     # player đã stand / bust
        self.compared_players = set()     # player đã bị dealer compare
    def player_count(self):
        return len(self.players)

    def add_player(self, player: PlayerState):
        self.players[player.sid] = player

    def remove_player(self, sid: str):
        return self.players.pop(sid, None)