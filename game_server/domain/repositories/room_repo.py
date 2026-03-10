#gameserver/domain/repositories/room_repo.py
from abc import ABC, abstractmethod

class RoomRepository(ABC):
    @abstractmethod
    async def save(self, room): ...
    
    @abstractmethod
    async def get(self, room_id: str): ...

    @abstractmethod
    async def remove(self, room_id: str): ...

    @abstractmethod
    async def get_by_dealer_sid(self, sid: str): ...
    
    @abstractmethod
    async def get_by_player_sid(self, sid: str): ...
    
    @abstractmethod
    async def list_rooms(self): ...   