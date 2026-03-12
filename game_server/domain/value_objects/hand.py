# game_server/domain/value_object/hand.py
from domain.value_objects.card import Card
class Hand:
    def __init__(self):
        self._cards = []

    def reset(self):
        self._cards.clear()

    def add(self, card: Card):
        self._cards.append(card)

    def cards(self):
        return list(self._cards)

    def count(self) -> int:
        return len(self._cards)

    def to_dict(self):
        return {
            "cards": [card.to_dict() for card in self._cards]
        }

    @classmethod
    def from_dict(cls, data: dict):
        hand = cls()

        cards = data.get("cards", [])

        for card_data in cards:
            hand.add(Card.from_dict(card_data))

        return hand

    # ── Dunder ────────────────────────────────────────────────────────────
    def __repr__(self):
        return f"Hand({self._cards})"

    def __len__(self) -> int:
        return self.count()