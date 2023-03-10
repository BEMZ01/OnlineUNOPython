import random


#########################################
# A standard UNO deck contains:         #
# 19 Red cards (0-9 and 1-9)            #
# 19 Green cards (0-9 and 1-9)          #
# 19 Blue cards (0-9 and 1-9)           #
# 19 Yellow cards (0-9 and 1-9)         #
# 8 Skip cards (2 of each color)        #
# 8 Reverse cards (2 of each color)     #
# 8 Draw Two cards (2 of each color)    #
# 4 Wild cards                          #
# 4 Wild Draw Four cards                #
# and if AllowBlankCards is True:       #
# 4 Blank cards                         #
#########################################


class Card():
    def __init__(self, type, color):
        self.type = type
        self.color = color

    def __str__(self):
        return self.type[0].capitalize() + " " + self.color[0].capitalize()

    def __repr__(self):
        return self.type + " " + self.color

    def __eq__(self, other):
        return self.type == other.type and self.color == other.color

    def __ne__(self, other):
        return not self.__eq__(other)

    def state(self):
        return {"type": self.type, "color": self.color}


class Deck:
    def __init__(self):
        self.cards = []

    def shuffle(self):
        random.shuffle(self.cards)

    def GetTopCard(self):
        return self.cards[0]

    def insertAt(self, i, card):
        self.cards.insert(i, card)

    def GetBottomCard(self):
        return self.cards[-1]

    def GetCardAt(self, index):
        return self.cards[index]


class Game:
    def __init__(self, settings, players):
        self.CurrentStackCount = 0
        self.SkipNextPlayer = False
        self.settings = settings
        self.MainDeck = Deck()
        self.DiscardDeck = Deck()
        colors = ["Red", "Green", "Blue", "Yellow"]
        for color in colors:
            for i in range(0, 10):
                self.MainDeck.cards.append(Card(str(i), color))
                self.MainDeck.cards.append(Card(str(i), color))
            for i in range(0, 2):
                self.MainDeck.cards.append(Card("Skip", color))
                self.MainDeck.cards.append(Card("Reverse", color))
                self.MainDeck.cards.append(Card("Draw-Two", color))
        for i in range(0, 4):
            self.MainDeck.cards.append(Card("Wild", "Black"))
            self.MainDeck.cards.append(Card("Wild-Draw-Four", "Black"))
        if self.settings["AllowBlankCards"]:
            for i in range(0, 4):
                self.MainDeck.cards.append(Card("Blank", "Black"))
        self.players = []
        self.round = 0

    def checkLegalMove(self, card):
        # A move is legal if:
        # 1. The card is a Wild or Wild Draw Four
        # 2. The card is the same color as the top card
        # 3. The card is the same type as the top card and the length
        # 4. The card is a Blank card
        top_card = self.DiscardDeck.GetTopCard()
        if card.type == "Wild" or card.type == "Wild-Draw-Four":
            return True
        elif card.color == top_card.color:
            return True
        elif card.type == top_card.type:
            for i in range(0, self.settings["MaxStack"]):
                # Check if a plus card is stacked on top of another plus card
                if top_card.type == "Draw-Two" or top_card.type == "Skip" or top_card.type == "Reverse":
                    top_card = self.DiscardDeck.GetCardAt(i + 1)
                else:
                    break
            if card.type == top_card.type:
                return True
        elif card.type == "Blank":
            return True
        else:
            return False


class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []

    def __str__(self):
        return self.name


class Game_Host:
    def __init__(self, AllowBlankCards=True, MaxPlayers=10, MaxRounds=100, MaxStack=3):
        self.settings = {
            "AllowBlankCards": AllowBlankCards,
            "MaxPlayers": MaxPlayers,
            "MaxRounds": MaxRounds,
            "MaxStack": MaxStack
        }
        self.game = Game(self.settings, [])

    def start_game(self):
        print("Welcome to UNO!")
        print("How many players are there?")
        while True:
            try:
                player_count = int(input())
                if player_count > self.settings["MaxPlayers"]:
                    print("Too many players! Max is " + str(self.settings["MaxPlayers"]))
                elif player_count < 2:
                    print("Not enough players! Min is 2")
                else:
                    break
            except ValueError:
                print("Please enter a number!")
        for i in range(0, player_count):
            self.game.players.append(Player("Player " + str(i + 1) + ""))
        print("Starting game with " + str(player_count) + " players!")
        self.game.MainDeck.shuffle()
        for player in self.game.players:
            for i in range(0, 7):
                player.hand.append(self.game.MainDeck.cards.pop())
        self.game.DiscardDeck.cards.append(self.game.MainDeck.cards.pop())
        while True:
            for player in self.game.players:
                if self.game.DiscardDeck.GetTopCard().type == "Reverse":
                    print("The direction of play has been reversed!")
                print(player.name + "'s turn!")
                if self.game.CurrentStackCount > 0:
                    # If there is a stack, tell the player how many cards they have to draw
                    print("You have to draw " + str(self.game.CurrentStackCount) + " cards!")
                    for i in range(0, self.game.CurrentStackCount):
                        player.hand.append(self.game.MainDeck.cards.pop())
                    self.game.CurrentStackCount = 0
                if self.game.SkipNextPlayer:
                    print("You have to skip your next turn!")
                    self.game.SkipNextPlayer = False
                    break
                print("Your hand is: ")
                for card in player.hand:
                    print(str(player.hand.index(card)) + ": " + str(card))
                print("The top card is: " + str(self.game.DiscardDeck.GetTopCard()))
                print("What card do you want to play?")
                while True:
                    try:
                        card_number = int(input())
                        if card_number > len(player.hand):
                            print("That card doesn't exist!")
                        else:
                            break
                        card = player.hand.GetCardAt(card_number - 1)
                        if not self.game.checkLegalMove(card):
                            print("That card is not legal!")
                    except ValueError:
                        print("Please enter a number!")
                card = player.hand.pop(card_number - 1)
                # Add the card to the top of the discard deck
                self.game.DiscardDeck.cards.append(card)
                if len(player.hand) == 0:
                    print("Congratulations! You won!")
                    return
                top_card = self.game.DiscardDeck.GetTopCard()
                if top_card.type == "Draw-Two":
                    self.game.CurrentStackCount += 2
                elif top_card.type == "Wild-Draw-Four":
                    self.game.CurrentStackCount += 4
                elif top_card.type == "Skip":
                    self.game.SkipNextPlayer = True
                elif top_card.type == "Reverse":
                    self.game.players.reverse()
                if len(self.game.MainDeck.cards) == 0:
                    self.game.MainDeck.cards = self.game.DiscardDeck.cards
                    self.game.DiscardDeck.cards = []
                    self.game.MainDeck.shuffle()
                self.game.round += 1
                if self.game.round > self.settings["MaxRounds"]:
                    print("Game ended in a draw!")
                    return


if __name__ == "__main__":
    game_host = Game_Host(AllowBlankCards=False)
    game_host.start_game()
