from infrastructure.repositories.game_repo_memory import InMemoryGameRepository
from application.room_service import RoomService
game_repo = InMemoryGameRepository()
class GameService:
    
    def __init__(self,room_id):
        self.game_repo = game_repo
        self.room =RoomService.get_room(room_id)
    def player_hit(self,player_id):

        self.room.game.player_hit(player_id)
        return self.room
    def player_stand(self,player_id):
        self.room.game.player_stand(player_id)
        return self.room
    
    def dealer_hit(self,dealer_id):
        self.room.game.dealer_hit(dealer_id)
        return
        
    def dealer_compare(self,dealer_id,player_id):
        result = self.room.game.dealer_compare(dealer_id,player_id)
        result = {i:v for i,v in enumerate(result)}
        return result
        