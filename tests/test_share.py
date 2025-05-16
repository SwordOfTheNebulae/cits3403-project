# tests/test_share.py
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from datetime import datetime
from app.create_app import db, create_app
from app.models.models import User, Movie, SharedRecommendation

import uuid

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.test_client() as client:
        with app.app_context():
            db.create_all()

            # 用唯一 ID 避免 username 冲突
            uid1 = str(uuid.uuid4())[:8]
            uid2 = str(uuid.uuid4())[:8]

            user1 = User(username=f'shareuser_{uid1}', password='123456', email=f'share_{uid1}@example.com')
            user2 = User(username=f'otheruser_{uid2}', password='abcdef', email=f'other_{uid2}@example.com')

            movie1 = Movie(
                name='Shared Movie',
                director='Director X',
                country='USA',
                years=datetime.strptime('2022-01-01', '%Y-%m-%d'),
                leader='Actor A',
                d_rate_nums=100,
                d_rate='7.5',
                intro='Intro of shared movie',
                image_link='poster.jpg',
                douban_link='http://douban.com/abc'
            )

            db.session.add_all([user1, user2, movie1])
            db.session.commit()

            # 把用户名传给测试用例
            app.config['TEST_USER1'] = user1.username
            app.config['TEST_USER2'] = user2.username

        yield client


def login(client, username=None, password='123456'):
    if username is None:
        username = client.application.config['TEST_USER1']
    return client.post('/login', data={
        'username': username,
        'password': password
    }, follow_redirects=True)


def test_create_share_page_loads(client):
    login(client)
    response = client.get('/create_share')
    assert response.status_code == 200
    assert b'Share Title' in response.data

def test_create_share_post(client):
    login(client)

    movie = Movie.query.first()
    user2 = User.query.filter_by(username='otheruser').first()

    response = client.post('/create_share', data={
        'title': 'My Share',
        'description': 'Watch this!',
        'movies': [movie.id],
        'shared_with': [user2.id],
        'is_public': False
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Share created successfully' in response.data
    assert SharedRecommendation.query.count() == 1

def test_my_shares_list(client):
    login(client)

    movie = Movie.query.first()
    user = User.query.filter_by(username='shareuser').first()

    # 人工添加一个分享
    share = SharedRecommendation(
        user_id=user.id,
        share_key='abc123',
        title='Test Share',
        description='A movie share',
        is_public=True
    )
    share.movies.append(movie)
    db.session.add(share)
    db.session.commit()

    response = client.get('/my_shares')
    assert b'Test Share' in response.data

def test_view_shared_page(client):
    login(client)
    share = SharedRecommendation.query.first()
    response = client.get(f'/view_shared/{share.share_key}')
    assert b'Test Share' in response.data or response.status_code == 200
