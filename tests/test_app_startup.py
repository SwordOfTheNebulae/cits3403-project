# tests/test_app_startup.py
from app.create_app import create_app

def test_app_creation():
    app = create_app()
    assert app is not None
    assert app.config['TESTING'] is not True 
