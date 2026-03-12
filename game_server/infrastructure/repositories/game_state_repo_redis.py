"""In-memory repository adapter (thin)"""
from domain.repositories.game_state_repo import GameStateRepository
import json
from domain.state.game_state import GameState

class RedisGameStateRepository(GameStateRepository):
    async def save(self, game_state: GameState):
        key = f"game:{game_state.room_id}"
        print(game_state.to_dict())
        # self.redis.set(
        #     key,
        #     json.dumps(game_state.to_dict()),
        #     ex=7200
        # )

    async def get(self, room_id):
        key = f"game:{room_id}"
        data = self.redis.get(key)

        if not data:
            return None

        return GameState.from_dict(json.loads(data))

    async def delete(self, room_id):
        self.redis.delete(f"game:{room_id}")
    
    