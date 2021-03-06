from flask import Flask, redirect, url_for, render_template, request, session, abort, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy import *
from os import urandom
from datetime import datetime
import time
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #to suppress some warning that popped up
db = SQLAlchemy(app)

class User(db.Model):

	username = db.Column(db.String(80), primary_key=True)
	password = db.Column(db.String(80), nullable=False)
	#save the chatroom the user is in currently in db so its the same across different sessions
	current_room = db.Column(db.String(80), db.ForeignKey("chatroom.name"), nullable=True)

	def __repr__(self):
		return self.username

class Chatroom(db.Model):
	
	name = db.Column(db.String(80), primary_key=True)
	creator_name = db.Column(db.String(80), db.ForeignKey('user.username', use_alter=True), nullable=False)
	most_recent_poll = db.Column(db.DateTime)
	
	def __repr__(self):
		return self.name

class Chatlog(db.Model):
	
	chatroom_name = db.Column(db.String(80), db.ForeignKey("chatroom.name", ondelete="cascade"), nullable=False, primary_key=True)
	sender = db.Column(db.String(80), db.ForeignKey("user.username"), nullable=False, primary_key=True)
	message = db.Column(db.Text, nullable=False)
	timestamp = db.Column(db.DateTime, nullable=False, primary_key=True)
	chatroom = db.relationship("Chatroom", backref=db.backref("log", cascade="all, delete-orphan"))
	
	def __repr__(self):
		return self.sender + ": " + self.message + " at " + str(self.timestamp)

@app.cli.command()
def initdb():
	db.drop_all()
	db.create_all()
	db.session.commit()

@app.route('/')
def default():
	return redirect(url_for("logger"))

@app.route('/login/', methods=["GET", "POST"])
def logger():
	if "username" in session:
		return redirect(url_for("profile", username=session["username"]))
		
	elif request.method == "POST":
		#query db
		user = User.query.filter_by(username=request.form["user"]).first()
		
		if user is not None:
			password = user.password
			if password == request.form["pass"]:
				#login successful
				session["username"] = request.form["user"]
				return redirect(url_for("profile", username=user.username))
		# bad password or bad username, just login again
		flash("Invalid login. Try again")
		return redirect(url_for("logger"))
	else:
		return render_template("loginPage.html")

@app.route("/logout/")
def unlogger():
	# if logged in, log out, otherwise offer to log in
	if "username" in session:
		# note, here were calling the .clear() method for the python dictionary builtin
		leave_room(session["username"])
		session.clear()
		return render_template("logoutPage.html")
	else:
		return redirect(url_for("logger"))

@app.route("/create_profile/", methods=["GET", "POST"])
def create_profile():
	
	if request.method == "POST":
		
		failure = create_account(request.form["user"], request.form["pass"])
		if "Duplicate" == failure:
			flash("Username already exists. Try something different")
			return redirect(url_for("create_profile"))
		#once new account is registered first set session
		session["username"] = request.form["user"]
		#then redirect to profile
		flash("Your account has been created successfully")
		return redirect(url_for("profile", username=request.form["user"]))
	else:
		return render_template("createProfilePage.html", title="Sign Up For an Account")

@app.route("/profile/")
@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username=None):
	if not username:
		# if no profile specified direct unlogged in users to the login page
		return redirect(url_for("logger"))
	logged_in = "username" in session and session["username"] == username
	if logged_in and request.method=="GET":
		return render_template('profilePage.html', user=username, chatrooms=get_chatrooms())			
	elif logged_in and request.method == "POST" and "create" in request.form:
		new_chatroom_name = request.form["create"]
		chatroom = Chatroom(name=new_chatroom_name, creator_name=session["username"], most_recent_poll=datetime.now())
		db.session.add(chatroom)
		try:
			db.session.commit()
			flash("Chatroom created!")
		except:
			flash("Something went wrong!")
		return redirect(url_for("profile", username=username))
	elif logged_in and request.method == "POST" and "join" in request.form:
		chatroom_name = request.form["join"]
		currently_in = User.query.filter_by(username=username).first()
		if currently_in.current_room is not None and currently_in.current_room != chatroom_name:
			flash("You are already in a chatroom!")
			return redirect(url_for("profile", username=username))
		currently_in.current_room = chatroom_name
		db.session.commit();
		chatroom = Chatroom.query.filter_by(name=chatroom_name).first()
		return redirect(url_for("rooms", chatroom=chatroom))
	elif logged_in and request.method == "POST" and "delete" in request.form:
		to_del_name = request.form["delete"]
		chatroom = Chatroom.query.filter_by(name=to_del_name).first()
		db.session.delete(chatroom)
		try:
			db.session.commit()
			users = User.query.all()
			for user in users:
				if user.current_room == to_del_name:
					user.current_room = None
					db.session.commit()
			flash("Chatroom deleted!")
		except:
			flash("Something went wrong, please try again!")
		return redirect(url_for("profile", username=username))
	else:
		abort(401)

