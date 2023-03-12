import json
import random
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pprint import pprint

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

app = Flask(__name__)


class Card():
    def __init__(self, type, color):
        self.type = type
        self.color = color

    def __str__(self):
        return self.type + " " + self.color

    def __repr__(self):
        return self.type[0].capitalize() + " " + self.color[0].capitalize()

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
            try:
                for i in range(0, self.settings["MaxStack"]):
                    # Check if a plus card is stacked on top of another plus card
                    if top_card.type == "Draw-Two" or top_card.type == "Skip" or top_card.type == "Reverse":
                        top_card = self.DiscardDeck.GetCardAt(i + 1)
                    else:
                        break
            except IndexError:
                pass
            if card.type == top_card.type:
                return True
        elif card.type == "Blank":
            return True
        else:
            return False


class Player:
    def __init__(self, name):
        self.name = name
        self.hand = Deck()

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
                player.hand.insertAt(0, self.game.MainDeck.cards.pop())
        self.game.DiscardDeck.cards.append(self.game.MainDeck.cards.pop())
        while True:
            for player in self.game.players:
                if self.game.DiscardDeck.GetTopCard().type == "Wild" or self.game.DiscardDeck.GetTopCard().type == "Wild-Draw-Four":
                    print("The top card is a Wild card! What color would you like to change it to?")
                    while True:
                        color = input()
                        if color.lower() == "red" or color.lower() == "blue" or color.lower() == "green" or color.lower() == "yellow":
                            break
                        else:
                            print("Please enter a valid color!")
                    self.game.DiscardDeck.GetTopCard().color = color.title()
                if self.game.DiscardDeck.GetTopCard().type == "Reverse":
                    print("The direction of play has been reversed!")
                print(player.name + "'s turn!")
                if self.game.CurrentStackCount > 0:
                    # If there is a stack, tell the player how many cards they have to draw
                    print("You have to draw " + str(self.game.CurrentStackCount) + " cards!")
                    for i in range(0, self.game.CurrentStackCount):
                        player.hand.cards.append(self.game.MainDeck.cards.pop())
                    self.game.CurrentStackCount = 0
                if self.game.SkipNextPlayer:
                    print("You have to skip your next turn!")
                    self.game.SkipNextPlayer = False
                    break
                print("Your hand is: ")
                for card in player.hand.cards:
                    print(str(player.hand.cards.index(card)) + ": " + str(card))
                print("The top card is: " + str(self.game.DiscardDeck.GetTopCard()))
                print("What card do you want to play?")
                while True:  # Input validation
                    try:
                        card_number = input()
                        try:
                            card_number = int(card_number)
                        except ValueError:
                            if card_number == "draw":
                                player.hand.cards.append(self.game.MainDeck.cards.pop())
                                break
                            else:
                                print("Please enter a number!")
                                continue
                        if card_number > len(player.hand.cards):
                            print("That card doesn't exist!")
                        else:
                            card = player.hand.GetCardAt(card_number)
                            if not self.game.checkLegalMove(card):
                                print("That card is not legal!")
                            else:
                                break
                    except ValueError:
                        print("Please enter a number!")
                if type(card_number) == int:
                    card = player.hand.cards.pop(card_number)
                    # Add the card to the top of the discard deck
                    self.game.DiscardDeck.insertAt(0, card)
                if len(player.hand.cards) == 0:
                    print("Congratulations! You won!")
                    return
                if type(card_number) == int:  # If the player didn't draw a card
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


#######################
#######################
#######################


class Client:
    def __init__(self, ip_address):
        self.ip_address = ip_address
        self.name = get_username(ip_address)

    def __str__(self):
        return self.ip_address

    def __iter__(self):
        return iter([self.ip_address, self.name])

    def __eq__(self, other):
        return self.ip_address == other.ip_address and self.name == other.name

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return str(self.__dict__)


class Room:
    def __init__(self, name, host, password=None):
        self.name = name
        self.host = host
        self.password = password
        self.players = []
        self.game = Game_Host()
        self.game_started = False

    def add_player(self, player):
        self.players.append(player)

    def remove_player(self, player):
        self.players.remove(player)

    def start_game(self):
        self.game.start_game()
        self.game_started = True

    def modify_settings(self, settings):
        self.game.settings = settings

    def get_settings(self):
        return self.game.settings


