from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlsplit
import sqlalchemy as sql
from app import app, db
import app.forms as forms
from app.models import User

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

@login_required
@app.route("/profile/<username>")
def profile(username):
    if not current_user.is_authenticated: return redirect(url_for("login")) # just in case
    user = db.session.scalar(sql.select(User).where(User.username == username))
    if user is None: return "page not found", 404
    if current_user.username == username:
        return render_template("your_profile.html")
    return render_template("profile.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = forms.LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(sql.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data): 
            flash("Invalid username or password")
            return redirect(url_for("login"))
        login_user(user, remember=form.remember_me.data)
        return redirect(((next := request.args.get('next')) and urlsplit(next).netloc == "" and next) or url_for("home")) # check for a next parameter in the url, and check if that parameter doesn't redirect to another website, then redirect to that or to the home page
    return render_template("login.html", title="Login - Sitename", form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route("/create_account", methods=["GET", "POST"])
def create_account():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = forms.CreateAccountForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for("home"))
    return render_template("create_account.html", title="Create Account - Sitename", form=form)