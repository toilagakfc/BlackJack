# test_game.py

from server.deck import Deck, Card
from server.player import Player, Dealer
from server.rules import XiDachRules


def print_state(player, dealer):
    print("Player:", player.hand.cards, "→", player.hand.calculate_point())
    print("Dealer:", dealer.hand.cards, "→", dealer.hand.calculate_point())


# ---------- TEST CASES ----------

def test_blackjack():
    print("\n=== TEST XÌ DÁCH ===")
    p = Player("P")
    d = Dealer()

    p.hand.cards = [Card("A", "Cơ"), Card("K", "Bích")]
    d.hand.cards = [Card("9", "Rô"), Card("7", "Chuồn")]

    print_state(p, d)
    print(XiDachRules.compare(p, d))


def test_xi_bang():
    print("\n=== TEST XÌ BÀNG ===")
    p = Player("P")
    d = Dealer()

    p.hand.cards = [Card("A", "Cơ"), Card("A", "Bích")]
    d.hand.cards = [Card("A", "Rô"), Card("A", "Chuồn")]

    print_state(p, d)
    print(XiDachRules.compare(p, d))


def test_ngu_linh():
    print("\n=== TEST NGŨ LINH ===")
    p = Player("P")
    d = Dealer()

    p.hand.cards = [
        Card("2", "Cơ"),
        Card("3", "Rô"),
        Card("4", "Chuồn"),
        Card("5", "Bích"),
    ]
    p.hand.add_card(Card("J", "Cơ"))  # 5 lá, 20 điểm
    d.hand.cards = [Card("10", "Rô"), Card("7", "Chuồn")]

    print_state(p, d)
    print(XiDachRules.compare(p, d))


def test_both_bust():
    print("\n=== TEST CẢ HAI QUẮC ===")
    p = Player("P")
    d = Dealer()

    p.hand.cards = [Card("K", "Cơ"), Card("Q", "Rô"), Card("5", "Chuồn")]
    d.hand.cards = [Card("K", "Bích"), Card("Q", "Chuồn"), Card("6", "Rô")]

    print_state(p, d)
    print(XiDachRules.compare(p, d))


def test_normal_compare():
    print("\n=== TEST SO ĐIỂM THƯỜNG ===")
    p = Player("P")
    d = Dealer()

    p.hand.cards = [Card("9", "Cơ"), Card("8", "Rô")]   # 17
    d.hand.cards = [Card("10", "Chuồn"), Card("6", "Bích")]  # 16

    print_state(p, d)
    print(XiDachRules.compare(p, d))


if __name__ == "__main__":
    # test_blackjack()
    test_xi_bang()
    # test_ngu_linh()
    # test_both_bust()
    # test_normal_compare()