# tests/test_auth.py
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from create_app import db, create_app


@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # 禁用 CSRF 方便测试
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # 使用内存数据库

    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()
        yield client


def test_register(client):
    response = client.post('/register', data={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'password123',
        'password2': 'password123'
    }, follow_redirects=True)

    # 调试时可用：print(response.data.decode())
    assert response.status_code == 200
    assert b'username' in response.data or b'Log In' in response.data


def test_login_success(client):
    client.post('/register', data={
        'username': 'testuser2',
        'email': 'test2@example.com',
        'password': 'abc123456',
        'password2': 'abc123456'
    }, follow_redirects=True)

    response = client.post('/login', data={
        'username': 'testuser2',
        'password': 'abc123456'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Movie' in response.data or b'Logout' in response.data


def test_login_fail_wrong_password(client):
    client.post('/register', data={
        'username': 'testuser3',
        'email': 'test3@example.com',
        'password': 'rightpass',
        'password2': 'rightpass'
    }, follow_redirects=True)

    response = client.post('/login', data={
        'username': 'testuser3',
        'password': 'wrongpass'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Incorrect' in response.data or b'username' in response.data


def test_logout(client):
    client.post('/register', data={
        'username': 'testuser4',
        'email': 'test4@example.com',
        'password': 'mypassword',
        'password2': 'mypassword'
    }, follow_redirects=True)

    client.post('/login', data={
        'username': 'testuser4',
        'password': 'mypassword'
    }, follow_redirects=True)

    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'logged out' in response.data or b'Logout' not in response.data
