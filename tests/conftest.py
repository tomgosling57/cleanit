import pytest
from flask import Flask
from unittest.mock import MagicMock

@pytest.fixture
def app_context():
    app = Flask(__name__)
    with app.app_context():
        yield

@pytest.fixture
def client():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_SESSION'] = MagicMock() # Mock the SQLAlchemy session
    from routes.users import user_bp
    app.register_blueprint(user_bp)
    with app.test_client() as client:
        yield client