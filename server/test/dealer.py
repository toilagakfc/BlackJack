import socketio
import time

SERVER = "http://127.0.0.1:8000"

dealer = socketio.Client()
ROOM_ID = None

player_sids = {}

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

@dealer.event
def turn_state(data):
    print("[DEALER] turn_state:", data)

@dealer.event
def player_ready(data):
    print("[DEALER] player_ready:", data)
    
@dealer.event
def room_closed(data):
    print("[DEALER] room_closed:", data)
@dealer.event
def player_out(data):
    print("[DEALER] player_out:", data)
    
@dealer.event
def player_kicked(data):
    print("[DEALER] Player kicked:", data)

@dealer.event
def rooms_list(data):
    print("[DEALER] rooms_list:", data)
    
@dealer.event
def remove_room(data):
    print("[DEALER] room_closed:", data)
# -------- RUN TEST --------
dealer.connect(SERVER)
while True:
    try:
        a = input(
            "[Enter]=create_room | start | public | state | leave | c | hit | compare_all | exit > "
        ).strip()

        if a == "exit":
            break

        elif a == "":
            dealer.emit("create_room_event", {"name": "Dealer"})

        elif a == "start":
            dealer.emit("start_game", {"room_id": ROOM_ID})

        elif a == "public":
            dealer.emit("dealer_public_state", {"room_id": ROOM_ID})

        elif a == "state":
            dealer.emit("turn_state", {"room_id": ROOM_ID})

        elif a == "leave":
            dealer.emit("leave_room", {"room_id": ROOM_ID})

        elif a == "c":
            target_sid = input("Nhập <player_index>: ").strip()
            # # target_sid = player_sids.get(f"Player_{index}")
            # target_sid = player_sids.get({index})
            if not target_sid:
                print("Player không tồn tại")
                continue

            dealer.emit(
                "dealer_action",
                {
                    "room_id": ROOM_ID,
                    "action": "compare",
                    "target_sid": target_sid,
                },
            )

        elif a == "hit":
            dealer.emit(
                "dealer_action",
                {
                    "room_id": ROOM_ID,
                    "action": "hit",
                },
            )

        elif a == "compare_all":
            dealer.emit(
                "dealer_action",
                {
                    "room_id": ROOM_ID,
                    "action": "compare_all",
                },
            )
        elif a == "rooms_list":
            dealer.emit("rooms_list")
            
        elif a == "kick":
            if not ROOM_ID:
                print("Chưa join room")
                continue
            target_sid = input("Nhập <player_sid>: ").strip()
            dealer.emit("kick_player", {"room_id": ROOM_ID, "target_sid": target_sid})
        else:
            print("Command không hợp lệ")

    except KeyboardInterrupt:
        break

dealer.disconnect()
