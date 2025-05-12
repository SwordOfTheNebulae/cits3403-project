from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import UniqueConstraint
import sqlalchemy as sa
from app import db, login

class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(sa.String(64), index=True, unique=True)
    email: Mapped[str] = mapped_column(sa.String(120), index=True, unique=True)
    password_hash: Mapped[Optional[str]] = mapped_column(sa.String(256))

    reviews = relationship("Review", back_populates="user")

    def __repr__(self):
        return f"<User {self.username}>"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))

class Movie(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(sa.String(128), index=True, nullable=False)
    genre: Mapped[str] = mapped_column(sa.String(64), nullable=True)
    avg_rating: Mapped[float] = mapped_column(sa.Float, nullable=True)  # 0.0 to 10.0
    release_year: Mapped[int] = mapped_column(nullable=False)
    __table_args__ = (UniqueConstraint("title", "release_year", name="unique movie title and year"),) # title and year are unique together

    reviews = relationship("Review", back_populates="movie")

    def __repr__(self):
        return f"<Movie {self.title}>"

class Review(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    rating: Mapped[int] = mapped_column()
    text: Mapped[str] = mapped_column(sa.Text)

    user_id: Mapped[int] = mapped_column(sa.ForeignKey("user.id"))
    movie_id: Mapped[int] = mapped_column(sa.ForeignKey("movie.id"))

    user = relationship("User", back_populates="reviews")
    movie = relationship("Movie", back_populates="reviews")
