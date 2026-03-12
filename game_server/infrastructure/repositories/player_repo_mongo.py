# game_server/infrastructure/repositories/player_repo_mongo.py
from datetime import datetime
from domain.entities.player import Player


class MongoPlayerRepository:

    def __init__(self, mongo):
        self.mongo = mongo

    def _collection(self):
        return self.mongo.get_db()["players"]

    # ── Read ──────────────────────────────────────────────────────────────

    async def get(self, player_id: str) -> Player | None:
        doc = await self._collection().find_one({"_id": player_id})
        if not doc:
            return None
        return self._to_player(doc)

    async def get_many(self, player_ids: list[str]) -> dict[str, Player]:
        """Lấy nhiều player 1 lần — tránh N+1 queries."""
        cursor = self._collection().find({"_id": {"$in": player_ids}})
        docs = await cursor.to_list(length=len(player_ids))
        return {doc["_id"]: self._to_player(doc) for doc in docs}

    async def exists(self, player_id: str) -> bool:
        count = await self._collection().count_documents(
            {"_id": player_id}, limit=1
        )
        return count > 0

    # ── Write ─────────────────────────────────────────────────────────────

    async def save(self, player: Player) -> None:
        """Upsert toàn bộ player — dùng khi tạo mới hoặc update nhiều field."""
        await self._collection().update_one(
            {"_id": player.id},
            {
                "$set": {
                    "name": player.name,
                    "balance": player.balance,
                    "updated_at": datetime.now().isoformat(),
                },
                "$setOnInsert": {
                    "_id": player.id,
                    "created_at": datetime.now().isoformat(),
                },
            },
            upsert=True,
        )

    async def update_balance(self, player_id: str, delta: int) -> int:
        """
        Cộng/trừ balance sau mỗi ván.
        Dùng $inc thay vì read-modify-write để tránh race condition.
        Trả về balance mới sau update.
        """
        result = await self._collection().find_one_and_update(
            {"_id": player_id},
            {
                "$inc": {"balance": delta},
                "$set": {"updated_at": datetime.now().isoformat()},
            },
            return_document=True,   # trả về doc sau khi update
        )
        if not result:
            raise ValueError(f"PLAYER_NOT_FOUND: {player_id}")

        return result["balance"]

    # ── Deserialize ───────────────────────────────────────────────────────

    @staticmethod
    def _to_player(doc: dict) -> Player:
        return Player(
            player_id=doc["_id"],
            name=doc["name"],
            balance=doc.get("balance", 0),
            ready=doc.get("ready", False),
            is_dealer=doc.get("is_dealer", False),
        )