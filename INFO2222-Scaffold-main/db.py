'''
db
database file, containing all the logic to interface with the sql database
'''

import base64
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import *

from pathlib import Path
import hashlib
import os

# creates the database directory
Path("database") \
    .mkdir(exist_ok=True)

# "database/main.db" specifies the database file
# change it if you wish
# turn echo = True to display the sql output
engine = create_engine("sqlite:///database/main.db", echo=False)

# initializes the database
Base.metadata.create_all(engine)


def hash_password(plain_password):
    # Hash the plain password and return the hash
    return bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt())

def check_password(plain_password, hashed_password):
    # Check if the plain password matches the hashed password
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)


# # inserts a user to the database
# def insert_user(username: str, password: str):
#     with Session(engine) as session:
#         user = User(username=username, password=password)
#         session.add(user)
#         session.commit()

# Modify the insert_user function to hash password before storing
def insert_user(username: str, password: str):
    with Session(engine) as session:
        #hashed_password = hash_password(password)
        user = User(username=username, password=password)
        session.add(user)
        session.commit()

# gets a user from the database
def get_user(username: str):
    with Session(engine) as session:
        return session.get(User, username)
