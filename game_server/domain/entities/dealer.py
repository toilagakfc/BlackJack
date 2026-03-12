from domain.entities.player import Player


class Dealer(Player):
    def __init__(self, sid: str, name: str, ready: bool = True, is_dealer: bool = True):
        super().__init__(player_id=sid, name=name, ready=ready, is_dealer=is_dealer)