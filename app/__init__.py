import os
from flask import Flask, redirect, url_for, session, render_template, send_from_directory, request
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

# DestinationModel for SQLAlchemy
class DestinationModel(db.Model):
    __tablename__ = "destinations"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String())
    order = db.Column(db.Integer)
    address = db.Column(db.String())
    daysToStay = db.Column(db.Integer)

    def __init__(self, email, order, address, daysToStay):
        self.email = email
        self.order = order
        self.address = address
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
def hello_world():
    email = dict(session).get('email', None)
    name = dict(session).get('name', None)
    picture = dict(session).get('picture', None)
    return f'Hello, you are logged in as {email}! And your name is {name}'


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
def storeInDb(user_info):
    email = user_info['email']
    # Will only store email if email does not already exist in db
    if DestinationModel.query.filter_by(email=email).first() is not None:
        error = None
        if not email:
            error = "email is required."
        if error is None:
            new_user = DestinationModel(email)
            db.session.add(new_user)
            db.session.commit()
            return f"User {email} created successfully"
        else:
            return error, 418










# import os
# from flask import Flask, render_template, send_from_directory, request
# from werkzeug.security import generate_password_hash, check_password_hash
# from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate


# app = Flask(__name__)
# # PostgresSQL congig
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

# db = SQLAlchemy(app)
# migrate = Migrate(app, db)



# class UserModel(db.Model):
#     __tablename__ = "users"

#     id = db.Column(db.Integer, primary_key=True)
#     email = db.Column(db.String(), unique=True, nullable=False)
#     password = db.Column(db.String(), unique=True, nullable=False)

#     def __init__(self, email, password):
#         self.email = email
#         self.password = password

#     def __repr__(self):
#         return f"<User {self.email}>"


# class DestinationModel(db.Model):
#     __tablename__ = "destinations"

#     id = db.Column(db.Integer, primary_key=True)
#     userId = db.Column(db.String(), db.ForeignKey('users.id'))
#     order = db.Column(db.Integer)
#     address = db.Column(db.String())
#     daysToStay = db.Column(db.Integer)

#     def __init__(self, userId, order, address, daysToStay):
#         self.userId = userId
#         self.order = order
#         self.address = address
#         self.daysToStay = daysToStay



# # home route
# @app.route("/")
# def hello_world():
#     return render_template("index.html")


# # destinations route will GET list of destinations, or POST list of destinations from user
# @app.route("/destinations", methods=("GET", "POST"))
# def get_destinations():
#     if request.method == "GET":
#         # Logic to handle GET request
#         # return list of destinations by userID


#     else:
#         # Logic to handle POST request
#         # Add list of destinations


#     # Register route logic
# @app.route("/register", methods=("GET", "POST"))
# def register():
#     if request.method == "POST":
#         email = request.form.get("email")
#         password = request.form.get("password")
#         error = None

#         if not email:
#             error = "email is required."
#         elif not password:
#             error = "Password is required."
#         elif UserModel.query.filter_by(email=email).first() is not None:
#             error = f"User {email} is already registered."

#         if error is None:
#             new_user = UserModel(email, generate_password_hash(password))
#             db.session.add(new_user)
#             db.session.commit()
#             return f"User {email} created successfully"
#         else:
#             return error, 418

#     ## TODO: Return a restister page
#     return render_template("register.html")


# @app.route("/login", methods=("GET", "POST"))
# def login():
#     if request.method == "POST":
#         email = request.form.get("email")
#         password = request.form.get("password")
#         error = None
#         user = UserModel.query.filter_by(email=email).first()

#         if user is None:
#             error = "Incorrect email."
#         elif not check_password_hash(user.password, password):
#             error = "Incorrect password."

#         if error is None:
#             return "Login Successful", 200
#         else:
#             return error, 418

#     ## TODO: Return a login page
#     return render_template("login.html")