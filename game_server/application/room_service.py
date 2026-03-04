# application/room_service.py

import uuid
from domain.entities.room import Room
from infrastructure.repositories.room_repo_memory import InMemoryRoomRepository

room_repo = InMemoryRoomRepository()


class RoomService:

    @staticmethod
    def create_room(dealer_sid: str):
        room_id = uuid.uuid4().hex[:6].upper()
        room = Room(room_id=room_id, dealer_id=dealer_sid)

        room_repo.save(room)
        return room

    @staticmethod
    def join_room(room_id: str, sid: str, name: str):
        room = room_repo.get(room_id)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")

        room.add_player(sid, name)
        room_repo.save(room)

        return room
    
    @staticmethod
    def leave_room(room_id: str, sid: str):
        room = room_repo.get(room_id)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")

        room.remove_player(sid)
        if not room.has_players():
            room_repo.remove(room_id)
        else:
            room_repo.save(room)

        return room
    
    @staticmethod
    def get_room_by_dealer_sid(sid: str):
        return room_repo.get_by_dealer_sid(sid)
    
    @staticmethod
    def get_room(room_id: str):
        return room_repo.get(room_id)
    
    @staticmethod
    def start_game(room_id: str, game):
        room = room_repo.get(room_id)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")

        room.start_game(game)
        room_repo.save(room)

        return room
    
    @staticmethod
    def end_game(room_id: str):
        room = room_repo.get(room_id)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")

        room.end_game()
        room_repo.save(room)

        return room
    
    @staticmethod
    def reset_game(room_id: str):
        room = room_repo.get(room_id)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")

        room.reset_game()
        room_repo.save(room)

        return room