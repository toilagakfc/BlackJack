
class GameState:

    def __init__(
        self,
        room_id: str,
        phase: str,
        turn_index: int,
        deck: list,
        dealer_cards: list,
        players_cards: dict
    ):
        self.room_id = room_id
        self.phase = phase
        self.turn_index = turn_index
        self.deck = deck
        self.dealer_cards = dealer_cards
        self.players_cards = players_cards
    def to_dict(self):
        return {
            "room_id": self.room_id,
            "phase": self.phase,
            "turn_index": self.turn_index,
            "deck": self.deck,
            "dealer_cards": self.dealer_cards,
            "players_cards": self.players_cards
        }
        
    @staticmethod
    def from_dict(data: dict):

        return GameState(
            room_id=data["room_id"],
            phase=data["phase"],
            turn_index=data["turn_index"],
            deck=data["deck"],
            dealer_cards=data["dealer_cards"],
            players_cards=data["players_cards"]
        )