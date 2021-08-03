from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def hello_world():
    return render_template("index.html")


# connect to postgres server
@app.route("/destinations")
def get_destinations():
    return "Test"