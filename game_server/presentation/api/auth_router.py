# game_server/presentation/api/auth_router.py
"""
REST endpoints for auth and player management.

Routes
──────
POST /auth/register         → { player, token }
POST /auth/login            → { player, token }
GET  /players/me            → PlayerAccount (requires Bearer token)
GET  /players/{id}          → PlayerAccount (requires Bearer token)
PUT  /players/{id}          → PlayerAccount (requires Bearer token, own account only)
GET  /players/{id}/balance  → { player_id, balance }
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator

from application.services.auth_service import AuthService
from domain.repositories.player_account_repo import PlayerAccountRepository
from infrastructure.repositories.player_account_repo_mongo import MongoPlayerAccountRepository
from infrastructure.database.mongodb import mongo
from config.setting import settings

router = APIRouter()
_bearer = HTTPBearer()

# ── Dependency wiring ─────────────────────────────────────────────────────

def _get_account_repo() -> PlayerAccountRepository:
    return MongoPlayerAccountRepository(mongo)


def _get_auth_service(repo: PlayerAccountRepository = Depends(_get_account_repo)) -> AuthService:
    return AuthService(
        account_repo=repo,
        jwt_secret=settings.jwt_secret,
        jwt_algorithm=settings.jwt_algorithm,
        token_expire_minutes=settings.jwt_expire_minutes,
    )


async def _current_player_id(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
    auth: AuthService = Depends(_get_auth_service),
) -> str:
    """FastAPI dependency — extracts and validates Bearer token → player_id."""
    try:
        return auth.get_player_id_from_token(creds.credentials)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="TOKEN_INVALID",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── Request / Response schemas ────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    password: str = Field(..., min_length=6, max_length=128)

    @field_validator("username")
    @classmethod
    def no_spaces(cls, v: str) -> str:
        if " " in v:
            raise ValueError("Username must not contain spaces")
        return v.strip()


class LoginRequest(BaseModel):
    username: str
    password: str


class UpdateProfileRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)

    @field_validator("username")
    @classmethod
    def no_spaces(cls, v: str) -> str:
        if " " in v:
            raise ValueError("Username must not contain spaces")
        return v.strip()


class AuthResponse(BaseModel):
    token: str
    player: dict


class PlayerResponse(BaseModel):
    player: dict


# ── Auth endpoints ────────────────────────────────────────────────────────

@router.post("/auth/register", response_model=AuthResponse, status_code=201)
async def register(
    body: RegisterRequest,
    auth: AuthService = Depends(_get_auth_service),
):
    try:
        account = await auth.register(body.username, body.password)
        _, token = await auth.login(body.username, body.password)
    except ValueError as exc:
        _raise_400(str(exc))

    return {"token": token, "player": account.to_public()}


@router.post("/auth/login", response_model=AuthResponse)
async def login(
    body: LoginRequest,
    auth: AuthService = Depends(_get_auth_service),
):
    try:
        account, token = await auth.login(body.username, body.password)
    except ValueError as exc:
        # Use 401 for credential errors, 400 for anything else
        code = str(exc)
        if code == "INVALID_CREDENTIALS":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=code)
        _raise_400(code)

    return {"token": token, "player": account.to_public()}


# ── Player endpoints ──────────────────────────────────────────────────────

@router.get("/players/me", response_model=PlayerResponse)
async def get_me(
    player_id: str = Depends(_current_player_id),
    repo: PlayerAccountRepository = Depends(_get_account_repo),
):
    account = await repo.get_by_id(player_id)
    if not account:
        raise HTTPException(status_code=404, detail="PLAYER_NOT_FOUND")
    return {"player": account.to_public()}


@router.get("/players/{player_id}", response_model=PlayerResponse)
async def get_player(
    player_id: str,
    _: str = Depends(_current_player_id),        # just require auth, any player can view
    repo: PlayerAccountRepository = Depends(_get_account_repo),
):
    account = await repo.get_by_id(player_id)
    if not account:
        raise HTTPException(status_code=404, detail="PLAYER_NOT_FOUND")
    return {"player": account.to_public()}


@router.put("/players/{player_id}", response_model=PlayerResponse)
async def update_player(
    player_id: str,
    body: UpdateProfileRequest,
    current_id: str = Depends(_current_player_id),
    repo: PlayerAccountRepository = Depends(_get_account_repo),
):
    if current_id != player_id:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    try:
        account = await repo.update_profile(player_id, username=body.username)
    except ValueError as exc:
        _raise_400(str(exc))
    return {"player": account.to_public()}


@router.get("/players/{player_id}/balance")
async def get_balance(
    player_id: str,
    current_id: str = Depends(_current_player_id),
    repo: PlayerAccountRepository = Depends(_get_account_repo),
):
    if current_id != player_id:
        raise HTTPException(status_code=403, detail="FORBIDDEN")
    account = await repo.get_by_id(player_id)
    if not account:
        raise HTTPException(status_code=404, detail="PLAYER_NOT_FOUND")
    return {"player_id": player_id, "balance": account.balance}


# ── Helpers ───────────────────────────────────────────────────────────────

def _raise_400(detail: str):
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)