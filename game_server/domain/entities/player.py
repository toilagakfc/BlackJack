# game_server/domain/entities/player.py
from domain.value_objects.hand import Hand


class Player:
    def __init__(
        self,
        player_id: str,
        name: str,
        ready: bool = False,
        is_dealer: bool = False,
        balance: int = 0,
    ):
        self.id = player_id
        self.name = name
        self.hand = Hand()
        self.standing = False
        self.busted = False
        self.ready = ready
        self.is_dealer = is_dealer
        self.bet = 0
        self.balance = balance
        self.folded = False   # True if player did not bet in time

    def reset(self):
        self.hand.reset()
        self.standing = False
        self.busted = False
        self.ready = False
        self.bet = 0
        self.folded = False

    def receive_card(self, card):
        self.hand.add(card)

    def stand(self):
        self.standing = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "ready": self.ready,
            "is_dealer": self.is_dealer,
            "balance": self.balance,
            "standing": self.standing,
            "busted": self.busted,
            "hand": self.hand.to_dict(),
            "bet": self.bet,
            "folded": self.folded,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        player = cls(
            player_id=data["id"],
            name=data["name"],
            ready=data.get("ready", False),
            is_dealer=data.get("is_dealer", False),
            balance=data.get("balance", 0),
        )

        player.standing = data.get("standing", False)
        player.busted = data.get("busted", False)
        player.bet = data.get("bet", 0)
        player.folded = data.get("folded", False)
        return player