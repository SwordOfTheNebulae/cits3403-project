# tests/test_database_admin.py
from app.create_app import create_app
from app.models.models import User

def test_admin_account_exists():
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        assert admin is not None
