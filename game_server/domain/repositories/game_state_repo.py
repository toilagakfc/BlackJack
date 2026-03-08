#gameserver/domain/repositories/game_repo.py
from abc import ABC, abstractmethod
from domain.state.game_state import GameState
class GameStateRepository(ABC):
    @abstractmethod
    async def save(self, game_state: GameState): ...
    
    @abstractmethod
    async def get(self, room_id: str)-> GameState | None: ...

    @abstractmethod
    async def delete(self, room_id: str): ...
