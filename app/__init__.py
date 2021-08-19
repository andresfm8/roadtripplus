import os
from dataclasses import dataclass
from flask import Flask, redirect, url_for, session, render_template
from authlib.integrations.flask_client import OAuth
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# dotenv setup
from dotenv import load_dotenv

load_dotenv()

# App config
app = Flask(__name__)
# Session config
app.secret_key = os.getenv("APP_SECRET_KEY")
app.config["SESSION_COOKIE_NAME"] = "google-login-session"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=5)
# PostgresSQL congig
# app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///test.db'
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "postgresql+psycopg2://{user}:{passwd}@{host}:{port}/{table}".format(
    user=os.getenv("POSTGRES_USER"),
    passwd=os.getenv("POSTGRES_PASSWORD"),
    host=os.getenv("POSTGRES_HOST"),
    port=5432,
    table=os.getenv("POSTGRES_DB"),
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# oAuth Setup
oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    access_token_url="https://accounts.google.com/o/oauth2/token",
    access_token_params=None,
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    authorize_params=None,
    api_base_url="https://www.googleapis.com/oauth2/v1/",
    userinfo_endpoint="https://openidconnect.googleapis.com/v1/userinfo",
    client_kwargs={"scope": "openid email profile"},
)

# ----------------------------------------------------------------
# db logic and helpers
# User model
class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(), unique=True, nullable=False)
    name = db.Column(db.String(20), default=None)
    # 1 -> many relationship with User -> Destination
    trips = db.relationship("Trip", backref="person", lazy=True)

    def __init__(self, email, name):
        self.email = email
        self.name = name

    def __repr__(self):
        return f"Person('{self.email}, '{self.name}')"


# Trip Model
class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    person_id = db.Column(db.Integer, db.ForeignKey("person.id"), nullable=False)
    destination = db.relationship("Destination", backref="trip", lazy=True)

    def __init__(self, name, person_id):
        self.name = name
        self.person_id = person_id

    def __repr__(self):
        return f"Trip('{self.name}', '{self.person_id}')"


# Destination model
class Destination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order = db.Column(db.Integer)
    address = db.Column(db.String())
    trip_id = db.Column(db.Integer, db.ForeignKey("trip.id"), nullable=False)

    def __init__(self, order, address, trip_id):
        self.order = order
        self.address = address
        self.trip_id = trip_id

    def __repr__(self):
        return f"Destinations('{self.order}', '{self.address}','{self.trip_id}')"


# stores user information into db
def addUser(userInfo):
    email = userInfo["email"]
    name = userInfo["name"]
    error = None
    if not email:
        error = "email is required."
    # Will only store email if email does not already exist in db
    if Person.query.filter_by(email=email).first() is None:
        if error is None:
            new_user = Person(email=email, name=name)
            db.session.add(new_user)
            db.session.commit()
            print(f"User {email}, {name} created successfully")
        else:
            return error, 418
    else:
        return


# checks if the user has any trips present in db
def checkTrips(userInfo):
    email = userInfo["email"]
    user = Person.query.filter_by(email=email).first()
    # Populating with dummy data
    trip1 = Trip(name="NY", person_id=user.id)
    # trip2 = Trip(name="SF", person_id=user.id)
    db.session.add(trip1)
    # db.session.add(trip2)
    db.session.commit()
    trip = Trip.query.first()
    dest1 = Destination(order="1", address="123 Test Ave", trip_id=trip.id)
    db.session.add(dest1)
    db.session.commit()
    trips = user.trips
    return trips


# adds a trip into the db
def addTrip(tripInfo):
    user = Person.query.filter_by(email=tripInfo["email"]).first()
    newTrip = Trip(name=tripInfo["name"], person_id=user.id)
    db.session.add(newTrip)
    db.session.commit()


# updates userDestinations
def updateUserDestination(userId, userInfo):
    updateRow = Person.query.filter_by(id=userId).first()
    updateRow.order = userInfo["order"]
    updateRow.address = userInfo["address"]
    updateRow.alias = userInfo["alias"]
    updateRow.daysToStay = userInfo["daysToStay"]
    updateRow.person_id = userId
    db.session.add(updateRow)
    db.session.commit()


# deletes userData
def deleteUserInfo(userId):
    delete = Destination.query.filter_by(id=userId).first()
    db.session.delete(delete)


@app.route("/")
def landing_page():
    return render_template("landing.html")


@app.route("/trips")
def trips_page():
    return render_template("trips.html")


@app.route("/planner")
def planner_page():
    return render_template("planner.html")


@app.route("/login")
def login():
    google = oauth.create_client("google")  # create the google oauth client
    redirect_uri = url_for("authorize", _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route("/authorize")
def authorize():
    google = oauth.create_client("google")  # create the google oauth client
    token = (
        google.authorize_access_token()
    )  # Access token from google (needed to get user info)
    resp = google.get("userinfo")  # userinfo contains stuff u specificed in the scrope
    user_info = resp.json()
    # store email into db
    added = addUser(user_info)
    # print(user_info)
    # stores the user email, name, and picture into session storage
    session["email"] = user_info["email"]
    session["name"] = user_info["name"]
    session["picture"] = user_info["picture"]
    user_info["added"] = added

    # checks if user has any trips stored

    trips = checkTrips(user_info)
    # if does then stores it into user_info dict
    user_info["trips"] = trips
    return render_template("trips.html", user=user_info)


@app.route("/logout")
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect("/")


# api route that returns destinations by trip_id
@app.route("/api/<trip_id>/destinations")
def getDestinations(trip_id):
    trip = Trip.query.filter_by(person_id=trip_id).first()
    destination = trip.destination
    str = ""
    # TODO: convert to json
    for value in destination:
        str += (
            f"order: {value.order}\naddress: {value.address}, trip_id: {value.trip_id} "
        )
    return str


@app.before_first_request
def before_req_func():
    # db.drop_all()
    db.create_all()


if __name__ == "__main__":
    db.init_app(app)
    app.run(host="0.0.0.0")
