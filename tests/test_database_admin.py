# tests/test_database_admin.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from create_app import create_app
from models.models import User

def test_admin_account_exists():
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        assert admin is not None
