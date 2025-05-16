# tests/test_routes.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.create_app import create_app

def test_login_route():
    app = create_app()
    client = app.test_client()
    response = client.get('/login')
    assert response.status_code in [200, 302]  
