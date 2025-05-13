from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlsplit
import sqlalchemy as sql
from app import app, db
import app.forms as forms
from app.models import User, Movie, Review, Friend
import datetime

@app.route("/")
def home():
    return render_template("not_logged_in.html", title="Sitename")

@app.route("/movies")
def movies():
    sort_by = request.args.get("sort", "name")
    search_query = request.args.get("search", "").strip().lower()

    movies_query = sql.select(Movie)

    if search_query:
        movies_query = movies_query.where(Movie.title.ilike(f"%{search_query}%"))

    match sort_by:
        case "name":
            movies_query = movies_query.order_by(Movie.title.asc())
        case "rating_desc":
            movies_query = movies_query.order_by(Movie.avg_rating.desc())
        case "rating_asc":
            movies_query = movies_query.order_by(Movie.avg_rating.asc())
        case "genre":
            movies_query = movies_query.order_by(Movie.genre.asc())

    movies_list = db.session.scalars(movies_query).all()

    return render_template("movies.html", title="All Movies", movies=movies_list, sort_by=sort_by, search_query=search_query)

@app.route("/movie/<int:movie_id>", methods=["GET"])
def movie_page(movie_id):
    movie = db.session.get(Movie, movie_id)
    if movie is None:
        return "Movie not found", 404
    reviews = db.session.scalars(
        sql.select(Review).where(Review.movie_id == movie_id).order_by(Review.id.desc())
    ).all()
    return render_template("movie.html", title=movie.title, movie=movie, reviews=reviews)

@app.route("/movie/<int:movie_id>/review", methods=["POST"])
@login_required
def submit_review(movie_id):
    movie = db.session.get(Movie, movie_id)
    if movie is None:
        return "Movie not found", 404

    rating = request.form.get("rating", type=int)
    text = request.form.get("review", type=str)

    if not (1 <= rating <= 10):
        flash("Rating must be between 1 and 10.")
        return redirect(url_for("movie_page", movie_id=movie_id))

    review = Review(user_id=current_user.id, movie_id=movie_id, rating=rating, text=text)
    db.session.add(review)

    # update average rating
    reviews = db.session.scalars(sql.select(Review).where(Review.movie_id == movie_id)).all()
    movie.avg_rating = sum(r.rating for r in reviews) / len(reviews)

    db.session.commit()
    flash("Review submitted successfully!")
    return redirect(url_for("movie_page", movie_id=movie_id))

@app.route("/reviews")
def reviews():
    return "coming soon"

@app.route("/visualize")
def data():
    return "coming soon"

@app.route("/about")
def about():
    return "coming soon"

@login_required
@app.route("/profile")
def your_profile():
    return redirect(url_for("profile", username=current_user.username))

@login_required
@app.route("/profile/<username>")
def profile(username):
    user = db.session.scalar(sql.select(User).where(User.username == username))
    if user is None: return "page not found", 404
    if current_user.username == username:
        return render_template("your_profile.html", user=user)
    return render_template("profile.html", user=user)

@login_required
@app.route("/profile/<username>/friend_request", methods=["GET", "POST"])
def friend_request(username):
    other_user: User = db.session.scalar(sql.select(User).where(User.username == username))
    if other_user is None: return "user not found", 404
    if current_user.id == other_user.id: return "cant friend request yourself", 422
    other_user.friends.append(current_user)
    current_user.friends.append(other_user)
    db.session.commit()

    return "<pre>" + "\n".join(user.username for user in other_user.friends) + "</pre>"

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
        return redirect(((next := request.args.get('next')) and urlsplit(next).netloc == "" and next) or url_for("home"))
    return render_template("login.html", title="Login - Sitename", form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))

@app.route("/create_account", methods=["GET", "POST"])
def create_account():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    form = forms.CreateAccountForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for("home"))
    return render_template("create_account.html", title="Create Account - Sitename", form=form)
