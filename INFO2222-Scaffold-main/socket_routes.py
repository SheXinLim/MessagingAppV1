'''
socket_routes
file containing all the routes related to socket.io
'''


from flask_socketio import join_room, emit, leave_room
from flask import request

try:
    from __main__ import socketio
except ImportError:
    from app import socketio

from models import Room

import db

room = Room()

# when the client connects to a socket
# this event is emitted when the io() function is called in JS
@socketio.on('connect')
def connect():
    username = request.cookies.get("username")
    room_id = request.cookies.get("room_id")
    if room_id is None or username is None:
        return
    # socket automatically leaves a room on client disconnect
    # so on client connect, the room needs to be rejoined
    join_room(int(room_id))
    emit("incoming", (f"{username} has connected", "green"), to=int(room_id))



# # event when client disconnects
# # quite unreliable use sparingly
# @socketio.on('disconnect')
# def disconnect():
#     username = request.cookies.get("username")
#     room_id = request.cookies.get("room_id")
#     if room_id is None or username is None:
#         return
#     emit("incoming", (f"{username} has disconnected", "red"), to=int(room_id))

@socketio.on('disconnect')
def disconnect():
    username = request.cookies.get("username")
    room_id = request.cookies.get("room_id")
    if room_id is None or username is None:
        return
    
    # Emit a message to inform the other user about the disconnection
    emit("incoming", (f"{username} has disconnected", "red"), to=int(room_id))
    
    # Leave the room
    leave_room(room_id)
    
    # Clear any data related to the conversation
    if username in room_relationships:
        del room_relationships[username]



joined_users = set()






room_relationships = {}


@socketio.on("join")
def join(sender_name, receiver_name):
    receiver = db.get_user(receiver_name)
    if receiver is None:
        return "Unknown receiver!"

    sender = db.get_user(sender_name)
    if sender is None:
        return "Unknown sender!"

    if receiver_name not in db.get_friends(sender_name):
        return "You can only join rooms with friends."

    room_id = room.get_room_id(receiver_name)

    if room_id is not None:
        room.join_room(sender_name, room_id)
        join_room(room_id)
        
        # Add sender-receiver relationship to the room_relationships dictionary
        room_relationships.setdefault(sender_name, set()).add(receiver_name)
        
        # Emit to everyone in the room except the sender
        emit("incoming", (f"{sender_name} has joined the room.", "green"), to=room_id, include_self=False)
        # Emit only to the sender
        emit("incoming", (f"{sender_name} has joined the room. Now talking to {receiver_name}.", "green"))
        joined_users.add(sender_name)
        return room_id

    # If the user isn't inside any room
    room_id = room.create_room(sender_name, receiver_name)
    join_room(room_id)
    
    # Add sender-receiver relationship to the room_relationships dictionary
    room_relationships.setdefault(sender_name, set()).add(receiver_name)
    
    emit("incoming", (f"{sender_name} has joined the room. Now talking to {receiver_name}.", "green"), to=room_id)
    joined_users.add(sender_name)
    return room_id


@socketio.on("send")
def send(username, message, room_id):
    if username not in joined_users:
        return "You must join a room before sending messages."
    
    room_members = room.get_room_members(room_id)
    if not room_members or username not in room_members:
        return "Both users must join the room before sending messages."
    
    # Check if the sender and receiver have joined the room with each other's usernames
    sender_name = username
    receiver_name = None
    for name, relationships in room_relationships.items():
        if sender_name in relationships:
            receiver_name = name
            break
    
    if receiver_name is None or sender_name not in room_relationships.get(receiver_name, set()):
        return "Both users must join the room with each other's usernames before sending messages."

    room_members = room.dict.values() 
    
    if len(room_members) > 1 :
        emit("incoming", f"{username}: {message}", to=room_id)


# # send message event handler
# @socketio.on("send")
# def send(username, message, room_id):
#     emit("incoming", (f"{username}: {message}"), to=room_id)




    
# # join room event handler
# # sent when the user joins a room
# @socketio.on("join")
# def join(sender_name, receiver_name):
    
#     receiver = db.get_user(receiver_name)
#     if receiver is None:
#         return "Unknown receiver!"
    
#     sender = db.get_user(sender_name)
#     if sender is None:
#         return "Unknown sender!"

#     room_id = room.get_room_id(receiver_name)

#     # if the user is already inside of a room 
#     if room_id is not None:
        
#         room.join_room(sender_name, room_id)
#         join_room(room_id)
#         # emit to everyone in the room except the sender
#         emit("incoming", (f"{sender_name} has joined the room.", "green"), to=room_id, include_self=False)
#         # emit only to the sender
#         emit("incoming", (f"{sender_name} has joined the room. Now talking to {receiver_name}.", "green"))
#         return room_id

#     # if the user isn't inside of any room, 
#     # perhaps this user has recently left a room
#     # or is simply a new user looking to chat with someone
#     room_id = room.create_room(sender_name, receiver_name)
#     join_room(room_id)
#     emit("incoming", (f"{sender_name} has joined the room. Now talking to {receiver_name}.", "green"), to=room_id)
#     return room_id


@socketio.on("start_private_conversation")
def start_private_conversation(sender_name, receiver_name):
    room_id = room.create_room(sender_name, receiver_name)
    join_room(room_id)
    emit("private_conversation_started", room_id, room=room_id)

@socketio.on("private_message")
def private_message(username, message, room_id):
    emit("incoming", f"{username}: {message}", to=room_id)




# leave room event handler
@socketio.on("leave")
def leave(username, room_id):
    emit("incoming", (f"{username} has left the room.", "red"), to=room_id)
    leave_room(room_id)
    room.leave_room(username)