'''
app.py contains all of the server application
this is where you'll find all of the get/post request handlers
the socket event handlers are inside of socket_routes.py
'''
from flask import Flask, flash, jsonify, redirect, render_template, request, abort, session, url_for
from flask_socketio import SocketIO, emit
import db
import secrets
import ssl
import re
from datetime import datetime
from datetime import timedelta

# import logging

# this turns off Flask Logging, uncomment this to turn off Logging
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)
def csp_policy_string(policy_dict):
    return "; ".join([f"{key} {' '.join(val) if isinstance(val, list) else val}" for key, val in policy_dict.items()])

def emit_friend_updates(username):
    # Example to get data and emit correctly
    received_requests = db.get_received_friend_requests(username)
    sent_requests = db.get_sent_friend_requests(username)
    # Assuming the user is subscribed to their own room using their username
    socketio.emit('update_friend_requests', {
        'received_requests': received_requests,
        'sent_requests': sent_requests
    }, room=username)

app = Flask(__name__)
@app.after_request
def apply_csp(response):
    policy = {
    "default-src": "'self'",
    "script-src": [
        "'self'",
        "https://cdnjs.cloudflare.com",  # Allow scripts from CDN for Crypto-JS
        "'unsafe-inline'" 
    ],
    "style-src": "'self' 'unsafe-inline'",  # Allows inline styles;
    "img-src": "'self'",
    "connect-src": "'self'",  # Restricts the URLs which can be loaded using script interfaces
    "font-src": "'self'",  # Fonts loading
    "object-src": "'none'",  # Prevents object, embed, and applet elements from rendering
    "frame-ancestors": "'none'"  # Protects against clickjacking
}

    response.headers['Content-Security-Policy'] = csp_policy_string(policy)
    return response


# secret key used to sign the session cookie
app.config['SECRET_KEY'] = secrets.token_hex()
socketio = SocketIO(app)

# don't remove this!!
import socket_routes

# index page
@app.route("/")
def index():
    return render_template("index.jinja")

# login page
@app.route("/login")
def login():    
    return render_template("login.jinja")

# handles a post request when the user clicks the log in button
# @app.route("/login/user", methods=["POST"])
# def login_user():
#     if not request.is_json:
#         abort(404)

#     username = request.json.get("username")
#     password = request.json.get("password")

#     user =  db.get_user(username)
#     if user is None:
#         return "Error: User does not exist!"
#     # Check if account is currently locked

#     if user.lockout_until and datetime.now() < user.lockout_until:
#         return "Account is locked. Please try again later."
    
#     if not db.check_password(password, user.password):
#         # Increment failed attempts and check if lockout is necessary
#         user.failed_attempts += 1
#         if user.failed_attempts >= 3:
#             user.lockout_until = datetime.now() + timedelta(minutes=30)
#             db.save_user(user)
#             return "Account is locked. Please try again in 30 minutes."
#         return "Error: Password does not match!"
#     # Reset failed attempts on successful login
#     user.failed_attempts = 0
#     user.lockout_until = None
#     session['username'] = username  # Set username in session
#     return url_for('home', username=request.json.get("username"))

@app.route("/login/user", methods=["POST"])
def login_user():
    if not request.is_json:
        abort(404)

    username = request.json.get("username")
    password = request.json.get("password")
    user = db.get_user(username)

    if user is None:
        return jsonify({"error": "User does not exist!"})

    # Check if account is currently locked
    if user.lockout_until and datetime.now() < user.lockout_until:
        return jsonify({"error": "Account is locked. Please try again later."})

    if not db.check_password(password, user.password):
        user.failed_attempts += 1
        if user.failed_attempts >= 3:
            user.lockout_until = datetime.now() + timedelta(minutes=30)
            db.save_user(user)
            return jsonify({"error": "Account is locked. Please try again in 30 minutes."})
        db.save_user(user)
        return jsonify({"error": "Password does not match!"})

    # Reset failed attempts on successful login
    user.failed_attempts = 0
    user.lockout_until = None
    db.save_user(user)
    session['username'] = username
    return (url_for('home', username=username))

