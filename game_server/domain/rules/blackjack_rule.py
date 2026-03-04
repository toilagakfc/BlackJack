class XiDachHandRule:
    MAX_CARDS = 5

    @staticmethod
    def card_value(card) -> int:
        if card.rank in ("J", "Q", "K"):
            return 10
        if card.rank == "A":
            return 11
        return int(card.rank)

    @staticmethod
    def calc_point(hand) -> int:
        total = 0
        ace_count = 0

        for c in hand.cards():
            if c.rank == "A":
                ace_count += 1
            else:
                total += XiDachHandRule.card_value(c)

        if ace_count == 0:
            return total

        card_num = hand.count()

        if card_num == 2:
            total += 11
        elif card_num == 3:
            total += 10 if total + 10 <= 28 else 1
        else:
            total += ace_count

        return total

    @staticmethod
    def is_bust(hand) -> bool:
        return XiDachHandRule.calc_point(hand) > 21

    @staticmethod
    def is_blackjack(hand) -> bool:
        if hand.count() != 2:
            return False
        ranks = [c.rank for c in hand.cards()]
        return ("A" in ranks) and any(r in ("10", "J", "Q", "K") for r in ranks)

    @staticmethod
    def is_xi_bang(hand) -> bool:
        return hand.count() == 2 and all(c.rank == "A" for c in hand.cards())

    @staticmethod
    def is_ngu_linh(hand) -> bool:
        return hand.count() == 5 and XiDachHandRule.calc_point(hand) < 21

    @staticmethod
    def can_draw(hand) -> bool:
        return hand.count() < XiDachHandRule.MAX_CARDS

    @staticmethod
    def can_stand(hand) -> bool:
        return XiDachHandRule.calc_point(hand) >= 16

    @staticmethod
    def dealer_should_draw(hand) -> bool:
        return XiDachHandRule.calc_point(hand) < 15