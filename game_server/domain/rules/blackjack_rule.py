from domain.value_objects.card import Card
from domain.value_objects.hand import Hand
class XiDachHandRule:
    MAX_CARDS = 5

    @staticmethod
    def card_value(card:Card) -> int:
        if card.rank in ("J", "Q", "K"):
            return 10
        if card.rank == "A":
            return 11
        return int(card.rank)

    @staticmethod
    def calc_point(hand: Hand) -> int:
        total = 0
        aces = 0
        card_num = hand.count()

        for c in hand.cards():
            if c.rank == "A":
                aces += 1
            else:
                total += XiDachHandRule.card_value(c)

        if aces == 0:
            return total

        if card_num == 2:
            return total + 11

        if card_num == 3:
            # 1 Át có thể =10
            if total + 10 <= 28:
                total += 10
                aces -= 1
            else:
                total += 1
                aces -= 1

            total += aces
            return total

        total += aces
        return total

    @staticmethod
    def is_bust(hand:Hand) -> bool:
        return XiDachHandRule.calc_point(hand) > 21

    @staticmethod
    def is_blackjack(hand:Hand) -> bool:
        if hand.count() != 2:
            return False
        ranks = [c.rank for c in hand.cards()]
        return ("A" in ranks) and any(r in ("10", "J", "Q", "K") for r in ranks)

    @staticmethod
    def is_xi_bang(hand:Hand) -> bool:
        return hand.count() == 2 and all(c.rank == "A" for c in hand.cards())

    @staticmethod
    def is_ngu_linh(hand:Hand) -> bool:
        return hand.count() == 5 and XiDachHandRule.calc_point(hand) < 21

    @staticmethod
    def can_draw(hand:Hand) -> bool:
        return hand.count() < XiDachHandRule.MAX_CARDS

    @staticmethod
    def can_stand(hand:Hand) -> bool:
        return XiDachHandRule.calc_point(hand) >= 16

    @staticmethod
    def dealer_should_draw(hand:Hand) -> bool:
        return XiDachHandRule.calc_point(hand) < 15