# deck.py

import random

SUITS = ["Cơ", "Rô", "Chuồn", "Bích"]
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]


class Card:
    def __init__(self, rank: str, suit: str):
        self.rank = rank
        self.suit = suit

    def __repr__(self):
        return f"{self.rank}-{self.suit}"

    def base_value(self) -> int:
        """
        Giá trị cơ bản:
        - J Q K = 10
        - A = 11 (xử lý lại ở Hand)
        - 2–10 = số tương ứng
        """
        if self.rank in ("J", "Q", "K"):
            return 10
        if self.rank == "A":
            return 11
        return int(self.rank)
    
    def to_dict(self):
        return {"rank": self.rank, "suit": self.suit}


class Deck:
    def __init__(self, shuffle: bool = True):
        self.cards = [Card(rank, suit) for suit in SUITS for rank in RANKS]
        if shuffle:
            self.shuffle()

    def shuffle(self):
        random.shuffle(self.cards)

    def draw(self) -> Card:
        if not self.cards:
            raise RuntimeError("Deck rỗng")
        return self.cards.pop()

    def remaining(self) -> int:
        return len(self.cards)