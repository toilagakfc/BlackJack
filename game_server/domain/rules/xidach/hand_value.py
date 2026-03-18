from domain.value_objects.card import Card
from domain.value_objects.hand import Hand

def card_value(card:Card) -> int:
    if card.rank in ("J", "Q", "K"):
        return 10
    if card.rank == "A":
        return 11
    return int(card.rank)

# def calc_point(hand: Hand) -> int:
#         total = 0
#         aces = 0
#         card_num = hand.count()

#         for c in hand.cards():
#             if c.rank == "A":
#                 aces += 1
#             else:
#                 total += card_value(c)

#         if aces == 0:
#             return total

#         if card_num == 2:
#             return total + 11

#         if card_num == 3:
#             # 1 Át có thể =10
#             if total + 10 <= 28:
#                 total += 10
#                 aces -= 1
#             else:
#                 total += 1
#                 aces -= 1

#             total += aces
#             return total

#         total += aces
#         return total

#new calculate point
def calc_point(hand: Hand) -> int:
    total = 0
    aces = 0

    for c in hand.cards():
        if c.rank == "A":
            aces += 1
            total += 11
        else:
            total += card_value(c)

    while total > 21 and aces > 0:
        total -= 10
        aces -= 1

    return total