from flask import Flask
import random

app = Flask(__name__)
app.config["SECRET_KEY"] = "insert really secure secret key here"

from app import routes

if __name__ == '__main__':
    app.run()
