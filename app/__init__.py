import os
from flask import Flask, redirect, url_for, session, render_template, send_from_directory, request
from authlib.integrations.flask_client import OAuth
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# dotenv setup
from dotenv import load_dotenv
from sqlalchemy.orm import backref
load_dotenv()

# App config
app = Flask(__name__)
# Session config
app.secret_key = os.getenv("APP_SECRET_KEY")
app.config['SESSION_COOKIE_NAME'] = 'google-login-session'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)
# PostgresSQL congig
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

#User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(), unique=True, nullable=False)
    name = db.Column(db.String())
    profile_pic = db.Column(db.String())
    # 1 -> many relationship with User -> Destination 
    # destination = db.relationship('Destination', backref='user', lazy=True)

    def __init__(self, email, name, profile_pic):
        self.email = email
        self.name = name
        self.profile_pic = profile_pic

# Destination model
class Destination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order = db.Column(db.Integer)
    alias = db.Column(db.String())
    address = db.Column(db.String())
    daysToStay = db.Column(db.Integer)
    #user_id = db.Column(db.Integer, db.ForeignKey('user.id', nullable=False))

    def __init__(self, order, address, alias, daysToStay):
        self.order = order
        self.address = address
        self.alias = alias
        self.daysToStay = daysToStay

# oAuth Setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo', 
    client_kwargs={'scope': 'openid email profile'},
)


@app.route('/')
def landing_page():
    email = dict(session).get('email', None)
    name = dict(session).get('name', None)
    return render_template("landing.html", title="Roadtrip", about="Something goes here")


@app.route('/planner')
def planner_page():
    return render_template("planner.html")


@app.route('/login')
def login():
    google = oauth.create_client('google')  # create the google oauth client
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/authorize')
def authorize():
    google = oauth.create_client('google')  # create the google oauth client
    token = google.authorize_access_token()  # Access token from google (needed to get user info)
    resp = google.get('userinfo')  # userinfo contains stuff u specificed in the scrope
    user_info = resp.json()
    # store email into db
    # storeInDb(user_info)
    # print(user_info)
    # stores the user email, name, and picture into session storage
    session['email'] = user_info['email']
    session['name'] = user_info['name']
    session['picture'] = user_info['picture']
    return redirect('/')


@app.route('/logout')
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect('/')


# logic to store user info into db
def storeInDb(userInfo):
    email = userInfo['email']
    # Will only store email if email does not already exist in db
    if Destination.query.filter_by(email=email).first() is not None:
        error = None
        if not email:
            error = "email is required."
        if error is None:
            new_user = Destination(email)
            db.session.add(new_user)
            db.session.commit()
            return f"User {email} created successfully"
        else:
            return error, 418
    else: return



# updates user
def updateUser(userId, userInfo):
    updateRow = Destination.query.filter_by(id=userId).first()
    updateRow.order =userInfo["order"]
    updateRow.address = userInfo["address"]
    updateRow.alias = userInfo["alias"]
    updateRow.daysToStay =userInfo["daysToStay"]
    db.session.commit()


#deletes userData
def deleteUserInfo(userId):
    deleteThis = Destination.query.filter_by(id=userId).first() 
    db.session.delete(deleteThis)