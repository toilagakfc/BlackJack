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
    def room_list(sid: str):
        return room_repo.list_rooms()

    @staticmethod
    def create_room(dealer_sid: str, name: str):
        room_id = uuid.uuid4().hex[:6].upper()
        dealer = Dealer(sid=dealer_sid, name=name)
        print(f"Creating room with ID: {room_id} for dealer SID: {dealer_sid}")
        if RoomService.get_room_by_dealer_sid(dealer_sid) is not None:
            print(f"Dealer {dealer.name} already has a room, cannot create another")
            raise ValueError("DEALER_ALREADY_HAS_ROOM")
        if RoomService.get_room_by_player_sid(dealer_sid) is not None:
            print(f"Player {dealer.name} is already in a room, cannot create room")
            raise ValueError("PLAYER_ALREADY_IN_ROOM")
        room = Room(room_id=room_id, dealer=dealer)
        print(f"Room created: {room.id}")
        room_repo.save(room)
        return room

    @staticmethod
    def join_room(room_id: str, sid: str, name: str):
        room = room_repo.get(room_id)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")
        if RoomService.get_room_by_player_sid(sid) is not None:
            raise ValueError("Player already in a room")
        if RoomService.get_room_by_dealer_sid(sid) is not None:
            raise ValueError("Dealer cannot join another room as player")
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
            room.dealer = None
        if sid in room.players.keys():
            room.remove_player(sid)
            room_repo.remove_player_from_room(room_id, sid)
            room_repo.save(room)
        print(f"room repo player map after player leaves: {room_repo.player_room_map}")
        print(f"room after player leaves: {room.players}")
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
        
        return room    
    
    @staticmethod
    def get_room_by_player_sid(player_sid: str):
        return room_repo.get_by_player_sid(player_sid)
    @staticmethod
    def get_room_by_dealer_sid(dealer_sid: str):
        return room_repo.get_by_dealer_sid(dealer_sid)

    @staticmethod
    def get_room(room_id: str):
        return room_repo.get(room_id)
    
    @staticmethod
    def start_game(room_id: str, sid: str):
        room = room_repo.get(room_id)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")
        if sid != room.dealer.id:
            raise ValueError("ONLY_DEALER_CAN_START_GAME")
        if not room.has_players():
            raise ValueError("NOT_ENOUGH_PLAYERS")
        if not room.all_ready() :
            raise ValueError("NOT_ALL_PLAYERS_READY")
        room.start_game()
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
    
    @staticmethod
    def ready(room_id: str, sid: str):
        room = room_repo.get(room_id)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")
        if sid not in room.players.keys():
            raise ValueError("PLAYER_NOT_IN_ROOM")
        player = room.players[sid]
        if player.ready:
            raise ValueError("PLAYER_ALREADY_READY")
        player.ready = True
        room_repo.save(room)
        return room

    @staticmethod
    def unready(room_id: str, sid: str):
        room = room_repo.get(room_id)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")
        if sid not in room.players.keys():
            raise ValueError("PLAYER_NOT_IN_ROOM")
        player = room.players[sid]
        if not player.ready:
            raise ValueError("PLAYER_ALREADY_UNREADY")
        player.ready = False
        room_repo.save(room)
        return room
        
    @staticmethod
    def player_disconnect(sid: str):
        room = RoomService.get_room_by_dealer_sid(sid)
        if room:
            RoomService.leave_room(room.id, sid)
            return
        #check if player in any room
        for room_id in room_repo.list_rooms():
            room = room_repo.get(room_id)
            if sid in room.players.keys():
                RoomService.leave_room(room.id, sid)
                room_repo.save(room)
                return room