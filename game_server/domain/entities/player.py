from domain.value_objects.hand import Hand


class Player:
    def __init__(self, player_id: str, name: str):
        self.id = player_id
        self.name = name
        self.hand = Hand()
        self.standing = False
        self.busted = False

    def reset(self):
        self.hand.reset()
        self.standing = False
        self.busted = False

    def receive_card(self, card):
        """
        Player chỉ nhận bài, không hỏi tại sao
        """
        self.hand.add(card)

    def stand(self):
        self.standing = True