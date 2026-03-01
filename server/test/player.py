import socketio
import time

SERVER = "http://127.0.0.1:8000"

player = socketio.Client()
player_sids = {}
ROOM_ID = None
PLAYER_SID = None

# -------- PLAYER --------
@player.event
def connect():
    print("[PLAYER] connected")

@player.event
def compare_result(data):
    print("[PLAYER] compare_result:", data)

@player.event
def error(data):
    print("[PLAYER] error:", data)
    
@player.event
def dealer_public_state(data):
    print("[PLAYER] dealer_public_state:", data)
    
@player.event
def player_joined(players):
    global player_sids
    player_sids = {p["name"]: p["sid"] for p in players if p["name"] != "Dealer"}
    print("[PLAYER] players List:", players)
    
@player.event
def game_started(data):
    print("[PLAYER] game_started:", data)

@player.event
def turn_state(data):
    print("[PLAYER] turn_state:", data)

@player.event
def player_ready(data):
    print("[PLAYER] player_ready:", data)   

@player.event
def room_closed(data):
    print("[PLAYER] room_closed:", data)

@player.event
def player_out(data):
    print("[PLAYER] player_out:", data)

@player.event
def player_kicked(data):
    print("[PLAYER] You were kicked:", data["kicked_by"])    

@player.event
def rooms_list(data):
    print("[PLAYER] rooms_list:", data)
    
@player.event
def room_closed():
    print("[PLAYER] room_closed")
player.connect(SERVER)
ROOM_ID = None

while True:
    try:
        a = input(
            "[JOINROOM <room_id> <name>] | ready | hit | stand | leave | exit > "
        )

        if a == "exit":
            break

        elif a.startswith("JOINROOM"):
            parts = a.split(" ")
            if len(parts) != 3:
                print("Sai cú pháp: JOINROOM <room_id> <player_name>")
                continue

            ROOM_ID = parts[2]
            name = parts[1]
            player.emit("join_room", {"room_id": ROOM_ID, "name": name})

        elif a == "ready":
            if not ROOM_ID:
                print("Chưa join room")
                continue
            player.emit("player_ready", {"room_id": ROOM_ID})

        elif a == "leave":
            if not ROOM_ID:
                print("Chưa join room")
                continue
            player.emit("leave_room", {"room_id": ROOM_ID})
            ROOM_ID = None

        elif a in ("hit", "stand"):
            if not ROOM_ID:
                print("Chưa join room")
                continue
            player.emit("player_action", {"room_id": ROOM_ID, "action": a})
        elif a == "rooms_list":
            player.emit("rooms_list")
        else:
            print(f"Command không hợp lệ: [{a}]")

    except KeyboardInterrupt:
        print("Player disconnecting...")
        break

player.disconnect()