# room_manager.py

import uuid
from models import Room, PlayerState

rooms = {}            # room_id -> Room
dealer_room_map = {}  # dealer_sid -> room_id


def create_room(sid: str, name: str) -> Room:
    if sid in dealer_room_map:
        raise ValueError("DEALER_ALREADY_HAS_ROOM")

    room_id = uuid.uuid4().hex[:6].upper()
    dealer = PlayerState(sid, name, is_dealer=True, ready=True)
    room = Room(room_id, dealer)

    rooms[room_id] = room
    dealer_room_map[sid] = room_id
    return room


def get_room(room_id: str):
    return rooms.get(room_id)


def remove_room(room_id: str):
    room = rooms.pop(room_id, None)
    if room:
        dealer_sid = room.dealer_sid
        dealer_room_map.pop(dealer_sid, None)