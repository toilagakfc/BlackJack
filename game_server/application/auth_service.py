# game_server/application/services/auth_service.py
"""
AuthService owns registration, login, and JWT lifecycle.

Password hashing uses bcrypt directly (no passlib).
passlib is unmaintained and breaks with bcrypt >= 4.0 because
bcrypt removed the __about__ module it relied on.

JWT payload shape:
    { "sub": "<player_id>", "username": "<username>", "exp": <unix ts> }
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from domain.entities.player_account import PlayerAccount
from domain.repositories.player_account_repo import PlayerAccountRepository


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


class AuthService:

    def __init__(
        self,
        account_repo: PlayerAccountRepository,
        jwt_secret: str,
        jwt_algorithm: str = "HS256",
        token_expire_minutes: int = 60 * 24,
    ):
        self._repo = account_repo
        self._secret = jwt_secret
        self._algorithm = jwt_algorithm
        self._expire_minutes = token_expire_minutes

    # ── Register ──────────────────────────────────────────────────────────

    async def register(self, username: str, password: str) -> PlayerAccount:
        username = username.strip()
        if not username:
            raise ValueError("USERNAME_EMPTY")
        if len(password) < 6:
            raise ValueError("PASSWORD_TOO_SHORT")

        account = PlayerAccount(
            id=uuid.uuid4().hex,
            username=username,
            password_hash=_hash_password(password),
        )
        return await self._repo.create(account)

    # ── Login ─────────────────────────────────────────────────────────────

    async def login(self, username: str, password: str) -> tuple[PlayerAccount, str]:
        account = await self._repo.get_by_username(username)

        # Deliberately vague — do not reveal whether the username exists
        if account is None or not _verify_password(password, account.password_hash):
            raise ValueError("INVALID_CREDENTIALS")

        return account, self._issue_token(account)

    # ── Token ─────────────────────────────────────────────────────────────

    def _issue_token(self, account: PlayerAccount) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=self._expire_minutes)
        payload = {"sub": account.id, "username": account.username, "exp": expire}
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def decode_token(self, token: str) -> dict:
        try:
            return jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except JWTError:
            raise ValueError("TOKEN_INVALID")

    def get_player_id_from_token(self, token: str) -> str:
        return self.decode_token(token)["sub"]