import socketio
import time

sio = socketio.Client()


@sio.event
def connect():
    print("CONNECTED")


@sio.event
def room_created(data):
    print("ROOM CREATED:", data)
    global ROOM_ID
    ROOM_ID = data["room_id"]


@sio.event
def player_joined(data):
    print("PLAYER JOINED LIST:", data)


@sio.event
def error(data):
    print("ERROR:", data)


sio.connect("http://127.0.0.1:8000")

# 1. tạo phòng (dealer)
sio.emit("create_room_event", {"name": "Dealer_A"})
time.sleep(1)

# 2. giả lập player join
sio.emit("join_room", {"room_id": ROOM_ID, "name": "Player_1"})
time.sleep(0.5)

sio.emit("join_room", {"room_id": ROOM_ID, "name": "Player_2"})
time.sleep(0.5)

time.sleep(3)
sio.disconnect()