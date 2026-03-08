from abc import ABC, abstractmethod

class GameRepository(ABC):
    @abstractmethod
    def save(self, game): ...
    
    @abstractmethod
    def get(self, game: str): ...

    @abstractmethod
    def remove(self, game: str): ...
