# game_server/domain/value_objects/card.py

class Card:
    def __init__(self, rank: str, suit: str):
        self.rank = rank
        self.suit = suit

    # ── Blackjack helpers ─────────────────────────────────────────────────

    def is_ace(self) -> bool:
        return self.rank == "A"

    def is_face(self) -> bool:
        return self.rank in ("J", "Q", "K")

    @property
    def base_value(self) -> int:
        """Giá trị mặc định (Ace = 11, face = 10)."""
        if self.is_face():
            return 10
        if self.is_ace():
            return 11
        return int(self.rank)

    # ── Equality & hashability ────────────────────────────────────────────

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return NotImplemented
        return self.rank == other.rank and self.suit == other.suit

    def __hash__(self) -> int:
        return hash((self.rank, self.suit))

    # ── Serialization ─────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {"rank": self.rank, "suit": self.suit}

    @classmethod
    def from_dict(cls, data: dict) -> "Card":
        return cls(rank=data["rank"], suit=data["suit"])

    # ── Dunder ────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return f"{self.rank}-{self.suit}"