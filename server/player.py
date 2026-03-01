# player.py

from hand import Hand


class Player:
    def __init__(self, name: str):
        self.name = name
        self.hand = Hand()
        self.stand = False

    def reset(self):
        self.hand = Hand()
        self.stand = False

    def draw(self, deck) -> bool:
        """
        Rút thêm bài
        - Tối đa 5 lá
        """
        if self.hand.card_count() >= 5:
            return False
        self.hand.add_card(deck.draw())
        return True

    def can_stand(self) -> bool:
        """
        Player chỉ được dừng khi >= 16 điểm
        """
        return self.hand.calculate_point() >= 16

    def is_bust(self) -> bool:
        return self.hand.calculate_point() > 21

    def is_ngu_linh(self) -> bool:
        return self.hand.is_ngu_linh()

    def is_xi_dach(self) -> bool:
        return self.hand.has_blackjack()

    def is_xi_bang(self) -> bool:
        return self.hand.is_xi_bang()


class Dealer(Player):
    def __init__(self, name: str = "Nhà cái"):
        super().__init__(name)

    def should_draw(self) -> bool:
        """
        Nhà cái rút khi < 15 điểm
        """
        return self.hand.calculate_point() < 15