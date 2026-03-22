# game_server/domain/repositories/player_account_repo.py
from abc import ABC, abstractmethod
from domain.entities.player_account import PlayerAccount


class PlayerAccountRepository(ABC):

    @abstractmethod
    async def create(self, account: PlayerAccount) -> PlayerAccount:
        """Insert a new account. Raises ValueError('USERNAME_TAKEN') on duplicate."""
        ...

    @abstractmethod
    async def get_by_id(self, player_id: str) -> PlayerAccount | None: ...

    @abstractmethod
    async def get_by_username(self, username: str) -> PlayerAccount | None: ...

    @abstractmethod
    async def update_balance(self, player_id: str, delta: int) -> int:
        """
        Atomically apply delta to balance.
        Returns the new balance.
        Raises ValueError('PLAYER_NOT_FOUND') if id is unknown.
        Raises ValueError('INSUFFICIENT_BALANCE') if balance would go negative.
        """
        ...

    @abstractmethod
    async def update_profile(self, player_id: str, **fields) -> PlayerAccount:
        """Update allowed mutable fields (currently: username). Returns updated account."""
        ...