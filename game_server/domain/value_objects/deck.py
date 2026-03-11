# game_server/domain/value_objects/deck.py
import random
from domain.value_objects.card import Card
from domain.value_objects.constants import SUITS, RANKS

# Lookup index → Card (build 1 lần lúc import)
_ALL_CARDS: list[Card] = [
    Card(rank, suit)
    for suit in SUITS
    for rank in RANKS
]  # index 0-51 cố định

_CARD_TO_INDEX: dict[tuple, int] = {
    (card.rank, card.suit): i
    for i, card in enumerate(_ALL_CARDS)
}


class Deck:
    """
    Bộ bài dùng set of indices (0-51) để track lá còn lại.

    DB workflow:
        # Lưu
        drawn = deck.drawn_indices   # list[int] → lưu JSON/array vào DB

        # Restore
        deck = Deck.from_drawn(drawn)
    """

    def __init__(self):
        self._remaining: set[int] = set(range(52))

    # ── DB integration ────────────────────────────────────────────────────

    @classmethod
    def from_drawn(cls, drawn_indices: list[int]) -> "Deck":
        """Khôi phục Deck từ danh sách index lá đã rút (lấy từ DB)."""
        deck = cls()
        deck._remaining -= set(drawn_indices)
        return deck

    @property
    def drawn_indices(self) -> list[int]:
        """Danh sách index lá đã rút — lưu vào DB."""
        return list(set(range(52)) - self._remaining)

    # ── Gameplay ──────────────────────────────────────────────────────────

    def draw(self) -> Card:
        """Rút 1 lá ngẫu nhiên."""
        if not self._remaining:
            raise RuntimeError("Deck is empty")
        idx = random.choice(tuple(self._remaining))
        self._remaining.discard(idx)
        return _ALL_CARDS[idx]

    def remaining(self) -> int:
        return len(self._remaining)

    def reset(self):
        """Trả toàn bộ lá về bộ bài."""
        self._remaining = set(range(52))

    # ── Helpers ───────────────────────────────────────────────────────────

    def __len__(self) -> int:
        return self.remaining()

    def __repr__(self) -> str:
        return f"Deck(remaining={self.remaining()}/52)"