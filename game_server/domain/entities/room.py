# game_server/domain/entities/room.py
import uuid
import datetime
from domain.entities.player import Player
from domain.entities.dealer import Dealer
from domain.entities.game import Game


class Room:
    def __init__(self, room_id: str, dealer: Player):
        self.id = room_id
        self.dealer = dealer
        self.players: dict[str, Player] = {}
        self.game = None
        self.phase = "waiting"          # waiting | betting | betting_locked | playing | finished
        self.betting_state = None       # BettingState | None
        self.created_at = datetime.datetime.now()
        self.updated_at = None
        self.started_at = None
        self.ended_at = None

    # ── Factory ───────────────────────────────────────────────────────────

    @staticmethod
    def create(dealer: Dealer) -> "Room":
        room_id = uuid.uuid4().hex[:6].upper()
        return Room(room_id, dealer)

    # ── Players ───────────────────────────────────────────────────────────

    def add_player(self, player: Player):
        if player.id in self.players or player.id == self.dealer.id:
            raise ValueError("Player already in room")
        self.players[player.id] = player

    def remove_player(self, sid: str):
        if sid not in self.players:
            raise ValueError("Player not in room")
        del self.players[sid]

    # ── Predicates ────────────────────────────────────────────────────────

    def all_ready(self) -> bool:
        """All non-folded players are ready (have a bet)."""
        active = [p for p in self.players.values() if not p.folded]
        return bool(active) and all(p.ready for p in active)

    def has_players(self) -> bool:
        return len(self.players) > 0

    def active_players(self) -> list:
        """Players who have not folded."""
        return [p for p in self.players.values() if not p.folded]

    # ── Game lifecycle ────────────────────────────────────────────────────

    def reset(self):
        for p in self.players.values():
            p.reset()
        self.game = None
        self.betting_state = None
        self.phase = "waiting"

    def start_game(self) -> Game:
        if self.game:
            raise ValueError("Game already started")
        # Only non-folded players participate
        active = self.active_players()
        if not active:
            raise ValueError("NO_ACTIVE_PLAYERS")
        self.game = Game(dealer=self.dealer, players=active)
        self.phase = "playing"
        self.started_at = datetime.datetime.now()
        self.updated_at = datetime.datetime.now()
        return self.game

    def end_game(self):
        if not self.game:
            raise ValueError("Game not started")
        self.phase = "finished"
        self.game = None
        self.betting_state = None
        self.ended_at = datetime.datetime.now()
        self.updated_at = datetime.datetime.now()

    # ── Serialization ─────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "dealer": self.dealer.to_dict() if self.dealer else None,
            "players": [p.to_dict() for p in self.players.values()],
            "phase": self.phase,
            "betting_state": self.betting_state.to_dict() if self.betting_state else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Room":
        from domain.state.betting_state import BettingState

        dealer_data = data.get("dealer")
        dealer = Player.from_dict(dealer_data) if dealer_data else None

        room = cls(room_id=data["id"], dealer=dealer)
        room.players = {
            Player.from_dict(p).id: Player.from_dict(p)
            for p in data.get("players", [])
        }
        room.phase = data.get("phase", "waiting")
        room.game = None  # Game is stored separately

        bs_data = data.get("betting_state")
        room.betting_state = BettingState.from_dict(bs_data) if bs_data else None

        def _parse(v):
            return datetime.datetime.fromisoformat(v) if v else None

        room.created_at = _parse(data.get("created_at"))
        room.updated_at = _parse(data.get("updated_at"))
        room.started_at = _parse(data.get("started_at"))
        room.ended_at   = _parse(data.get("ended_at"))

        return room