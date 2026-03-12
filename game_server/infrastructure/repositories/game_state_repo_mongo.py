# game_server/infrastructure/repositories/game_state_repo_mongo.py
from domain.repositories.game_state_repo import GameStateRepository as BaseGameStateRepository
from domain.entities.game import Game
from domain.state.game_state import GameState
from domain.entities.player import Player
from domain.entities.dealer import Dealer
from domain.value_objects.hand import Hand
from domain.value_objects.deck import Deck


class MongoGameStateRepository(BaseGameStateRepository):
    """
    Lưu Game entity vào MongoDB.
    - _id bỏ trước khi from_dict
    - Deck restore từ drawn_indices
    - Hand restore từ cards
    """

    def __init__(self, mongo):
        self.mongo = mongo

    def _collection(self):
        """Sync — get_db() trả về db object, không cần await."""
        return self.mongo.get_db()["games"]

    # ── Write ─────────────────────────────────────────────────────────────

    async def save(self, game: Game, room_id: str) -> None:
        collection = self._collection()
        data = game.to_dict()
        data["room_id"] = room_id           # đảm bảo room_id luôn có

        await collection.update_one(
            {"room_id": room_id},
            {"$set": data},
            upsert=True,
        )

    async def delete(self, room_id: str) -> None:
        collection = self._collection()
        await collection.delete_one({"room_id": room_id})

    # ── Read ──────────────────────────────────────────────────────────────

    async def get(self, room_id: str) -> Game | None:
        collection = self._collection()
        doc = await collection.find_one({"room_id": room_id})
        if not doc:
            return None
        return self._to_game(doc)

    # ── Deserialize ───────────────────────────────────────────────────────

    @staticmethod
    def _to_game(doc: dict) -> Game:
        """Rebuild Game entity từ MongoDB document."""
        doc.pop("_id", None)        # MongoDB ObjectId không serialize được
        doc.pop("room_id", None)

        # Dealer
        dealer = Dealer.from_dict(doc["dealer"])
        dealer.hand = Hand.from_dict(doc["dealer"].get("hand", {"cards": []}))

        # Players
        players = []
        for pid, pdata in doc.get("players", {}).items():
            p = Player.from_dict(pdata)
            p.hand = Hand.from_dict(pdata.get("hand", {"cards": []}))
            p.standing = pdata.get("standing", False)
            p.busted = pdata.get("busted", False)
            players.append(p)

        # Game
        game = Game(dealer=dealer, players=players)
        game.deck = Deck.from_drawn(doc.get("deck_drawn", []))
        game.turn_index = doc.get("turn_index", 0)
        game.phase = doc.get("phase", "PLAYER_TURN")
        game.compared_players = {
            p for p in players
            if p.id in doc.get("compared_players", {})
        }

        # Timestamps
        from datetime import datetime
        def parse_dt(v):
            return datetime.fromisoformat(v) if v else None

        game.started_at = parse_dt(doc.get("started_at"))
        game.updated_at = parse_dt(doc.get("updated_at"))
        game.ended_at   = parse_dt(doc.get("ended_at"))

        return game