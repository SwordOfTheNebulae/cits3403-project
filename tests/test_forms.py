from utils.forms import LoginForm, RegisterForm, CommentForm, RateForm
from werkzeug.datastructures import MultiDict
from create_app import create_app

app = create_app()

def test_login_form_valid():
    with app.test_request_context():
        form = LoginForm(formdata=MultiDict({
            'username': 'testuser',
            'password': '123456'
        }), meta={'csrf': False})  # 禁用 CSRF
        assert form.validate() is True

def test_login_form_missing_username():
    with app.test_request_context():
        form = LoginForm(formdata=MultiDict({
            'username': '',
            'password': '123456'
        }))
        assert not form.validate()
        assert 'Please enter your username' in form.username.errors[0]

def test_register_form_password_mismatch():
    with app.test_request_context():
        form = RegisterForm(formdata=MultiDict({
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'abc123',
            'password2': 'def456'
        }))
        assert not form.validate()
        assert 'Passwords must match' in form.password2.errors[0]

def test_register_form_invalid_email():
    with app.test_request_context():
        form = RegisterForm(formdata=MultiDict({
            'username': 'testuser',
            'email': 'not-an-email',
            'password': 'abc123',
            'password2': 'abc123'
        }))
        assert not form.validate()
        assert 'Invalid email format' in form.email.errors[0]

def test_comment_form_too_long():
    with app.test_request_context():
        content = 'a' * 300
        form = CommentForm(formdata=MultiDict({
            'content': content
        }), meta={'csrf': False})
        assert not form.validate()
        assert 'Field cannot be longer than 255 characters.' in form.content.errors[0]

def test_rate_form_invalid_value():
    with app.test_request_context():
        form = RateForm(formdata=MultiDict({
            'mark': ''
        }))
        assert not form.validate()
        assert 'Please enter your rating' in form.mark.errors[0]
