# tests/test_user.py
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from datetime import datetime
from create_app import db, create_app
from models.models import User, Movie

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()
            user = User(username='testuser', password='123456', email='test@example.com')
            movie = Movie(
                name='Test Movie', director='Someone', country='USA',
                years=datetime.strptime('2022-01-01', '%Y-%m-%d'), leader='Actor', d_rate_nums=100,
                d_rate='8.5', intro='test movie', image_link='default.jpg',
                douban_link='http://example.com'
            )
            db.session.add_all([user, movie])
            db.session.commit()
        yield client


def login(client, username='testuser', password='123456'):
    return client.post('/login', data={
        'username': username,
        'password': password
    }, follow_redirects=True)


def test_personal_info_page(client):
    login(client)
    response = client.get('/personal')
    assert b'Personal Information' in response.data


def test_add_comment(client):
    login(client)
    movie = Movie.query.first()
    response = client.post(f'/comment/{movie.id}', data={
        'content': 'This is a test comment.'
    }, follow_redirects=True)
    assert b'Test Movie' in response.data


def test_rate_movie(client):
    login(client)
    movie = Movie.query.first()
    response = client.post(f'/rate/{movie.id}', data={
        'mark': '7.5'
    }, follow_redirects=True)
    assert b'Test Movie' in response.data


def test_collect_movie(client):
    login(client)
    movie = Movie.query.first()
    response = client.get(f'/collect/{movie.id}', follow_redirects=True)
    assert b'Test Movie' in response.data


def test_decollect_movie(client):
    login(client)
    movie = Movie.query.first()
    client.get(f'/collect/{movie.id}', follow_redirects=True)
    response = client.get(f'/decollect/{movie.id}', follow_redirects=True)
    assert b'Test Movie' in response.data
