import json
import os
import random
import sys
import time

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pprint import pprint
import datetime as dt

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
        try:
            return self.cards[0]
        except IndexError:
            return None

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
        self.current_turn = 0
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
        print(top_card.type, card.type)
        print(top_card.color, card.color)
        if card.type == "Wild" or card.type == "Wild-Draw-Four":
            return True
        elif card.color == top_card.color:
            return True
        elif card.type == top_card.type:
            try:
                while True:
                    i = 0
                    for card in self.DiscardDeck.cards:
                        if card.type == "Draw-Two":
                            i += 1
                        else:
                            break
                    print(i)
                    break
                if i < self.settings["MaxStack"]:
                    return True
                else:
                    return False
            except IndexError:
                pass
            if card.type == top_card.type:
                return True
        elif card.type == "Blank":
            return True
        else:
            return False


class Player:
    def __init__(self, name, address):
        self.name = name
        self.hand = Deck()
        self.address = address

    def __str__(self):
        return self.name


class Game_Host:
    def __init__(self, AllowBlankCards=False, MaxPlayers=10, MaxRounds=100, MaxStack=3, StartingCards=7):
        self.winner = None
        self.settings = {
            "AllowBlankCards": AllowBlankCards,
            "MaxPlayers": MaxPlayers,
            "MaxRounds": MaxRounds,
            "MaxStack": MaxStack,
            "StartingCards": StartingCards,
        }
        self.game = Game(self.settings, [])
        self.toSend = []
        self.started = False

    def start_game(self, players):
        self.started = True
        for player in players:
            self.game.players.append(Player(player.name, player.ip_address))
        self.game.MainDeck.shuffle()
        for player in self.game.players:
            for i in range(0, self.settings["StartingCards"]):
                player.hand.insertAt(0, self.game.MainDeck.cards.pop())
        self.game.DiscardDeck.cards.append(self.game.MainDeck.cards.pop())
        return self.game

    def play_card(self, player_address, cardIndex, wild_choice=None):
        if self.started:
            for player in self.game.players:
                if player.address == player_address and self.game.players[
                    self.game.current_turn].address == player_address:
                    try:
                        player.hand.GetCardAt(cardIndex)
                    except IndexError:
                        if str(len(player.hand.cards)) == str(cardIndex):
                            player.hand.cards.append(self.game.MainDeck.cards.pop())
                            self.advance_turn()
                            return True, "Card drew from MainDeck!"
                        else:
                            return False, "Card index out of range!"
                    card = player.hand.GetCardAt(cardIndex)
                    if self.game.checkLegalMove(card):
                        player.hand.cards.remove(card)
                        self.game.DiscardDeck.cards.insert(0, card)
                        if card.type == "Wild" or card.type == "Wild-Draw-Four":
                            if wild_choice is None:
                                return False, "You must choose a color!"
                            else:
                                card.color = wild_choice
                        if card.type == "Reverse":
                            self.game.players.reverse()
                        if card.type == "Skip":
                            self.game.SkipNextPlayer = True
                        if card.type == "Draw-Two":
                            self.game.CurrentStackCount += 2
                        if card.type == "Wild-Draw-Four":
                            self.game.CurrentStackCount += 4
                        if len(self.game.players[self.game.current_turn].hand.cards) == 0:
                            self.started = False
                            self.winner = self.game.players[self.game.current_turn]
                        self.advance_turn()
                        return True, "Card played successfully!"
                    else:
                        return False, "Illegal move!"
        return False, "False"

    def draw_card(self, player_address):
        if self.started:
            for player in self.game.players:
                if player.address == player_address and self.game.players[
                    self.game.current_turn].address == player_address:
                    player.hand.cards.append(self.game.MainDeck.cards.pop())
                    return True, "Card drawn successfully!"
        return False, "False"

    def advance_turn(self):
        # This function is called when the current player is done playing their turn
        if self.started:
            if len(self.game.MainDeck.cards) == 0:
                self.game.MainDeck.cards = self.game.DiscardDeck.cards
                self.game.DiscardDeck.cards = []
                self.game.MainDeck.shuffle()
            self.game.round += 1
            if self.game.round >= self.settings["MaxRounds"]:
                self.started = False
                return True, "Game over!"
            ###
            if self.game.DiscardDeck.GetTopCard().type == "Reverse":
                self.game.players.reverse()
            self.game.current_turn += 1
            if self.game.current_turn >= len(self.game.players):
                self.game.current_turn = 0
            if self.game.CurrentStackCount > 0:
                for i in range(0, self.game.CurrentStackCount):
                    self.game.players[self.game.current_turn].hand.cards.append(self.game.MainDeck.cards.pop())
                self.game.CurrentStackCount = 0
            if self.game.SkipNextPlayer:
                self.game.current_turn += 1
                if self.game.current_turn >= len(self.game.players):
                    self.game.current_turn = 0
                self.game.SkipNextPlayer = False
                return True, "Game over!"

    def get_status(self, player_address):
        # Returns a dictionary containing the status of the game, along with information about the players
        # This is sent to the client
        status = {
            "winner": self.winner.name if self.winner is not None else None,
            "players": [],
            "top_card": str(self.game.DiscardDeck.GetTopCard()),
            "round": self.game.round,
            "max_rounds": self.settings["MaxRounds"],
            "stack_count": self.game.CurrentStackCount,
            "skip_next_player": self.game.SkipNextPlayer,
            "main_deck_size": len(self.game.MainDeck.cards),
            "discard_deck_size": len(self.game.DiscardDeck.cards)}
        for player in self.game.players:
            status["players"].append({"name": player.name, "hand_size": len(player.hand.cards)})
        try:
            status["player_turn"] = {
                "name": self.game.players[self.game.current_turn].name,
                "hand_size": len(self.game.players[self.game.current_turn].hand.cards)
            }
        except IndexError:
            status["player_turn"] = {}
        status["player_hand"] = []
        # find the player using player_name
        for player in self.game.players:
            if player.address == player_address:
                for card in player.hand.cards:
                    status["player_hand"].append(str(card))
        return status

    def remove_player(self, player_address):
        for player in self.game.players:
            if player.address == player_address:
                for card in player.hand.cards:
                    self.game.DiscardDeck.cards.insert(-1, card)
                # if the current player is the one being removed, advance the turn
                if self.game.players[self.game.current_turn].address == player_address:
                    print("Removing currently playing player, advancing turn!")
                    self.advance_turn()

                self.game.players.remove(player)
                return True, "Player removed successfully!"
        return False, "False"


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
        self.hb_timings = {}
        self.win_check = False

    def add_player(self, player):
        self.players.append(player)
        self.hb_timings[player.ip_address] = time.time()

    def remove_player(self, player):
        self.players.remove(player)
        if player.ip_address in self.hb_timings:
            del self.hb_timings[player.ip_address]
        self.game.remove_player(player.ip_address)

    def start_game(self):
        self.game.start_game(self.players)
        self.game_started = True

    def reset_game(self):
        self.game = Game_Host()
        self.game_started = False

    def modify_settings(self, settings):
        self.game.settings = settings

    def get_settings(self):
        return self.game.settings

    def get_status(self, player_name):
        return {
            "players": self.players,
            "game_started": self.game_started,
            "game_status": self.game.get_status(player_name)
        }

    def heartbeat(self, address):
        # get the current seconds since the epoch
        ct = time.time()
        self.hb_timings[address] = time.time()
        for player in self.players:
            if player.ip_address in self.hb_timings:
                if ct - self.hb_timings[player.ip_address] > 10:
                    print("Player " + player.name + " timed out! (Room: " + self.name + ")")
                    self.remove_player(player)
        return True


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
        for room in self.rooms:
            if room.name == name:
                return None
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


