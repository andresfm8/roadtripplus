import os
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

#----------------------------------------------------------------
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
    name = db.Column(db.String(), unique=True)
    person_id = db.Column(db.Integer, db.ForeignKey("person.id"))
    destination = db.relationship("Destination", backref="trip", lazy=True)

    def __init__(self, name, user_id):
        self.name = name
        self.user_id = user_id

    def __repr__(self):
        return f"Trip('{self.name}', '{self.user_id}')"


# Destination model
class Destination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order = db.Column(db.Integer)
    alias = db.Column(db.String())
    address = db.Column(db.String())
    daysToStay = db.Column(db.Integer)
    trip_id = db.Column(db.Integer, db.ForeignKey("trip.id"))

    def __init__(self, order, address, alias, daysToStay, trip_id):
        self.order = order
        self.address = address
        self.alias = alias
        self.daysToStay = daysToStay
        self.trip_id = trip_id

    def __repr__(self):
        return (
            f"Destinations("
            + "'{self.order}', '{self.alias}', '{self.address}', "
            + "'{self.daysToStay}', '{self.trip_id}')"
        )


# stores user information into db
def addUser(userInfo):
    email = userInfo["email"]
    name = userInfo["name"]
    # Will only store email if email does not already exist in db
    if Person.query.filter_by(email=email).first() is not None:
        error = None
        if not email:
            error = "email is required."
        if error is None:
            new_user = Person(email, name)
            db.session.add(new_user)
            db.session.commit()
            return f"User {email}, {name} created successfully"
        else:
            return error, 418 
    else:
        return


# updates userDestinations
# TODO: test this route and make sure it updates based on user_id, add checks
def updateUserDestination(userId, userInfo):
    updateRow = Person.query.filter_by(id=userId).first()
    updateRow.order = userInfo["order"]
    updateRow.address = userInfo["address"]
    updateRow.alias = userInfo["alias"]
    updateRow.daysToStay = userInfo["daysToStay"]
    updateRow.user_id = userId
    db.session.add(updateRow)
    db.session.commit()


# deletes userData
def deleteUserInfo(userId):
    delete = Destination.query.filter_by(id=userId).first()
    db.session.delete(delete)


# TODO: add more routes that talks to front end to send back User object



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
    addUser(user_info)
    # print(user_info)
    # stores the user email, name, and picture into session storage
    session["email"] = user_info["email"]
    session["name"] = user_info["name"]
    session["picture"] = user_info["picture"]
    return render_template("trips.html", user=user_info)


@app.route("/logout")
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect("/")

@app.before_first_request
def before_req_func():
    db.drop_all()
    db.create_all()


if __name__ == "__main__":
    db.init_app(app)
    app.run(host="0.0.0.0")