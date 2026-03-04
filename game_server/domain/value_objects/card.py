class Card:
    def __init__(self, rank: str, suit: str):
        self.rank = rank
        self.suit = suit

    def __repr__(self):
        return f"{self.rank}-{self.suit}"

    def is_ace(self) -> bool:
        return self.rank == "A"

    def is_face(self) -> bool:
        return self.rank in ("J", "Q", "K")