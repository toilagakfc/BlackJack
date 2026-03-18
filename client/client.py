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

# -------- Room EVENTS --------
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
def player_unready(data):
    print("player unready", data)
    
@client.event
def room_closed(data):
    print("Dealer has left", data)

# -------- Betting EVENTS --------
@client.on("bet:opened")
def on_bet_opened(data):
    """Server mở phase đặt cược."""
    print(
        f"[BET] Betting opened! "
        f"Min={data['min_bet']} | Max={data['max_bet']} | "
        f"Timeout={data['timeout_seconds']}s | Deadline={data.get('deadline')}"
    )

@client.on("bet:placed")
def on_bet_placed(data):
    """Một player vừa đặt cược thành công."""
    print(
        f"[BET] Player {data['player_id']} placed {data['amount']}. "
        f"Pot={data['pot']}"
    )

@client.on("bet:balance")
def on_bet_balance(data):
    """Response riêng cho lệnh check_balance."""
    print(f"[BET] Your balance: {data['balance']}")

@client.on("bet:timeout")
def on_bet_timeout(data):
    """Hết giờ đặt cược — một số player bị fold."""
    folded = data.get("folded", [])
    reason = data.get("reason", "timeout")
    if folded:
        print(f"[BET] Timeout ({reason})! Folded players: {folded}")
    else:
        print(f"[BET] Timeout — no players folded.")

@client.on("bet:locked")
def on_bet_locked(data):
    """Betting đã bị khóa, chuẩn bị deal bài."""
    print(
        f"[BET] Betting LOCKED. "
        f"Pot={data['pot']} | Bets={data['bets']}"
    )

# -------- Game EVENTS --------
@client.event
def game_started(data):
    print("game start", data)

@client.event
def game_updated(data):
    print("game_update:", data)  
    
@client.event
def game_finished(data):
    print("game finished", data)
    
@client.event
def player_turn(data):
    print("player turn", data)  

# -------- Dealer EVENTS --------
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
def turn_state(data):
    print("[DEALER] turn_state:", data)

    
# -------- RUN TEST --------
username = input("Enter username name: ").strip()
client.connect(SERVER, socketio_path='socket.io')

HELP = """
Commands:
  [Enter]        create_room (dealer)
  joinroom <id>  join a room
  ready          set ready
  unready        set unready
  leave          leave room
  kick           kick a player (dealer)
  rooms_list     list all rooms

  bet_start      open betting phase (dealer)
  bet <amount>   place a bet
  balance        check your balance
  bet_lock       lock betting early (dealer)

  start          start game (dealer, legacy — skips betting)
  hit            player hit
  stand          player stand
  dhit           dealer hit
  c              dealer compare one player
  exit           quit
"""
print(HELP)

while True:
    try:
        a = input("> ").strip()

        if a == "exit":
            break

        # ---- System ----
        elif a == "":
            print(f"Dealer {username} create_room")
            client.emit("create_room", {"name": username})

        # ---- Room ----
        elif a.startswith("joinroom"):
            parts = a.split(" ")
            if len(parts) != 2:
                print("Usage: joinroom <room_id>")
                continue
            client.emit("join_room", {"room_id": parts[1], "name": username})

        elif a == "ready":
            client.emit("player_ready", {"room_id": ROOM_ID})

        elif a == "unready":
            client.emit("player_unready", {"room_id": ROOM_ID})

        elif a == "leave":
            client.emit("leave_room", {"room_id": ROOM_ID})
            ROOM_ID = None

        elif a == "kick":
            target_sid = input("Enter player_sid to kick: ").strip()
            client.emit("kick_player", {"room_id": ROOM_ID, "target_sid": target_sid})

        elif a == "rooms_list":
            client.emit("room_list")

        # ---- Betting ----
        elif a == "bet_start":
            # Dealer mở phase đặt cược
            print(f"[BET] Opening betting phase for room {ROOM_ID}...")
            client.emit("bet_start", {"room_id": ROOM_ID})

        elif a.startswith("bet "):
            # Player đặt cược: "bet 100"
            parts = a.split(" ")
            if len(parts) != 2 or not parts[1].isdigit():
                print("Usage: bet <amount>  (e.g. bet 100)")
                continue
            amount = int(parts[1])
            print(f"[BET] Placing bet of {amount}...")
            client.emit("bet_place", {"room_id": ROOM_ID, "amount": amount})

        elif a == "balance":
            # Check balance trong betting phase
            client.emit("bet_check_balance", {"room_id": ROOM_ID})

        elif a == "bet_lock":
            # Dealer khoá betting sớm
            print(f"[BET] Locking betting for room {ROOM_ID}...")
            client.emit("bet_lock", {"room_id": ROOM_ID})

        # ---- Game (legacy / post-bet) ----
        elif a == "start":
            print(f"Dealer {username} start game, Room={ROOM_ID}")
            client.emit("start_game", {"room_id": ROOM_ID})

        elif a == "hit":
            client.emit("player_action", {"room_id": ROOM_ID, "action": "hit"})

        elif a == "stand":
            client.emit("player_action", {"room_id": ROOM_ID, "action": "stand"})

        elif a == "dhit":
            client.emit("dealer_action", {"room_id": ROOM_ID, "action": "hit"})

        elif a == "c":
            target_sid = input("Enter player_id to compare: ").strip()
            if not target_sid:
                print("No player_id entered.")
                continue
            client.emit(
                "dealer_action",
                {"room_id": ROOM_ID, "action": "compare", "target_sid": target_sid},
            )

        elif a == "public":
            client.emit("dealer_public_state", {"room_id": ROOM_ID})

        elif a == "help":
            print(HELP)

        else:
            print("Unknown command. Type 'help' to see all commands.")

    except KeyboardInterrupt:
        break

client.disconnect()