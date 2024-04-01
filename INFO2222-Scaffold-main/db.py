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
    salt = os.urandom(16)
    hashed_password = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, 100000)
    salt_encoded = base64.b64encode(salt).decode('utf-8')
    hashed_password_encoded = base64.b64encode(hashed_password).decode('utf-8')
    return f"{salt_encoded}${hashed_password_encoded}"

def check_password(plain_password, stored_password):
    salt_encoded, hashed_password_encoded = stored_password.split('$')
    salt = base64.b64decode(salt_encoded)
    hashed_password = base64.b64decode(hashed_password_encoded)
    new_hashed_password = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, 100000)
    return new_hashed_password == hashed_password

# Modify the insert_user function to hash password before storing
def insert_user(username: str, password: str):
    with Session(engine) as session:
        hashed_password = hash_password(password)
        user = User(username=username, password=hashed_password)
        session.add(user)
        session.commit()

# gets a user from the database
def get_user(username: str):
    with Session(engine) as session:
        return session.get(User, username)
