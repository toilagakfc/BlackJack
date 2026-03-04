def create_game():
    """Factory stub: create domain aggregates or initial game state."""
    # import here to avoid circular imports
    try:
        from game_server.domain.entities.Game import Game
        return Game()
    except Exception:
        return None
