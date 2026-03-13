# application/room_service.py

import uuid
from domain.entities.room import Room
from domain.entities.dealer import Dealer
from domain.entities.player import Player
from infrastructure.repositories import *
import logging
room_repo = get_room_repository()
logger = logging.getLogger("Room")
class RoomService:

    def __init__(self):
        self.room_repo = room_repo

    @staticmethod
    async def room_list(sid: str):
        return await room_repo.list_rooms()

    @staticmethod
    async def create_room(dealer_sid: str, name: str):
        room_id = uuid.uuid4().hex[:6].upper()
        dealer = Dealer(player_id=dealer_sid, name=name)
        logger.info(f"Creating room with ID: {room_id} for dealer SID: {dealer_sid}")
        if await RoomService.get_room_by_dealer_sid(dealer_sid) is not None:
            logger.error(f"Dealer {dealer.name} already has a room, cannot create another")
            raise ValueError("DEALER_ALREADY_HAS_ROOM")
        if await RoomService.get_room_by_player_sid(dealer_sid) is not None:
            logger.error(f"Player {dealer.name} is already in a room, cannot create room")
            raise ValueError("PLAYER_ALREADY_IN_ROOM")
        room = Room(room_id=room_id, dealer=dealer)
        logger.info(f"Room created: {room.id}")
        await room_repo.save(room)
        return room

    @staticmethod
    async def join_room(room_id: str, sid: str, name: str):
        room = await room_repo.get(room_id)
        if not room:
            logger.error("ROOM_NOT_FOUND")
            raise ValueError("ROOM_NOT_FOUND")
        if await RoomService.get_room_by_player_sid(sid) is not None:
            logger.error("Player already in a room")
            raise ValueError("Player already in a room")
        if await RoomService.get_room_by_dealer_sid(sid) is not None:
            logger.error("Dealer cannot join another room as player")
            raise ValueError("Dealer cannot join another room as player")
        player = Player(player_id=sid, name=name)
        room.add_player(player)
        await room_repo.save(room)
        return room
    
    # @staticmethod
    # async def leave_room(room_id: str, sid: str):
    #     room = await room_repo.get(room_id)
    #     if not room:
    #         raise ValueError("ROOM_NOT_FOUND")
    #     if sid not in room.players.keys() and sid != room.dealer.id:
    #         raise ValueError("PLAYER_NOT_IN_ROOM")
    #     if room.phase !='waiting':
    #         raise ValueError("Can not leave while playing")
    #     if sid == room.dealer.id:
    #         await room_repo.remove(room_id)
    #         room.dealer = None
    #     if sid in room.players.keys():
    #         room.remove_player(sid)
    #         await room_repo.save(room)
    #     return room
    @staticmethod
    async def leave_room(room_id: str, sid: str):
        room = await room_repo.get(room_id)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")
        if room.phase != "waiting":
            raise ValueError("CANNOT_LEAVE_WHILE_PLAYING")

        if sid == room.dealer.id:
            # Dealer rời → xóa cả phòng
            await room_repo.remove(room_id)
            return None                         # phòng không còn tồn tại

        elif sid in room.players:
            room.remove_player(sid)
            await room_repo.save(room)
            return room

        else:
            raise ValueError("PLAYER_NOT_IN_ROOM")
        
    @staticmethod
    async def kick_player(room_id: str, dealer_sid: str, target_sid: str):
        room = await room_repo.get(room_id)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")
        if target_sid == room.dealer.id:
            raise ValueError("CANNOT_KICK_DEALER")
        if target_sid not in room.players.keys():
            raise ValueError("PLAYER_NOT_IN_ROOM")
        if dealer_sid != room.dealer.id:
            raise ValueError("ONLY_DEALER_CAN_KICK_PLAYERS")
        if room.phase !='waiting':
            raise ValueError("Can not kick while playing")
        room.remove_player(target_sid)
        await room_repo.save(room)
        return room    
    
    @staticmethod
    async def get_room_by_player_sid(player_sid: str):
        return await room_repo.get_by_player_sid(player_sid)
    @staticmethod
    async def get_room_by_dealer_sid(dealer_sid: str):
        return await room_repo.get_by_dealer_sid(dealer_sid)

    @staticmethod
    async def get_room(room_id: str):
        return await room_repo.get(room_id)
    
    @staticmethod
    async def ready(room_id: str, sid: str):
        room = await room_repo.get(room_id)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")
        if room.phase != "waiting":
            raise ValueError("GAME_RUNNING")
        if sid not in room.players.keys():
            raise ValueError("PLAYER_NOT_IN_ROOM")
        player = room.players[sid]
        if player.ready:
            raise ValueError("PLAYER_ALREADY_READY")
        
        player.ready = True
        await room_repo.save(room)
        return room

    @staticmethod
    async def unready(room_id: str, sid: str):
        room = await room_repo.get(room_id)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")
        if sid not in room.players.keys():
            raise ValueError("PLAYER_NOT_IN_ROOM")
        player = room.players[sid]
        if not player.ready:
            raise ValueError("PLAYER_ALREADY_UNREADY")
        if room.phase !="waiting":
            raise ValueError("GAME_RUNNING")
        player.ready = False
        await room_repo.save(room)
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