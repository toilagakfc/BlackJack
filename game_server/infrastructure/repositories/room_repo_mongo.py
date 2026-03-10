from domain.repositories.room_repo import RoomRepository
from domain.entities.room import Room
class MongoRoomRepository(RoomRepository):

    def __init__(self,mongo):
        
        self.mongo = mongo

    async def _collection(self):
        return self.mongo.get_db()["rooms"]
    
    async def save(self, room):
        collection =  await self._collection()

        await collection.update_one(
            {"room_id": room.id,
             "dealer_sid":room.dealer.id},
            {"$set": room.to_dict()},
            upsert=True
        )

    async def get(self, room_id):
        collection = await self._collection()
        doc = await collection.find_one({"room_id": room_id})
        if not doc:
            return
        return Room.from_dict(doc)

    async def remove(self, room_id):
        collection = await self._collection()
        await collection.delete_one({"room_id": room_id})

    async def get_by_dealer_sid(self, sid):
        collection = await self._collection()
        return await collection.find_one({"dealer_sid": sid})

    async def get_by_player_sid(self, sid):
        collection = await self._collection()
        return await collection.find_one({"players.id": sid})
    
    async def list_rooms(self):

        collection = await self._collection()
        cursor = collection.find({},{ "_id": 0})

        rooms = []

        async for room in cursor:
            rooms.append({
                "room_id": room["room_id"],
                "phase": room["phase"],
                "player_count": len(room.get("players", [])) +1
            })

        return rooms