from infrastructure.database.mongodb import db


class GameRepository:

    async def save_game(self, game_id, data):
        await db.games.update_one(
            {"_id": game_id},
            {"$set": data},
            upsert=True
        )

    async def load_game(self, game_id):
        return await db.games.find_one({"_id": game_id})