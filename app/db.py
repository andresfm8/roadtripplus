import os
from flask import Flask, redirect, url_for, session, render_template, send_from_directory, request
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy

from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)
# app.secret_key = os.getenv("APP_SECRET_KEY")
# app.config("SQLALCHEMY_DATABASE_URI") = 'sqlite:///test.db'
# app.config[
#     "SQLALCHEMY_DATABASE_URI"
# ] = "postgresql+psycopg2://{user}:{passwd}@{host}:{port}/{table}".format(
#     user=os.getenv("POSTGRES_USER"),
#     passwd=os.getenv("POSTGRES_PASSWORD"),
#     host=os.getenv("POSTGRES_HOST"),
#     port=5432,
#     table=os.getenv("POSTGRES_DB"),
# )

# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
#migrate = Migrate(app, db)

#User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(), unique=True, nullable=False)
    name = db.Column(db.String(), default=None)
    profile_pic = db.Column(db.String())
    # 1 -> many relationship with User -> Destination 
    trip = db.relationship('Trip', backref='user', lazy=True)

    def __init__(self, email, name, profile_pic):
        self.email = email
        self.name = name
        self.profile_pic = profile_pic

    def __repr__(self):
        return f"User('{self.email}, '{self.name}')"

# Trip Model
class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), unique= True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    destination = db.relationship('Destination', backref="trip", lazy = True)

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
    trip_id = db.Column(db.Integer, db.ForeignKey('trip.id'))

    def __init__(self, order, address, alias, daysToStay, trip_id):
        self.order = order
        self.address = address
        self.alias = alias
        self.daysToStay = daysToStay
        self.trip_id = trip_id

    
    def __repr__(self):
        return f"Destinations('{self.order}', '{self.alias}', '{self.address}', '{self.daysToStay}', '{self.trip_id})"

# stores user information into db
def storeInDb(userInfo):
    email = userInfo['email']
    name = userInfo["name"]
    # Will only store email if email does not already exist in db
    if Destination.query.filter_by(email=email).first() is not None:
        error = None
        if not email:
            error = "email is required."
        if error is None:
            new_user = User(email=email, name=name)
            db.session.add(new_user)
            db.session.commit()
            return f"User {email} created successfully"
        else:
            return error, 418
    else: return



# updates userDestinations
# TODO: test this route and make sure it updates based on user_id, add checks
def updateUserDestination(userId, userInfo):
    updateRow = Destination.query.filter_by(id=userId).first()
    updateRow.order =userInfo["order"]
    updateRow.address = userInfo["address"]
    updateRow.alias = userInfo["alias"]
    updateRow.daysToStay =userInfo["daysToStay"]
    updateRow.user_id = userId
    db.session.add(updateRow)
    db.session.commit()


#deletes userData
def deleteUserInfo(userId):
    delete = Destination.query.filter_by(id=userId).first() 
    db.session.delete(delete)


# TODO: add more routes that talks to front end to send back User object