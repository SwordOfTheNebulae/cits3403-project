# tests/test_app_startup.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from create_app import create_app

def test_app_creation():
    app = create_app()
    assert app is not None
    assert app.config['TESTING'] is not True 
