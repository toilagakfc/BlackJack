# game_server/domain/repositories/player_repo.py
from abc import ABC, abstractmethod
from domain.entities.player import Player


class PlayerRepository(ABC):

    @abstractmethod
    async def get(self, player_id: str) -> Player | None: ...

    @abstractmethod
    async def get_many(self, player_ids: list[str]) -> dict[str, Player]: ...

    @abstractmethod
    async def save(self, player: Player) -> None: ...

    @abstractmethod
    async def update_balance(self, player_id: str, delta: int) -> int: ...