@app.route("/rooms/", methods=["GET", "POST"])
@app.route("/rooms/<chatroom>", methods=["GET", "POST"])
def rooms(chatroom=None):
	logged_in = "username" in session
	if not logged_in:
		return redirect(url_for("logger"))
	elif request.method == "POST" and "join" in request.form:
		#join chatroom
		chatroom_name = request.form["join"]
		chatroom_tojoin = Chatroom.query.filter_by(name=chatroom_name).first()
		currently_in = User.query.filter_by(username=session["username"]).first()
		if currently_in.current_room is not None and currently_in.current_room != chatroom_tojoin:
			flash("You are already in a chatroom!")
			return redirect(url_for("profile", username=username))
		currently_in.current_room = chatroom_name
		db.session.commit();
		return redirect(url_for("rooms", chatroom=chatroom_tojoin))
	elif request.method == "POST" and "leave" in request.form:
		leave_room(session["username"])
		return redirect(url_for("profile", username=session["username"]))
	elif chatroom is None:
		return render_template("roomsPage.html", chatrooms=get_chatrooms())
	elif chatroom is not None:
		return render_template("roomPage.html", chatroom=chatroom)

#AJAX Methods#

@app.route("/get_messages/<chatroom>")
def get_messages(chatroom=None):
	if chatroom:
		room = Chatroom.query.get(chatroom)
		if not room:
			flash("Oh no! The chatroom was deleted by the owner!")
			return url_for("profile")
		chat_history = Chatlog.query.order_by(Chatlog.timestamp).filter_by(chatroom_name=chatroom).all()
		messages = []
		message_dict = {}
		for message in chat_history:
			message_dict = {"sender":message.sender, "text":message.message, "time":message.timestamp}
			messages.append(message_dict)
	return jsonify(messages)

@app.route("/get_new_messages/<chatroom>")
def get_new_messages(chatroom=None):
	if chatroom:
		new_mrp = datetime.now()
		#check if room was deleted
		room = Chatroom.query.get(chatroom)
		if not room:
			flash("Oh no! The chatroom was deleted by the owner!")
			return url_for("profile")
		
		#room = Chatroom.query.filter_by(name=chatroom).first()
		mrp = room.most_recent_poll
		new_logs = Chatlog.query.order_by(Chatlog.timestamp).filter(Chatlog.chatroom_name==chatroom, Chatlog.timestamp > mrp).all()
		messages = []
		message_dict = {}
		for message in new_logs:
			message_dict = {"sender":message.sender, "text":message.message, "time":message.timestamp}
			messages.append(message_dict)
		room.most_recent_poll = new_mrp
		db.session.commit()
	return jsonify(messages)

@app.route("/post_message/", methods=["POST"])
def post_message():
	timestamp = datetime.now()
	message = request.form["message"]
	chatroom = request.form["chatroom"]
	sender = session["username"]
	new_message = Chatlog(chatroom_name=chatroom, sender=sender, message=message, timestamp=timestamp)
	db.session.add(new_message)
	db.session.commit()
	return jsonify(sender)
	

#Helper functions#

def create_account(new_username, new_password):
	new_user = User(username=new_username, password=new_password)
	db.session.add(new_user)
	try:
		db.session.commit()
	except IntegrityError as ie:
		db.session.rollback()
		return "Duplicate"
	return None

def get_chatrooms():
	return Chatroom.query.all()

def leave_room(username):
	currently_in = User.query.filter_by(username=username).first()
	currently_in.current_room = None
	db.session.commit()

app.secret_key = urandom(24)