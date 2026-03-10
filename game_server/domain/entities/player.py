from domain.value_objects.hand import Hand


class Player:
    def __init__(self, player_id: str, name: str, ready: bool = False, is_dealer: bool = False):
        self.id = player_id
        self.name = name
        self.hand = Hand()
        self.standing = False
        self.busted = False
        self.ready = ready
        self.is_dealer = is_dealer

    def reset(self):
        self.hand.reset()
        self.standing = False
        self.busted = False

    def receive_card(self, card):
        self.hand.add(card)

    def stand(self):
        self.standing = True

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "hand": self.hand.to_dict(),
            "standing": self.standing,
            "busted": self.busted,
            "ready": self.ready,
            "is_dealer": self.is_dealer
        }

    @classmethod
    def from_dict(cls, data: dict):
        player = cls(
            player_id=data["id"],
            name=data["name"],
            ready=data.get("ready", False),
            is_dealer=data.get("is_dealer", False)
        )

        player.hand = Hand.from_dict(data.get("hand", {}))
        player.standing = data.get("standing", False)
        player.busted = data.get("busted", False)

        return player