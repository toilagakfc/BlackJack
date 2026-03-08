#game_server/infrastructure/repositories/room_repo_memory.py
from domain.repositories.room_repo import RoomRepository

class InMemoryRoomRepository(RoomRepository):
    def __init__(self):
        self.rooms = {}
        self.dealer_room_map = {}
        self.player_room_map = {}

    def save(self, room):
        self.rooms[room.id] = room
        self.dealer_room_map[room.dealer.id] = room.id
        for player_id in room.players.keys():
            self.player_room_map[player_id] = room.id

    def get(self, room_id):
        return self.rooms.get(room_id)

    def remove(self, room_id):
        room = self.rooms.pop(room_id, None)
        if not room:
            return
        
        self.dealer_room_map.pop(room.dealer.id, None)
        self.player_room_map = {pid: rid for pid, rid in self.player_room_map.items() if rid != room_id}

            
    def get_by_dealer_sid(self, sid):
        room_id = self.dealer_room_map.get(sid)
        return self.rooms.get(room_id) if room_id else None

    def get_by_player_sid(self, sid):
        room_id = self.player_room_map.get(sid)
        return self.rooms.get(room_id) if room_id else None

    def list_rooms(self):
        return list(self.rooms.keys())
