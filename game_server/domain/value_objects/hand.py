from domain.value_objects.card import Card
class Hand:
    def __init__(self):
        self._cards = []

    def reset(self):
        self._cards.clear()

    def add(self, card:Card):
        self._cards.append(card)

    def cards(self):
        return list(self._cards)  # tránh mutate ngoài

    def count(self) -> int:
        return len(self._cards)

    def __repr__(self):
        return f"Hand({self._cards})"
    
