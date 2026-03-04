
from domain.repositories.room_repo import RoomRepository


class InMemoryRoomRepository(RoomRepository):
    def __init__(self):
        self.rooms = {}
        self.dealer_room_map = {}

    def save(self, room):
        self.rooms[room.id] = room
        self.dealer_room_map[room.dealer] = room.id

    def get(self, room_id):
        return self.rooms.get(room_id)

    def remove(self, room_id):
        room = self.rooms.pop(room_id, None)
        if room:
            self.dealer_room_map.pop(room.dealer, None)

    def get_by_dealer_sid(self, sid):
        room_id = self.dealer_room_map.get(sid)
        return self.rooms.get(room_id) if room_id else None