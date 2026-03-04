"""In-memory repository adapter (thin)"""
from ...server import room_manager


def list_rooms():
    return [
        {
            "room_id": rid,
            "dealer": r.players[r.dealer_sid].name,
            "player_count": r.player_count(),
        }
        for rid, r in room_manager.rooms.items()
    ]
