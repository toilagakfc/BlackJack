# Design Notes

- Bounded contexts: game room, player management, persistence
- Aggregates: Room (aggregate root), Player, Game
- Keep domain rules in `game_server/domain/rules`
- Persistence adapters live in `game_server/infrastructure` (implement domain repository interfaces)
