# game_server/application/game_service.py
from datetime import datetime
from domain.entities.game import Game
from domain.state.game_state import GameState
class GameService:

    def __init__(self, room_repo, game_repo, player_repo):
        self.room_repo = room_repo
        self.game_repo = game_repo
        self.player_repo = player_repo

    # ── Helpers ───────────────────────────────────────────────────────────

    async def _get_room(self, room_id: str):
        room = await self.room_repo.get(room_id)
        if not room:
            raise ValueError("ROOM_NOT_FOUND")
        return room

    async def _get_game(self, room_id: str) -> Game:
        game = await self.game_repo.get(room_id)
        if not game:
            raise ValueError("GAME_NOT_FOUND")
        return game

    def _build_state(self, room_id: str, game: Game) -> GameState:
        return GameState.from_game(room_id, game)

    @staticmethod
    def _calc_delta(bet: int, result: str) -> int:
        return {"win": bet, "lose": -bet, "draw": 0}.get(result, 0)

    # ── Game lifecycle ────────────────────────────────────────────────────

    async def start_game(self, room_id: str, sid: str) -> GameState:
        room = await self._get_room(room_id)

        if room.phase == "playing":
            raise ValueError("ROOM_IS_PLAYING")
        if sid != room.dealer.id:
            raise ValueError("ONLY_DEALER_CAN_START")
        if not room.has_players():
            raise ValueError("NOT_ENOUGH_PLAYERS")
        if not room.all_ready():
            raise ValueError("NOT_ALL_PLAYERS_READY")

        # Load balance mới nhất từ DB cho tất cả player
        player_ids = list(room.players.keys())
        players_from_db = await self.player_repo.get_many(player_ids)
        for pid, player in room.players.items():
            if pid in players_from_db:
                player.balance = players_from_db[pid].balance

        game = room.start_game()
        game.initial_deal()
        game.init_turn()

        await self.room_repo.save(room)
        await self.game_repo.save(game, room_id)
        return self._build_state(room_id, game)

    async def end_game(self, room_id: str, sid: str) -> GameState:
        room = await self._get_room(room_id)
        game = await self._get_game(room_id)

        if sid != room.dealer.id:
            raise ValueError("ONLY_DEALER_CAN_END")
        if game.phase != "FINISHED":
            raise ValueError("GAME_NOT_FINISHED")

        room.end_game()

        await self.room_repo.save(room)
        await self.game_repo.delete(room_id)
        return self._build_state(room_id, game)

    # ── Bet ───────────────────────────────────────────────────────────────

    async def place_bet(self, room_id: str, player_id: str, amount: int) -> GameState:
        game = await self._get_game(room_id)
        player = game._get_player_or_raise(player_id)

        if game.phase != "PLAYER_TURN":
            raise ValueError("NOT_PLAYER_PHASE")
        if amount <= 0:
            raise ValueError("INVALID_BET_AMOUNT")
        if amount > player.balance:
            raise ValueError("INSUFFICIENT_BALANCE")

        player.bet = amount

        await self.game_repo.save(game, room_id)
        return self._build_state(room_id, game)

    # ── Player actions ────────────────────────────────────────────────────

    async def player_hit(self, room_id: str, player_id: str) -> GameState:
        game = await self._get_game(room_id)

        game.player_hit(player_id)

        await self.game_repo.save(game, room_id)
        return self._build_state(room_id, game)

    async def player_stand(self, room_id: str, player_id: str) -> GameState:
        game = await self._get_game(room_id)

        game.player_stand(player_id)

        await self.game_repo.save(game, room_id)
        return self._build_state(room_id, game)

    # ── Dealer actions ────────────────────────────────────────────────────

    async def dealer_hit(self, room_id: str, dealer_id: str) -> GameState:
        game = await self._get_game(room_id)

        game.dealer_hit(dealer_id)

        await self.game_repo.save(game, room_id)
        return self._build_state(room_id, game)

    async def dealer_compare(
        self, room_id: str, dealer_id: str, player_id: str
    ) -> tuple[GameState, dict]:
        room = await self._get_room(room_id)
        game = await self._get_game(room_id)
        result = game.dealer_compare(dealer_id, player_id)

        # Update balance
        player = game.get_player_by_id(player_id)
        delta = self._calc_delta(player.bet, result)
        # new_balance = await self.player_repo.update_balance(player_id, delta)
        new_balance = 0
        player.balance = new_balance
        if game.phase == 'FINISHED':
            room.phase = 'waiting'
            await self.room_repo.save(room)
        await self.game_repo.save(game, room_id)
        return self._build_state(room_id, game), {
            "result": result,
            "delta": delta,
            "balance": new_balance,
        }
