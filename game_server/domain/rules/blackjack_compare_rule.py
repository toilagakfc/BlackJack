
from game_server.domain.rules.blackjack_rule import XiDachHandRule

class XiDachCompareRule:
    @staticmethod
    def compare(player_hand, dealer_hand):
        p_point = XiDachHandRule.calc_point(player_hand)
        d_point = XiDachHandRule.calc_point(dealer_hand)

        # 1. Blackjack
        if XiDachHandRule.is_blackjack(dealer_hand) and not XiDachHandRule.is_blackjack(player_hand):
            return ("LOSE", "DEALER_BLACKJACK", 0)

        if XiDachHandRule.is_blackjack(player_hand) and not XiDachHandRule.is_blackjack(dealer_hand):
            return ("WIN", "PLAYER_BLACKJACK", 1)

        if XiDachHandRule.is_blackjack(player_hand) and XiDachHandRule.is_blackjack(dealer_hand):
            return ("DRAW", "BOTH_BLACKJACK", 0)

        # 2. Xì bàng
        if XiDachHandRule.is_xi_bang(player_hand) and not XiDachHandRule.is_xi_bang(dealer_hand):
            return ("WIN", "PLAYER_XI_BANG", 2)

        if XiDachHandRule.is_xi_bang(dealer_hand) and not XiDachHandRule.is_xi_bang(player_hand):
            return ("LOSE", "DEALER_XI_BANG", 2)

        if XiDachHandRule.is_xi_bang(player_hand) and XiDachHandRule.is_xi_bang(dealer_hand):
            return ("DRAW", "BOTH_XI_BANG", 0)

        # 3. Ngũ linh
        if XiDachHandRule.is_ngu_linh(player_hand):
            if XiDachHandRule.is_ngu_linh(dealer_hand):
                if p_point < d_point:
                    return ("WIN", "BOTH_NGU_LINH_LOW_POINT", 1)
                if p_point > d_point:
                    return ("LOSE", "BOTH_NGU_LINH_HIGH_POINT", 1)
                return ("DRAW", "BOTH_NGU_LINH_EQUAL", 0)
            return ("WIN", "PLAYER_NGU_LINH", 1)

        if XiDachHandRule.is_ngu_linh(dealer_hand):
            return ("LOSE", "DEALER_NGU_LINH", 1)

        # 4. Bust
        if p_point > 21 and d_point > 21:
            return ("DRAW", "BOTH_BUST", 0)

        if p_point > 21:
            return ("LOSE", "PLAYER_BUST", 1)

        if d_point > 21:
            return ("WIN", "DEALER_BUST", 1)

        # 5. So điểm thường
        if p_point > d_point:
            return ("WIN", "HIGHER_POINT", 1)
        if p_point < d_point:
            return ("LOSE", "LOWER_POINT", 1)

        return ("DRAW", "EQUAL_POINT", 0)