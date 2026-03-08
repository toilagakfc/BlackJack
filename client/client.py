import socketio
import time

SERVER = "http://127.0.0.1:8000"

client = socketio.Client()
ROOM_ID = None
player_index = None
player_sids = {}

# -------- System EVENTS --------
@client.event
def connect():
    print(client.get_sid())
    print("Connected")
@client.event
def pong():
    print("Server response")
@client.event
def error(data):
    print("Error:", data)
@client.event
def disconnect():
    print("Disconnected")
# --------Room EVENTS --------
@client.event
def room_list(data):
    print("Room List:", data)
    
@client.event
def player_joined(data):
    global ROOM_ID, player_sids
    print("Players List:", data)
    ROOM_ID = data["room_id"] if data else None
    player_sids = {i: p for i, p in enumerate(data["players"])}
    
@client.event
def player_ready(data):
    print("Player ready:", data)
@client.event
def left_room(data):
    print("You has left room:", data)
    
@client.event
def player_kicked(data):
    print("Player was kicked:", data)

@client.event
def kicked(data):
    print("You were kicked:", data) 
    
@client.event
def player_left(data):
    print("Player has left:", data)
    
@client.event
def room_closed(data):
    print("Dealer has left", data)

# -------- Game Event -------
@client.event
def game_started(data):
    print("game start",data)

@client.event
def game_updated(data):
    print("game_update:",data)    
# -------- DEALER --------
@client.event
def room_created(data):
    global ROOM_ID
    ROOM_ID = data["room_id"]
    name = data["dealer_name"]
    print(f"DEALER: {name}, Room created:", ROOM_ID)

@client.event
def compare_result(data):
    print("[DEALER] compare_result:", data)

@client.event
def dealer_public_state(data):
    print("[DEALER] dealer_public_state:", data)

@client.event
def turn_state(data):
    print("[DEALER] turn_state:", data)

    
# -------- RUN TEST --------
username = input("Enter username name: ").strip()
client.connect(SERVER)
while True:
    try:
        a = input(
            "[Enter]=create_room | joinroom | start | public | state | leave | c | hit | compare_all | exit > "
        ).strip()

        if a == "exit":
            break

        elif a == "leave":
            print(f"{username} send request leave room , Room_ID = {ROOM_ID}")
            client.emit("leave_room", {"room_id": ROOM_ID})
            ROOM_ID = None
        elif a == "public":
            client.emit("dealer_public_state", {"room_id": ROOM_ID})

        elif a == "hit":
            client.emit(
                "player_action",
                {
                    "room_id": ROOM_ID,
                    "action": "hit",
                },
            )
        elif a == "stand":
            client.emit(
                "player_action",
                {
                    "room_id": ROOM_ID,
                    "action": "stand",
                },
            )
        
        elif a == "rooms_list":
            client.emit("room_list")
            
        # ---- DEALER COMMANDS ----
        elif a == "":
            print(f"Dealer {username} create_room")
            client.emit("create_room", {"name": username})
        elif a == "start":
            print(f"Dealer {username} send start game request , Room_ID = {ROOM_ID}")
            client.emit("start_game", {"room_id": ROOM_ID})
            
        elif a.startswith("joinroom"):
            parts = a.split(" ")
            if len(parts) != 2:
                print("Sai cú pháp: joinroom <room_id>")
                continue
            print(f"Client {username} send join room request , Room_ID = {parts[1]}")
            client.emit("join_room", {"room_id": parts[1], "name": username})
            
        elif a == "kick":
            if not ROOM_ID:
                print("Chưa join room")
                continue
            target_sid = input("Nhập <player_sid>: ").strip()
            print(f"Dealer {username} kick player {target_sid} in room: {ROOM_ID}")
            client.emit("kick_player", {"room_id": ROOM_ID, "target_sid": target_sid})
        
        elif a == "dhit":
            client.emit(
                "dealer_action",
                {
                    "room_id": ROOM_ID,
                    "action": "hit",
                },
            )    
        elif a == "c":
            target_sid = input("Nhập <player_id>: ").strip()

            if not target_sid:
                print("Player không tồn tại")
                continue

            client.emit(
                "dealer_action",
                {
                    "room_id": ROOM_ID,
                    "action": "compare",
                    "target_sid": target_sid,
                },
            )
        # ----- PLAYER COMMANDS -----
        elif a == "ready":
            print(f"Client {username} send ready request , Room_ID = {ROOM_ID}")
            client.emit("player_ready", {"room_id": ROOM_ID})
        elif a == "unready":
            print(f"Client {username} send unready request , Room_ID = {ROOM_ID}")
            client.emit("player_unready", {"room_id": ROOM_ID})
            

        else:
            print("Command không hợp lệ")

    except KeyboardInterrupt:
        break

client.disconnect()
