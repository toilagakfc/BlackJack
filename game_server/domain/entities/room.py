import uuid
from domain.entities.player import Player
from domain.entities.dealer import Dealer
from domain.entities.game import Game
import datetime
class Room:
    def __init__(self, room_id: str, dealer: Player):
        self.id = room_id
        self.dealer = dealer
        self.players = {}
        self.game = None
        self.phase = "waiting"
        self.created_at = None
        self.updated_at = None
        self.started_at = None
        self.ended_at = None

    @staticmethod
    def create(dealer: Dealer):
        room_id = uuid.uuid4().hex[:6].upper()
        return Room(room_id, dealer)
    
    def add_player(self, player: Player):
        if player.id in self.players.keys() or player.id == self.dealer.id:
            raise ValueError("Player already in room")
        self.players[player.id] = player
    
    def remove_player(self, sid: str):
        if sid not in self.players.keys():
            raise ValueError("Player not in room")
        del self.players[sid]
        
    def all_ready(self):
        return all(p.ready for p in self.players.values()) 
    
    def has_players(self):
        return len(self.players) > 0
    
    def reset(self):
        for p in self.players.values():
            p.reset()
        self.game = None
        self.phase = "waiting"
    
    def start_game(self):
        if self.game:
            raise ValueError("Game already started")
        self.game = Game(dealer=self.dealer, players=list(self.players.values()))
        self.phase = "playing"
        self.started_at = datetime.datetime.now()
        print(f"Game started in room {self.id} at {self.started_at}")
        self.game.initial_deal()
        self.game.init_turn()
        self.updated_at = datetime.datetime.now()
        
    def end_game(self):
        if not self.game:
            raise ValueError("Game not started")
        self.phase = "finished"
        self.ended_at = datetime.datetime.now()
        self.updated_at = datetime.datetime.now()
    
    