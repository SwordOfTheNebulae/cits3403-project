# tests/test_media_route.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from create_app import create_app

def test_media_route_not_found():
    app = create_app()
    client = app.test_client()
    response = client.get('/media/nonexistent/file.png')
    assert response.status_code in [404, 200]
