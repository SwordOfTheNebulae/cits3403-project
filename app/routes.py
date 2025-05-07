from app import app
from flask import render_template
import app.forms as forms

@app.route("/")
def home():
    return render_template("not_logged_in.html", title="Sitename")

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
    form = forms.LoginForm()
    return render_template("login.html", title="Login - Sitename", form=form)

@app.route("/create_account")
def create_account():
    form = forms.CreateAccountForm()
    return render_template("create_account.html", title="Create Account - Sitename", form=form)