@app.route("/room/<room_name>/game")
def game(room_name):
    global rooms
    room = rooms.get_room(room_name)
    try:
        room.game_started
    except AttributeError:
        # Room doesn't exist
        return redirect(url_for("index"))
    if room.game_started:
        return render_template("game.html", room=room, username=get_username(request.remote_addr), host=request.remote_addr == room.host, player=request.remote_addr in [player.ip_address for player in room.players])
    else:
        return redirect(url_for("room", room_name=room_name))


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
                "AllowBlankCards": False,
                "StartingCards": int(data["StartingCards"])
            })
        else:
            room.modify_settings({
                "MaxPlayers": int(data["MaxPlayers"]),
                "MaxRounds": int(data["MaxRounds"]),
                "MaxStack": int(data["MaxStack"]),
                "AllowBlankCards": True,
                "StartingCards": int(data["StartingCards"])
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
        return redirect(url_for("game", room_name=room_name))


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


@app.route("/room/<room_name>/api/heartbeat", methods=["GET"])
def api_heartbeat(room_name):
    """When a client joins a room, they send a heartbeat every 5 seconds to notify the server that they are still connected.
    If the server doesn't receive a heartbeat for 10 seconds, the client is disconnected from the room."""
    global rooms
    room = rooms.get_room(room_name)
    if request.remote_addr in [player.ip_address for player in room.players]:
        hb = room.heartbeat(request.remote_addr)
        if hb:
            data = room.game.get_status(request.remote_addr)
            if data["winner"] and not room.win_check:
                room.win_check = True
            elif room.win_check and data["winner"]:
                room.game_started = False
                room.reset_game()
            return jsonify(room.game.get_status(request.remote_addr)), 200
        else:
            return "", 403
    else:
        return "", 403


@app.route("/room/<room_name>/api/lobby_info", methods=["GET"])
def api_lobby_info(room_name):
    global rooms
    room = rooms.get_room(room_name)
    if request.remote_addr in [player.ip_address for player in room.players]:
        return jsonify(room.get_status(request.remote_addr)), 200
    else:
        return "", 403


@app.route("/room/<room_name>/api/play_card", methods=["POST"])
def api_play_card(room_name):
    global rooms
    room = rooms.get_room(room_name)
    if request.remote_addr in [player.ip_address for player in room.players] and request.remote_addr == room.players[
        room.game.game.current_turn].ip_address:
        cardIndex = str(request.data).replace("card", "").replace("=", "").replace("b", "").replace("'", "")
        if " " in cardIndex:
            play = room.game.play_card(request.remote_addr, int(cardIndex.split(" ")[0]), str(cardIndex.split(" ")[1]))
        else:
            play = room.game.play_card(request.remote_addr, int(cardIndex))
        try:
            if play[0]:
                return play[1], 200
            else:
                return play[1], 404
        except TypeError as e:
            print(e, play)  # why no work?
            return "error", 404
    else:
        return "error", 403


if __name__ == "__main__":
    # print cwd
    print(os.getcwd())
    rooms = Room_Manager()
    app.run("0.0.0.0", 8080, debug=True)