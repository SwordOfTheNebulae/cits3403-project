# tests/test_routes.py
from app.create_app import create_app

def test_login_route():
    app = create_app()
    client = app.test_client()
    response = client.get('/login')
    assert response.status_code in [200, 302]  
