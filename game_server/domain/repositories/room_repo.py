from abc import ABC, abstractmethod

class RoomRepository(ABC):
    @abstractmethod
    def save(self, room): ...
    
    @abstractmethod
    def get(self, room_id: str): ...

    @abstractmethod
    def remove(self, room_id: str): ...

    @abstractmethod
    def get_by_dealer_sid(self, sid: str): ...