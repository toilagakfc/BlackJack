from infrastructure.repositories.game_state_repo_redis import RedisGameStateRepository
from infrastructure.repositories.room_repo_memory import InMemoryRoomRepository
# game_repo = RedisGameStateRepository()

class GameService:
    
    def __init__(self,room_repo):
        # self.game_repo = game_repo
        self.room_repo = room_repo
        
    def start_game(self, room_id: str, sid: str):
        room = self.room_repo.get(room_id)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")
        if sid != room.dealer.id:
            raise ValueError("ONLY_DEALER_CAN_START_GAME")
        if not room.has_players():
            raise ValueError("NOT_ENOUGH_PLAYERS")
        if not room.all_ready() :
            raise ValueError("NOT_ALL_PLAYERS_READY")
        room.start_game()
        self.room_repo.save(room)
        return room
    
    @staticmethod
    def end_game(self,room_id: str):
        room = self.room_repo.get(room_id)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")

        room.end_game()
        self.room_repo.save(room)

        return room
    
    def player_hit(self,room_id,player_id):
        room = self.room_repo.get(room_id)
        game = room.game
        game.player_hit(player_id)
        self.room_repo.save(room)
        return self.room
    
    def player_stand(self,room_id,player_id):
        room = self.room_repo.get(room_id)
        game = room.game
        game.player_stand(player_id)
        self.room_repo.save(room)
        return self.room
    
    def dealer_hit(self,room_id,dealer_id):
        room = self.room_repo.get(room_id)
        game = room.game
        game.dealer_hit(dealer_id)
        self.room_repo.save(room)
        return room
        
    def dealer_compare(self,dealer_id,player_id):
        result = self.room.game.dealer_compare(dealer_id,player_id)
        result = {i:v for i,v in enumerate(result)}
        return result
        