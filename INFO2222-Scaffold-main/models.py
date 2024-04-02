'''
models
defines sql alchemy data models
also contains the definition for the room class used to keep track of socket.io rooms

Just a sidenote, using SQLAlchemy is a pain. If you want to go above and beyond, 
do this whole project in Node.js + Express and use Prisma instead, 
Prisma docs also looks so much better in comparison

or use SQLite, if you're not into fancy ORMs (but be mindful of Injection attacks :) )
'''

from sqlalchemy import String,Column, Integer, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Dict
from sqlalchemy.dialects.postgresql import JSON


# data models
class Base(DeclarativeBase):
    pass

# model to store user information
class User(Base):
    __tablename__ = "user"
    
    # looks complicated but basically means
    # I want a username column of type string,
    # and I want this column to be my primary key
    # then accessing john.username -> will give me some data of type string
    # in other words we've mapped the username Python object property to an SQL column of type String
        
    # Adding user_id as the primary key
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Making username a unique identifier, but not the primary key
    username: Mapped[str] = mapped_column(String, unique=True)
    #username: Mapped[str] = mapped_column(String, primary_key=True)
    password: Mapped[str] = mapped_column(String)
    

# stateful counter used to generate the room id
class Counter():
    def __init__(self):
        self.counter = 0
    
    def get(self):
        self.counter += 1
        return self.counter

# Room class, used to keep track of which username is in which room
class Room():
    def __init__(self):
        self.counter = Counter()
        # dictionary that maps the username to the room id
        # for example self.dict["John"] -> gives you the room id of 
        # the room where John is in
        self.dict: Dict[str, int] = {}

    def create_room(self, sender: str, receiver: str) -> int:
        room_id = self.counter.get()
        self.dict[sender] = room_id
        self.dict[receiver] = room_id
        return room_id
    
    def join_room(self,  sender: str, room_id: int) -> int:
        self.dict[sender] = room_id

    def leave_room(self, user):
        if user not in self.dict.keys():
            return
        del self.dict[user]

    # gets the room id from a user
    def get_room_id(self, user: str):
        if user not in self.dict.keys():
            return None
        return self.dict[user]
    
#user_id and friend_id are foreign keys that reference the id column of the user table.
#status is a string that can hold values like 'confirmed', 'pending', or 'rejected'.
#relationship is used to define a linkage with the User model so that you can easily access user details from a Friendship instance.

class FriendRequest(Base):
    __tablename__ = 'friend_request'

    sender_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.user_id'), primary_key=True)
    receiver_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.user_id'), primary_key=True)
    status: Mapped[str] = mapped_column(String)  # 'pending', 'accepted', 'rejected'

    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])


class Friendship(Base):
    __tablename__ = 'friendship'

    # Assuming you have an 'id' column in your 'User' model
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.user_id'))
    friend_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.user_id'))

    user = relationship("User", foreign_keys=[user_id])
    friend = relationship("User", foreign_keys=[friend_id])