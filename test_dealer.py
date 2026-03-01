import socketio
import time

SERVER = "http://127.0.0.1:8000"

dealer = socketio.Client()
player = socketio.Client()
player2 = socketio.Client()
ROOM_ID = None
PLAYER1_SID = None
PLAYER2_SID = None
player_sids = {}

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

# PLAYER 2
@player2.event
def connect():
    print("[PLAYER2] connected")

@player2.event
def dealer_public_state(data):
    print("[PLAYER2] dealer_public_state:", data)

# -------- DEALER --------
@dealer.event
def connect():
    print("[DEALER] connected")

@dealer.event
def room_created(data):
    global ROOM_ID
    ROOM_ID = data["room_id"]
    print("[DEALER] room created:", ROOM_ID)

@dealer.event
def player_joined(players):
    global player_sids
    player_sids = {p["name"]: p["sid"] for p in players if p["name"] != "Dealer"}
    print("[DEALER] players List:", players)

@dealer.event
def compare_result(data):
    print("[DEALER] compare_result:", data)

@dealer.event
def error(data):
    print("[DEALER] error:", data)

@dealer.event
def dealer_public_state(data):
    print("[DEALER] dealer_public_state:", data)

@dealer.event
def game_started(data):
    print("[DEALER] game_started:", data)
# -------- RUN TEST --------
dealer.connect(SERVER)
dealer.emit("create_room_event", {"name": "Dealer"})
time.sleep(2)

player.connect(SERVER)
player.emit("join_room", {"room_id": ROOM_ID, "name": "Player_1"})
time.sleep(2)
player2.connect(SERVER)
player2.emit("join_room", {"room_id": ROOM_ID, "name": "Player_2"})
time.sleep(2)

# BẮT BUỘC: start game để tạo engine
dealer.emit("start_game", {"room_id": ROOM_ID})
time.sleep(2)

# LẤY SID PLAYER (server-authoritative thì bạn có thể emit mapping,
# ở đây demo: dùng socketio client sid)

print("[TEST] Dealer compare Player")

dealer.emit(
    "dealer_action",
    {
        "room_id": ROOM_ID,
        "action": "compare",
        "target_sid": player_sids["Player_1"],
    }
)
time.sleep(2)
print("\n[TEST] Dealer HIT lần 1")
dealer.emit("dealer_action", {"room_id": ROOM_ID, "action": "hit"})
time.sleep(1)
time.sleep(2)

dealer.disconnect()
player.disconnect()
player2.disconnect()