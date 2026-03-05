# application/room_service.py

import uuid
from domain.entities.room import Room
from domain.entities.dealer import Dealer
from domain.entities.player import Player
from infrastructure.repositories.room_repo_memory import InMemoryRoomRepository

room_repo = InMemoryRoomRepository()


class RoomService:

    def __init__(self):
        self.room_repo = room_repo

    @staticmethod
    def create_room(dealer_sid: str, name: str):
        room_id = uuid.uuid4().hex[:6].upper()
        dealer = Dealer(sid=dealer_sid, name=name)
        print(f"Creating room with ID: {room_id} for dealer SID: {dealer_sid}")
        if RoomService.get_room_by_dealer_sid(dealer_sid) is not None:
            print(f"Dealer {dealer.name} already has a room, cannot create another")
            return None
        room = Room(room_id=room_id, dealer=dealer)
        print(f"Room created: {room.id}")
        room_repo.save(room)
        return room

    @staticmethod
    def join_room(room_id: str, sid: str, name: str):
        room = room_repo.get(room_id)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")
        player = Player(player_id=sid, name=name)
        room.add_player(player)
        room_repo.save(room)
        return room
    
    @staticmethod
    def leave_room(room_id: str, sid: str):
        room = room_repo.get(room_id)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")
        if sid not in room.players.keys() and sid != room.dealer.id:
            raise ValueError("PLAYER_NOT_IN_ROOM")
        if sid == room.dealer.id:
           room_repo.remove(room_id)
           print(f"Rooms: {room_repo.rooms}")
           print(f"room_repo.dealer_room_map: {room_repo.dealer_room_map}")
           return None
        if sid in room.players.keys():
            room.remove_player(sid)
            room_repo.save(room)
        return room
    @staticmethod
    def kick_player(room_id: str, dealer_sid: str, target_sid: str):
        room = room_repo.get(room_id)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")
        if target_sid not in room.players.keys():
            raise ValueError("PLAYER_NOT_IN_ROOM")
        if target_sid == room.dealer.id:
            raise ValueError("CANNOT_KICK_DEALER")
        if dealer_sid != room.dealer.id:
            raise ValueError("ONLY_DEALER_CAN_KICK_PLAYERS")
        room.remove_player(target_sid)
        room_repo.save(room)
        print(f"Rooms: {room_repo.rooms}")
        print(f"room_repo.dealer_room_map: {room_repo.dealer_room_map}")
        return room    
    @staticmethod
    def get_room_by_dealer_sid(dealer_sid: str):
        return room_repo.get_by_dealer_sid(dealer_sid)

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
    
