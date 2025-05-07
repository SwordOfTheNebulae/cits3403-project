from app import app
from flask import render_template

@app.route("/")
def home():
    return render_template("not_logged_in.html", title="Sitename", account={"username": "john"})

@app.route("/movies")
def movies():
    return "comming soon"

@app.route("/reviews")
def reviews():
    return "comming soon"

@app.route("/visualize")
def data():
    return "comming soon"

@app.route("/about")
def about():
    return "comming soon"

@app.route("/profile")
def profile(username):
    return "comming soon"

@app.route("/login")
def login():
    return "comming soon"