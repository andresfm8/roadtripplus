import os
import json
from typing_extensions import OrderedDict
from flask import Flask, request, redirect, url_for, session, render_template
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
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=10)
# PostgresSQL congig
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
# app.config[
#     "SQLALCHEMY_DATABASE_URI"
# ] = "postgresql+psycopg2://{user}:{passwd}@{host}:{port}/{table}".format(
#     user=os.getenv("POSTGRES_USER"),
#     passwd=os.getenv("POSTGRES_PASSWORD"),
#     host=os.getenv("POSTGRES_HOST"),
#     port=5432,
#     table=os.getenv("POSTGRES_DB"),
#)


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
    place_id = db.Column(db.String())
    area_name = db.Column(db.String())
    lat = db.Column(db.Integer)
    lng = db.Column(db.Integer)
    trip_id = db.Column(db.Integer, db.ForeignKey("trip.id"), nullable=False)

    def __init__(self, order, place_id, area_name, lat, lng, trip_id):
        self.order = order
        self.place_id = place_id
        self.area_name = area_name
        self.lat = lat
        self.lng = lng
        self.trip_id = trip_id

    def __repr__(self):
        return f"Destinations('{self.order}', '{self.place_id}','{self.area_name}','{self.lat}','{self.lng}','{self.trip_id}')"


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


# returns the user object
def getUser():
    user = {}
    user["email"] = session["email"]
    user["name"] = session["name"]
    user["picture"] = session["picture"]
    return user


def addDest(order, place_id, area_name, lat, lng):
    trip_id = session["trip_id"]
    newDest = Destination(order=order, place_id=place_id, area_name=area_name,lat=lat, lng=lng, trip_id=trip_id)
    db.session.add(newDest)
    db.session.commit()
    print("Success")


# checks if the user has any trips present in db
def checkTrips(userInfo):
    email = userInfo["email"]
    user = Person.query.filter_by(email=email).first()
    # Populating with dummy data
    # trip1 = Trip(name="NY", person_id=user.id)
    # trip2 = Trip(name="SF", person_id=user.id)
    # db.session.add(trip1)
    # db.session.add(trip2)
    # db.session.commit()
    # trip = Trip.query.first()
    # dest1 = Destination(order="1", address="123 Test Ave", trip_id=trip.id)
    # db.session.add(dest1)
    # db.session.commit()
    trips = user.trips
    return trips


# adds a trip into the db
def addTrip(email, trip_name):
    user = Person.query.filter_by(email=email).first()
    newTrip = Trip(trip_name, person_id=user.id)
    db.session.add(newTrip)
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
    user = getUser()
    # checks if user has any trips stored
    trips = checkTrips(user)
    # if does then stores it into user_info dict
    user["trips"] = trips
    return render_template("trips.html", user=user)


@app.route("/planner/<trip_id>")
def planner_page(trip_id):
    # TODO pull up destinations here
    #destinations = getDest(trip_id)
    session["trip_id"] = trip_id
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
    return redirect("/trips")


@app.route("/logout")
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect("/")

# api route that returns destinations by trip_id
def getDest(trip_id):
    trip = Trip.query.filter_by(person_id=trip_id).first()
    destination = trip.destination
    destDic = {}




# api route that creates a new trip and routes to trip page
@app.route("/api/create_trip/<trip_name>")
def createTrip(trip_name):
    email = session["email"]
    addTrip(email, trip_name)
    return redirect("/login")


@app.route("/api/destination/<trip_id>", methods=['POST', 'GET'])
def createDestinations(trip_id):
    # if get send data, if post save data
    if request.method == 'POST':
        json_data = request.data
        #print(json_data)
        json_list = json.loads(json_data)
        for p in json_list:
            order = (p['order'])
            place_id = (p['location_data']['place_id'])
            area_name = (p['location_data']['area_name'])
            lat = (p['location_data']['coordinate']['location']['lat'])
            lng = (p['location_data']['coordinate']['location']['lng'])
            addDest(order,place_id,area_name, lat,lng)
           

    # json_data contains an arry of destinations
        #addDest(order, dest_id, trip_id)
    return redirect("/planner")


@app.before_first_request
def before_req_func():
    # db.drop_all()
    db.create_all()


if __name__ == "__main__":
    db.init_app(app)
    app.run(host="0.0.0.0")
