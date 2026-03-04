
from game_server.domain.entities.Game import Game
from game_server.domain.rules.blackjack_rule import XiDachHandRule

def serialize_hand(hand, hide=False):
    if hide:
        return [hand.cards()[0].serialize(), {"rank": "Hidden", "suit": "Hidden"}]
    return [c.serialize() for c in hand.cards()]

def serialize_game(game: Game, hide_dealer=True):
    return {
        "players": [
            {
                "id": p.id,
                "name": p.name,
                "cards": serialize_hand(p.hand),
                "point": XiDachHandRule.calc_point(p.hand),
            }
            for p in game.players
        ],
        "dealer": {
            "cards": serialize_hand(game.dealer.hand, hide=hide_dealer),
            "point": (
                None if hide_dealer
                else XiDachHandRule.calc_point(game.dealer.hand)
            ),
        },
        "phase": game.phase,
    }