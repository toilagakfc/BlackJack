import random
from domain.value_objects.card import Card
from domain.value_objects.constants import SUITS, RANKS


class Deck:
    def __init__(self, shuffle: bool = True):
        self._cards = [Card(rank, suit) for suit in SUITS for rank in RANKS]
        if shuffle:
            self.shuffle()

    def shuffle(self):
        random.shuffle(self._cards)

    def draw(self) -> Card:
        if not self._cards:
            raise RuntimeError("Deck is empty")
        return self._cards.pop()

    def remaining(self) -> int:
        return len(self._cards)