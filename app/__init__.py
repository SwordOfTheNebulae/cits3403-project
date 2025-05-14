from flask import Flask
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

app = Flask(__name__)
app.config["SECRET_KEY"] = "insert really secure secret key here" # key for anti-CSRF
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(os.path.abspath(os.path.dirname(__file__)), "app.db")
db = SQLAlchemy(app)
mirgrate = Migrate(app, db, render_as_batch=True)
login = LoginManager(app)
login.login_view = "login" # flask will redirect users to the login page if they aren't logged when they try to access a page that requires authentication

from app import routes, models

if __name__ == '__main__':
    app.run()
