from domain.entities.player import Player


class Dealer(Player):
    def __init__(self):
        super().__init__(player_id="dealer", name="Nhà cái")