class Room_Manager:
    def __init__(self):
        self.rooms = []

    def get_room(self, name):
        for room in self.rooms:
            if room.name == name:
                return room
        return None

    def delete_room(self, name):
        for room in self.rooms:
            if room.name == name:
                self.rooms.remove(room)
                return True
        return False

    def create_room(self, name, host, password=None):
        if len(password) == 0:
            password = None
        self.rooms.append(Room(name, host, password))
        return self.rooms[-1]


def get_username(ip_address):
    with open("storage/users.json", "r") as f:
        users = json.load(f)
    for user in users:
        if user["ip_address"] == ip_address:
            return user["name"]
    return ip_address


def set_username(ip_address, name):
    with open("storage/users.json", "r") as f:
        users = json.load(f)
    for user in users:
        # If IPaddress is already in the database overwrite the username
        if user["ip_address"] == ip_address:
            user["name"] = name
            with open("storage/users.json", "w") as f:
                json.dump(users, f)
            return True
    users.append({"ip_address": ip_address, "name": name})
    with open("storage/users.json", "w") as f:
        json.dump(users, f)
    return True


@app.route("/create_room", methods=["POST"])
def create_room():
    global rooms
    data = request.form.to_dict()
    rooms.create_room(data["name"], request.remote_addr, data["password"])
    return redirect(url_for("index"))


@app.route("/")
def index():
    global rooms
    return render_template("index.html", rooms=rooms.rooms, username=get_username(request.remote_addr))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/room/<room_name>")
def room(room_name):
    global rooms
    room = rooms.get_room(room_name)
    try:
        room.game_started
    except AttributeError:
        # Room doesn't exist
        return redirect(url_for("index"))
    if not room.game_started:
        if request.remote_addr == room.host:
            return render_template("room.html", room=room, username=get_username(request.remote_addr), host=True)
        # else if the ip address is in the room, render the player page
        elif request.remote_addr in [player.ip_address for player in room.players]:
            return render_template("room.html", room=room, username=get_username(request.remote_addr), player=True)
        else:
            return render_template("room.html", room=room, username=get_username(request.remote_addr))
    else:
        return render_template("room.html", room=room, username=get_username(request.remote_addr), game_started=True)


@app.route("/room/<room_name>/api/players", methods=["GET", "POST"])
def api_players(room_name):
    global rooms
    room = rooms.get_room(room_name)
    if request.method == "GET":
        out = []
        for player in room.players:
            out.append({
                "name": player.name,
                "isHost": player.ip_address == room.host
            })
        return jsonify(out)

    else:
        room.add_player(Client(request.remote_addr))
        return "", 201


@app.route("/room/<room_name>/api/settings", methods=["GET", "POST"])
def api_settings(room_name):
    global rooms
    room = rooms.get_room(room_name)
    if request.remote_addr != room.host:
        return "", 403
    if request.method == "GET":
        return jsonify(room.get_settings())
    else:
        data = request.form.to_dict()
        try:
            data["AllowBlankCards"]
        except KeyError:
            room.modify_settings({
                "MaxPlayers": int(data["MaxPlayers"]),
                "MaxRounds": int(data["MaxRounds"]),
                "MaxStack": int(data["MaxStack"]),
                "AllowBlankCards": False
            })
        else:
            room.modify_settings({
                "MaxPlayers": int(data["MaxPlayers"]),
                "MaxRounds": int(data["MaxRounds"]),
                "MaxStack": int(data["MaxStack"]),
                "AllowBlankCards": True
            })
        return redirect(url_for("room", room_name=room_name))


@app.route("/room/<room_name>/api/start_game", methods=["POST"])
def api_start_game(room_name):
    global rooms
    room = rooms.get_room(room_name)
    if request.remote_addr != room.host:
        return "", 403
    else:
        room.start_game()
        return "", 201


@app.route("/room/<room_name>/api/leave", methods=["POST"])
def api_leave(room_name):
    global rooms
    room = rooms.get_room(room_name)
    if request.remote_addr == room.host:
        rooms.delete_room(room_name)
        return redirect(url_for("index"))
    else:
        room.remove_player(request.remote_addr)
        return redirect(url_for("index"))


@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "GET":
        return render_template("settings.html", username=get_username(request.remote_addr), address=request.remote_addr)
    else:
        data = request.form.to_dict()
        set_username(request.remote_addr, data["username"])
        return redirect(url_for("index"))


@app.route("/room/<room_name>/api/status", methods=["GET"])
def api_status(room_name):
    global rooms
    room = rooms.get_room(room_name)
    ...


if __name__ == "__main__":
    rooms = Room_Manager()
    app.run("0.0.0.0", 5000, debug=True)
