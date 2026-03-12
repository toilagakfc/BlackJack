def serialize_hand(hand, hide=False):
    if hide:
        return [{"hidden": True} for _ in hand.cards()]
    return [{"rank": c.rank, "suit": c.suit} for c in hand.cards()]