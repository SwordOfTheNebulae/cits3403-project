# tests/test_models.py
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from datetime import datetime
from app.create_app import db, create_app
from app.models.models import User, Movie, Rate, Comment, Tags, UserTagPrefer


@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def test_user_creation(app):
    db.session.query(User).delete()
    db.session.commit()
    
    user = User(username='modeluser', password='123456', email='model@example.com')
    db.session.add(user)
    db.session.commit()
    assert User.query.count() == 1
    assert User.query.first().username == 'modeluser'


def test_movie_creation_and_to_dict(app):
    movie = Movie(
        name='Model Movie',
        director='Director X',
        country='AU',
        years=datetime.strptime('2024-01-01', '%Y-%m-%d'),
        leader='Actor A',
        d_rate_nums=123,
        d_rate='7.8',
        intro='A movie for testing.',
        image_link='some.jpg',
        douban_link='https://example.com'
    )
    db.session.add(movie)
    db.session.commit()
    assert Movie.query.count() == 1
    assert movie.to_dict()['name'] == 'Model Movie'


def test_rate_relationship(app):
    user = User(username='rateuser', password='123', email='r@example.com')
    movie = Movie(
        name='Rated Movie',
        director='Someone',
        country='CN',
        years=datetime.strptime('2023-01-01', '%Y-%m-%d'),
        leader='Somebody',
        d_rate_nums=100,
        d_rate='8.1',
        intro='Intro here.',
        image_link='poster.jpg',
        douban_link='https://douban.com/movie/123'
    )
    db.session.add_all([user, movie])
    db.session.commit()

    rate = Rate(user_id=user.id, movie_id=movie.id, mark=9.0)
    db.session.add(rate)
    db.session.commit()

    assert rate in user.rates
    assert rate in movie.rates


def test_comment_creation(app):
    user = User(username='commenter', password='aaa', email='c@example.com')
    movie = Movie(
        name='Commented Movie',
        director='Dr. C',
        country='NZ',
        years=datetime.strptime('2023-06-01', '%Y-%m-%d'),
        leader='Lead C',
        d_rate_nums=456,
        d_rate='9.0',
        intro='Good film.',
        image_link='cover.png',
        douban_link='https://douban.com/movie/c'
    )
    db.session.add_all([user, movie])
    db.session.commit()

    comment = Comment(user_id=user.id, movie_id=movie.id, content='Nice movie!')
    db.session.add(comment)
    db.session.commit()

    assert comment in user.comments
    assert comment in movie.comments


def test_tag_and_preference_relationship(app):
    user = User(username='tagtester', password='111', email='t@example.com')
    tag = Tags(name='Drama')
    db.session.add_all([user, tag])
    db.session.commit()

    prefer = UserTagPrefer(user_id=user.id, tag_id=tag.id, score=1.0)
    db.session.add(prefer)
    db.session.commit()

    assert prefer in user.tag_prefers
    assert prefer in tag.tag_prefers