# handles a get request to the signup page
@app.route("/signup")
def signup():
    return render_template("signup.jinja")

# handles a post request when the user clicks the signup button
@app.route("/signup/user", methods=["POST"])
def signup_user():
    if not request.is_json:
        abort(404)
    username = request.json.get("username")
    password = request.json.get("password")

    if not username or not password:
        return "Error: Username and password are required."

    if db.get_user(username) is not None:
        # return "Error: User already exists!"
        return jsonify({"error": "User already exists!"})
    else:
        db.insert_user(username, password)
        session['username'] = username  # Automatically log in the user after signup
        # return url_for('home', username=username)
        return jsonify({"redirect": url_for('home')})

# handler when a "404" error happens
@app.errorhandler(404)
def page_not_found(_):
    return render_template('404.jinja'), 404

# home page, where the messaging app is
@app.route("/home")
def home():
    username = request.args.get("username") or session.get("username")
    if username is None:
        abort(404)
    received_requests = db.get_received_friend_requests(username)
    sent_requests = db.get_sent_friend_requests(username)
    friends = db.get_friends(username)  # Get the list of friends

    return render_template("home.jinja", username=username, received_requests=received_requests, 
                           sent_requests=sent_requests, friends=friends)

    # return render_template("home.jinja", username=request.args.get("username"),received_requests=received_requests, 
    #                        sent_requests=sent_requests)

# friend req
@app.route("/send-friend-request", methods=["POST"])
def send_friend_request_route():
    if not request.is_json:
        abort(400)

    sender_username = session.get("username")  # Assume the sender is the logged-in user
    receiver_username = request.json.get("receiver")

    if not sender_username:
        return "You must be logged in to send friend requests"

    if db.send_friend_request(sender_username, receiver_username):
        # Emit an update to both the sender and receiver
        emit_friend_updates(sender_username)
        emit_friend_updates(receiver_username)
        return "Friend request sent successfully!"
    else:
        return "Friend request could not be sent (user may not exist or request already sent)"

# @app.route("/friend-requests/<username>")
# def friend_requests(username):
#     requests = db.get_friend_requests(username)
#     return {"friendRequests": requests}
@app.route('/friend-requests')
def friend_requests():
    username = session.get('username')
    if not username:
        flash('You need to login first.')
        return redirect(url_for('login'))

    received_requests = db.get_received_friend_requests(username)
    sent_requests = db.get_sent_friend_requests(username)

    return render_template('friend_requests.jinja', 
                           received_requests=received_requests, 
                           sent_requests=sent_requests,
                           username=username)

@app.route("/accept-friend-request/<request_id>", methods=["POST"])
def accept_friend_request_route(request_id):
    username = session.get("username")  # Get username from session
    if not username:
        return "You must be logged in to accept friend requests", 403

    if db.accept_friend_request(int(request_id),username):
        return jsonify(message="Friend request accepted!") 
    else:
        return jsonify(message="Relog and try again") 
    
@app.route("/decline-friend-request/<request_id>", methods=["POST"])
def decline_friend_request_route(request_id):
    username = session.get("username")  # Get username from session
    if not username:
        return "You must be logged in to decline friend requests", 403

    success = db.decline_friend_request(int(request_id), username)
    if success:
        return jsonify(message="Friend request declined successfully") 
    else:
        return jsonify(message="Relog and try again")
    
@app.route('/logout')
def logout():
    session.clear()  # Clear all data from the session
    flash('You have been logged out.')
    return redirect(url_for('login'))  # Redirect to the login page or home page


if __name__ == '__main__':
    # socketio.run(app)
    # for HTTPS Communication
        # context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain('cert/info2222.test.crt', 'cert/info2222.test.key') 
        app.run(debug=True, ssl_context=context, host='127.0.0.1', port=5000) # debug should be false after fully implemented
 