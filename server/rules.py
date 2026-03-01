# rules.py

class XiDachRules:
    """
    Quy ước:
    - Hợp lệ so điểm thường: 16–21
    - Quắc: >21
    - Ngũ linh: 5 lá, <21
    - Xì dách: A + 10/J/Q/K (2 lá)
    - Xì bàng: A + A (2 lá)
    """

    @staticmethod
    def compare(player, dealer):
        p = player.hand
        d = dealer.hand

        p_point = p.calculate_point()
        d_point = d.calculate_point()

        # 1. Dealer xì dách → tất cả player thua
        if d.has_blackjack() and not p.has_blackjack():
            
            return {
                "result": "LOSE",
                "reason": "DEALER_BLACKJACK",
                "multiplier": 0
            }
        
        if p.has_blackjack() and not d.has_blackjack():
            return {
                "result": "WIN",
                "reason": "PLAYER_BLACKJACK",
                "multiplier": 1
            }

        if p.has_blackjack() and d.has_blackjack():
            return {
                "result": "DRAW",
                "reason": "BOTH_BLACKJACK",
                "multiplier": 0
            }
        
        # 2. Xì bàng
        if p.is_xi_bang() and not d.is_xi_bang():
            return {
                "result": "WIN",
                "reason": "PLAYER_XI_BANG",
                "multiplier": 2
            }

        if d.is_xi_bang() and not p.is_xi_bang():
            return {
                "result": "LOSE",
                "reason": "DEALER_XI_BANG",
                "multiplier": 2
            }

        if p.is_xi_bang() and d.is_xi_bang():
            return {
                "result": "DRAW",
                "reason": "BOTH_XI_BANG",
                "multiplier": 0
            }

        # 3. Ngũ linh
        if p.is_ngu_linh():
            if d.is_ngu_linh():
                if p_point < d_point:
                    return {
                        "result": "WIN",
                        "reason": "BOTH_NGU_LINH_LOW_POINT",
                        "multiplier": 1
                    }
                elif p_point > d_point:
                    return {
                        "result": "LOSE",
                        "reason": "BOTH_NGU_LINH_HIGH_POINT",
                        "multiplier": 1
                    }
                else:
                    return {
                        "result": "DRAW",
                        "reason": "BOTH_NGU_LINH_EQUAL",
                        "multiplier": 0
                    }
            else:
                return {
                    "result": "WIN",
                    "reason": "PLAYER_NGU_LINH",
                    "multiplier": 1
                }

        if d.is_ngu_linh():
            return {
                "result": "LOSE",
                "reason": "DEALER_NGU_LINH",
                "multiplier": 1
            }

        # 4. Cả hai quắc
        if p_point > 21 and d_point > 21:
            return {
                "result": "DRAW",
                "reason": "BOTH_BUST",
                "multiplier": 0
            }

        # 5. Một bên quắc
        if p_point > 21:
            return {
                "result": "LOSE",
                "reason": "PLAYER_BUST",
                "multiplier": 1
            }

        if d_point > 21:
            return {
                "result": "WIN",
                "reason": "DEALER_BUST",
                "multiplier": 1
            }

        # 6. So điểm chuẩn (16–21)
        if 16 <= p_point <= 21 and 16 <= d_point <= 21:
            if p_point > d_point:
                return {
                    "result": "WIN",
                    "reason": "HIGHER_POINT",
                    "multiplier": 1
                }
            elif p_point < d_point:
                return {
                    "result": "LOSE",
                    "reason": "LOWER_POINT",
                    "multiplier": 1
                }
            else:
                return {
                    "result": "DRAW",
                    "reason": "EQUAL_POINT",
                    "multiplier": 0
                }

        # fallback (không nên xảy ra)
        return {
            "result": "UNKNOWN",
            "reason": "UNDEFINED_STATE",
            "multiplier": 0
        }