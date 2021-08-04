import os
from flask import Flask, render_template, send_from_directory, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


app = Flask(__name__)
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



class UserModel(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(), unique=True, nullable=False)
    password = db.Column(db.String(), unique=True, nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __repr__(self):
        return f"<User {self.username}>"


class DestinationModel(db.Model):
    __tablename__ = "destinations"

    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.String(), db.ForeignKey('users.id'))
    order = db.Column(db.Integer)
    address = db.Column(db.String())
    daysToStay = db.Column(db.Integer)

    def __init__(self, userId, order, address, daysToStay):
        self.userId = userId
        self.order = order
        self.address = address
        self.daysToStay = daysToStay



# home route
@app.route("/")
def hello_world():
    return render_template("index.html")


# destinations route will GET list of destinations, or POST list of destinations from user
@app.route("/destinations", methods=("GET", "POST"))
def get_destinations():
    if request.method == "GET":
        # Logic to handle GET request
        # return list of destinations by userID


    else:
        # Logic to handle POST request
        # Add list of destinations


    # Register route logic
@app.route("/register", methods=("GET", "POST"))
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        error = None

        if not username:
            error = "Username is required."
        elif not password:
            error = "Password is required."
        elif UserModel.query.filter_by(username=username).first() is not None:
            error = f"User {username} is already registered."

        if error is None:
            new_user = UserModel(username, generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
            return f"User {username} created successfully"
        else:
            return error, 418

    ## TODO: Return a restister page
    return render_template("register.html")


@app.route("/login", methods=("GET", "POST"))
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        error = None
        user = UserModel.query.filter_by(username=username).first()

        if user is None:
            error = "Incorrect username."
        elif not check_password_hash(user.password, password):
            error = "Incorrect password."

        if error is None:
            return "Login Successful", 200
        else:
            return error, 418

    ## TODO: Return a login page
    return render_template("login.html")