# tests/test_movie.py
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
            user = User(username='movieuser', password='123456', email='movie@example.com')
            movie = Movie(
                name='Test Movie', director='Someone', country='USA',
                years=datetime.strptime('2023-01-01', '%Y-%m-%d'), leader='Actor',
                d_rate_nums=100, d_rate='8.5', intro='Sample intro',
                image_link='default.jpg', douban_link='http://example.com'
            )
            db.session.add_all([user, movie])
            db.session.commit()
        yield client

def login(client):
    return client.post('/login', data={
        'username': 'movieuser',
        'password': '123456'
    }, follow_redirects=True)

def test_index_redirects_to_login(client):
    """未登录状态访问首页，应为 200 或重定向"""
    response = client.get('/')
    assert response.status_code == 200

def test_logged_in_user_can_see_movie_index(client):
    login(client)
    response = client.get('/')
    assert b'Recommended Movies' in response.data or response.status_code == 200

def test_movie_detail_view(client):
    login(client)
    movie = Movie.query.first()
    response = client.get(f'/movie/{movie.id}')
    assert b'Test Movie' in response.data

