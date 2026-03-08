"""In-memory repository adapter (thin)"""
from domain.repositories.game_repo import GameRepository

class InMemoryGameRepository(GameRepository):
    def __init__(self):
        self.rooms = {}
        self.dealer_room_map = {}
        self.player_room_map = {}
    def save(self, game):
        pass

    def get(self, room_id):
        pass

    def remove(self, room_id):
        pass
  