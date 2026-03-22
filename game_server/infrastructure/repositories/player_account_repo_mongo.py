# game_server/infrastructure/repositories/player_account_repo_mongo.py
from __future__ import annotations

import uuid
from datetime import datetime

from pymongo import ASCENDING
from pymongo.errors import DuplicateKeyError

from domain.entities.player_account import PlayerAccount
from domain.repositories.player_account_repo import PlayerAccountRepository


class MongoPlayerAccountRepository(PlayerAccountRepository):
    """
    Collection: players
    Indexes (created on first use via _ensure_indexes):
        unique(username)
    """

    def __init__(self, mongo):
        self.mongo = mongo
        self._indexes_created = False

    def _col(self):
        return self.mongo.get_db()["players"]

    async def _ensure_indexes(self):
        if self._indexes_created:
            return
        await self._col().create_index(
            [("username", ASCENDING)], unique=True, name="uq_username"
        )
        self._indexes_created = True

    # ── Write ─────────────────────────────────────────────────────────────

    async def create(self, account: PlayerAccount) -> PlayerAccount:
        await self._ensure_indexes()
        doc = account.to_dict()
        try:
            await self._col().insert_one(doc)
        except DuplicateKeyError:
            raise ValueError("USERNAME_TAKEN")
        return account

    async def update_balance(self, player_id: str, delta: int) -> int:
        """
        Uses $inc for atomicity. Rejects updates that would take balance below 0
        by using a conditional filter ($expr).
        """
        now = datetime.utcnow().isoformat()

        if delta >= 0:
            # Simple increment — can never go negative
            result = await self._col().find_one_and_update(
                {"_id": player_id},
                {"$inc": {"balance": delta}, "$set": {"updated_at": now}},
                return_document=True,
            )
        else:
            # Only apply if balance + delta >= 0
            result = await self._col().find_one_and_update(
                {"_id": player_id, "balance": {"$gte": abs(delta)}},
                {"$inc": {"balance": delta}, "$set": {"updated_at": now}},
                return_document=True,
            )

        if result is None:
            # Distinguish between "not found" and "insufficient balance"
            exists = await self._col().count_documents({"_id": player_id}, limit=1)
            if exists:
                raise ValueError("INSUFFICIENT_BALANCE")
            raise ValueError("PLAYER_NOT_FOUND")

        return result["balance"]

    async def update_profile(self, player_id: str, **fields) -> PlayerAccount:
        allowed = {"username"}
        update = {k: v for k, v in fields.items() if k in allowed}
        if not update:
            raise ValueError("NO_VALID_FIELDS")
        update["updated_at"] = datetime.utcnow().isoformat()

        try:
            result = await self._col().find_one_and_update(
                {"_id": player_id},
                {"$set": update},
                return_document=True,
            )
        except DuplicateKeyError:
            raise ValueError("USERNAME_TAKEN")

        if result is None:
            raise ValueError("PLAYER_NOT_FOUND")
        return PlayerAccount.from_doc(result)

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_by_id(self, player_id: str) -> PlayerAccount | None:
        doc = await self._col().find_one({"_id": player_id})
        return PlayerAccount.from_doc(doc) if doc else None

    async def get_by_username(self, username: str) -> PlayerAccount | None:
        doc = await self._col().find_one({"username": username})
        return PlayerAccount.from_doc(doc) if doc else None