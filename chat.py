from flask import Flask, redirect, url_for, render_template, request, session, abort, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy import *
from os import urandom
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #to suppress some warning that popped up
db = SQLAlchemy(app)

class User(db.Model):

	username = db.Column(db.String(80), primary_key=True)
	password = db.Column(db.String(80), nullable=False)
	
	def __repr__(self):
		return self.username

class Chatroom(db.Model):
	
	name = db.Column(db.String(80), primary_key=True)
	creator_name = db.Column(db.String(80), db.ForeignKey('user.username'), nullable=False)
	creator = db.relationship("User", backref=db.backref("chatrooms_created", lazy=True))

class Chatlog(db.Model):
	
	chatroom_name = db.Column(db.String(80), db.ForeignKey("chatroom.name"), nullable=False, primary_key=True)
	sender = db.Column(db.String(80), db.ForeignKey("user.username"), nullable=False, primary_key=True)
	message = db.Column(db.Text, nullable=False)
	timestamp = db.Column(db.DateTime, nullable=False, primary_key=True)

@app.cli.command()
def initdb():
	db.create_all()
	#owner = User(username=owner_login, password=owner_pw, account_type='owner')
	#db.session.add(owner) #hard code owner
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
		return render_template("createProfilePage.html", title="Become A Customer")

@app.route("/profile/")
@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username=None):
	if not username:
		# if no profile specified direct unlogged in users to the login page
		return redirect(url_for("logger"))
	logged_in = "username" in session and session["username"] == username
	if logged_in and request.method=="GET":
		return render_template('profilePage.html', user=username)			
	elif logged_in and request.method == "POST" and "cancel" in request.form:
		#delete from database
		event = Event.query.filter_by(date=request.form["cancel"]).first()
		db.session.delete(event)
		db.session.commit()
		flash("Event on " + request.form["cancel"] + " deleted!")
		return redirect(url_for("profile", username=username))
	elif logged_in and request.method == "POST" and "work" in request.form:
		#add to EventStaff table
		event_date = request.form["work"]
		#first query User objet that represents this staff
		staff = User.query.filter_by(username=username).first()
		#create EventStaff object
		event = EventStaff(date=event_date, staff_name=username, staffer=staff)
		db.session.add(event)
		try:
			db.session.commit()
			flash("You have successfully signed up for this event")
		except:
			flash("Something went wrong")
		return redirect(url_for("profile", username=username))
	elif logged_in and request.method == "POST":
		event_date = request.form["eventdate"]
		event_name = request.form["eventname"]
		#get user object from db
		user = User.query.filter_by(username=username).first()
		#make Event object
		event = Event(date=event_date, name=event_name, requester_name=username, requester=user)
		db.session.add(event)
		try:
			db.session.commit()
			flash("Event successfully scheduled!")
			return redirect(url_for("profile", username=username))
		except IntegrityError:
			db.session.rollback()
			flash("Sorry, we are already booked for that date")
			return redirect(url_for("profile", username=username))
	else:
		abort(401)
#Helper functions
def create_account(new_username, new_password):
	new_user = User(username=new_username, password=new_password)
	db.session.add(new_user)
	try:
		db.session.commit()
	except IntegrityError as ie:
		db.session.rollback()
		return "Duplicate"
	return None

app.secret_key = urandom(24)