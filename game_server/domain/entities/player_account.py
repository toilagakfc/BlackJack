# game_server/domain/entities/player_account.py
"""
PlayerAccount is the *persistent identity* of a user.

It is intentionally separate from the in-game Player entity:

    PlayerAccount  — lives in MongoDB, survives sessions
                     carries username, password_hash, balance
    Player         — lives in a Game, reset each round
                     carries hand, bet, folded, standing

They share the same _id so GameService can look up balance
with a single query:  player_repo.get(account.id)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class PlayerAccount:
    id: str                  # MongoDB _id (str ObjectId hex or uuid)
    username: str
    password_hash: str
    balance: int = 1000      # starting balance for new accounts
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # ── Serialization ─────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "_id": self.id,
            "username": self.username,
            "password_hash": self.password_hash,
            "balance": self.balance,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_doc(cls, doc: dict) -> "PlayerAccount":
        return cls(
            id=str(doc["_id"]),
            username=doc["username"],
            password_hash=doc["password_hash"],
            balance=doc.get("balance", 1000),
            created_at=_parse_dt(doc.get("created_at")),
            updated_at=_parse_dt(doc.get("updated_at")),
        )

    # ── Public projection (never include password_hash) ───────────────────

    def to_public(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "balance": self.balance,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


def _parse_dt(value) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    return datetime.utcnow()