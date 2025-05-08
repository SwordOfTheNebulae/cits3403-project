from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app import db
from app.models import User
import sqlalchemy as sql

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')
    
class CreateAccountForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo("password")])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Create Account')
    
    def validate_username(self, username):
        user = db.session.scalar(sql.select(User).where(User.username == username.data))
        if user is not None:
            raise ValidationError('Username already in use')

    def validate_email(self, email):
        user = db.session.scalar(sql.select(User).where(User.email == email.data))
        if user is not None:
            raise ValidationError('Email address already in use')