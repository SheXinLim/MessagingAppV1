'''
app.py contains all of the server application
this is where you'll find all of the get/post request handlers
the socket event handlers are inside of socket_routes.py
'''

from functools import wraps
from flask import Flask, flash, jsonify, redirect, render_template, request, abort, session, url_for
from flask_socketio import SocketIO
import db
import secrets
import ssl
import logging
from flask_wtf.csrf import CSRFProtect

# # this turns off Flask Logging, uncomment this to turn off Logging
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

app = Flask(__name__)
csrf = CSRFProtect(app)

# Define the decorator in your app.py
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# secret key used to sign the session cookie
app.config['SECRET_KEY'] = secrets.token_hex()

# Secure session cookie configuration
app.config.update(
    SESSION_COOKIE_SECURE=True,  # Only send cookies over HTTPS.
    SESSION_COOKIE_HTTPONLY=True,  # Prevent access via JavaScript.
    SESSION_COOKIE_SAMESITE='Lax'  # Guard against CSRF attacks.
)

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
@app.route("/login/user", methods=["POST"])
def login_user():
    if not request.is_json:
        abort(404)

    username = request.json.get("username")
    password = request.json.get("password")

    user =  db.get_user(username)
    if user is None:
        return "Error: User does not exist!"
    
    if not db.check_password(password, user.password):
        return "Error: Password does not match!"
    session['username'] = username  # Set username in session
    return url_for('home', username=request.json.get("username"))

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
    
    if db.get_user(username) is None:
        db.insert_user(username, password)
        session['username'] = username  # Automatically log in the user after signup
        return url_for('home', username=username)
    return "Error: User already exists!"

# handler when a "404" error happens
@app.errorhandler(404)
def page_not_found(_):
    return render_template('404.jinja'), 404

# home page, where the messaging app is
@app.route("/home")
@login_required
def home():
    username = request.args.get("username") or session.get("username")
    if username is None:
        abort(404)
    received_requests = db.get_received_friend_requests(username)
    sent_requests = db.get_sent_friend_requests(username)
    friends = db.get_friends(username)  # Get the list of friends

    return render_template("home.jinja", username=username, received_requests=received_requests, 
                           sent_requests=sent_requests, friends=friends)

@app.route('/logout')
@login_required
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

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
        return "Friend request sent successfully!"
    else:
        return "Friend request could not be sent (user may not exist or request already sent)"

@app.route("/friend-requests/<username>")
def friend_requests(username):
    requests = db.get_friend_requests(username)
    return {"friendRequests": requests}

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

# CSP header to your HTTP responses prevent Cross-Site Scripting (XSS)
@app.after_request
def set_csp_header(response):
    csp_policy = "default-src 'self'; script-src 'self' https://trusted.cdn.com;"
    response.headers.setdefault('Content-Security-Policy', csp_policy)
    return response

if __name__ == '__main__':
    #socketio.run(app)
    # for HTTPS Communication
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.load_cert_chain('cert/info2222.test.crt', 'cert/info2222.test.key')
        app.run(debug=True, ssl_context=context, host='127.0.0.1', port=5000)
 