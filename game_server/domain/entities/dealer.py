from domain.entities.player import Player


class Dealer(Player):
    def __init__(self, player_id: str, name: str, ready: bool = True, is_dealer: bool = True, balance: int = 0):
        super().__init__(player_id=player_id, name=name, ready=ready, is_dealer=is_dealer,balance=balance)