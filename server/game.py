from rules import XiDachRules
from player import Player, Dealer
player = Player("Alice")
dealer = Dealer("Nhà cái")
result = XiDachRules.compare(player, dealer)

print(result["result"], result["reason"], result["multiplier"])