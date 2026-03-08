from .hand_value import *
from domain.value_objects.constants import MAX_CARDS

def is_bust(hand:Hand) -> bool:
    return calc_point(hand) > 21


def is_blackjack(hand:Hand) -> bool:
    if hand.count() != 2:
        return False
    ranks = [c.rank for c in hand.cards()]
    return ("A" in ranks) and any(r in ("10", "J", "Q", "K") for r in ranks)


def is_xi_bang(hand:Hand) -> bool:
    return hand.count() == 2 and all(c.rank == "A" for c in hand.cards())


def is_ngu_linh(hand:Hand) -> bool:
    return hand.count() == 5 and calc_point(hand) < 21


def can_draw(hand:Hand) -> bool:
    return hand.count() < MAX_CARDS


def can_stand(hand:Hand) -> bool:
    return calc_point(hand) >= 16


def dealer_should_draw(hand:Hand) -> bool:
    return calc_point(hand) < 15