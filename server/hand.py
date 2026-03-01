# hand.py

class Hand:
    def __init__(self):
        self.cards = []

    # ---------- basic ----------
    def reset(self):
        self.cards.clear()

    def add_card(self, card):
        self.cards.append(card)

    def card_count(self) -> int:
        return len(self.cards)

    # ---------- special hands ----------
    def has_blackjack(self) -> bool:
        """
        Xì dách: 2 lá = A + 10/J/Q/K
        """
        if self.card_count() != 2:
            return False
        ranks = [c.rank for c in self.cards]
        return ("A" in ranks) and any(r in ("10", "J", "Q", "K") for r in ranks)

    def is_xi_bang(self) -> bool:
        """
        Xì bàng: 2 lá A
        """
        if self.card_count() != 2:
            return False
        return all(c.rank == "A" for c in self.cards)

    def is_ngu_linh(self) -> bool:
        """
        Ngũ linh: đủ 5 lá và < 21 điểm
        """
        return self.card_count() == 5 and self.calculate_point() < 21

    # ---------- point calculation ----------
    def calculate_point(self, hide_dealer_cards=False) -> int:
        """
        Luật A theo xì dách VN:
        - 2 lá có A  -> A = 11
        - 3 lá có A  -> A = 10 hoặc 1 (chọn tốt nhất <= 28)
        - >=4 lá có A -> A = 1
        """
        total = 0
        ace_count = 0

        for c in self.cards:
            if c.rank == "A":
                ace_count += 1
            else:
                total += c.base_value()

        if ace_count == 0:
            return total

        card_num = self.card_count()

        # 2 lá
        if card_num == 2:
            total += 11

        # 3 lá
        elif card_num == 3:
            if total + 10 <= 28:
                total += 10
            else:
                total += 1

        # 4–5 lá
        else:
            total += ace_count * 1

        if hide_dealer_cards:
            return None
        return total

    # ---------- status ----------
    def is_bust(self) -> bool:
        return self.calculate_point() > 21

    def __repr__(self):
        return f"Hand({self.cards})"
    
    def to_public_dict(self, hide_dealer_cards=False):
        if hide_dealer_cards:
            return [{"hidden": True} for _ in self.cards]
        else:
            return [card.to_dict() for card in self.cards]