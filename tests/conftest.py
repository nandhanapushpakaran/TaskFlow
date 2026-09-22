"""
Pytest configuration and fixtures for TaskFlow.
Sets up an isolated in-memory SQLite database and test clients.
"""
import os
import sys
import pytest

# Ensure repository root is on Python sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.pool import StaticPool

from backend import create_app
from backend.models import db, User, Task



@pytest.fixture
def app():
    """Create and configure a clean app instance for each test."""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite://',
        'SQLALCHEMY_ENGINE_OPTIONS': {
            'poolclass': StaticPool,
            'connect_args': {'check_same_thread': False},
        },
        'SECRET_KEY': 'pytest-super-secret-key-12345',
        'SESSION_COOKIE_SECURE': False,
    })

    with app.app_context():
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def user_a(app):
    """Create User A in the database."""
    with app.app_context():
        user = User(name="User Alice", email="alice@example.com")
        user.set_password("SecurePass123!")
        db.session.add(user)
        db.session.commit()
        return User.query.filter_by(email="alice@example.com").first()


@pytest.fixture
def user_b(app):
    """Create User B in the database."""
    with app.app_context():
        user = User(name="User Bob", email="bob@example.com")
        user.set_password("PasswordBob456!")
        db.session.add(user)
        db.session.commit()
        return User.query.filter_by(email="bob@example.com").first()


@pytest.fixture
def auth_client_a(app, user_a):
    """Client authenticated as User Alice."""
    client = app.test_client()
    client.post('/api/auth/login', json={
        'email': 'alice@example.com',
        'password': 'SecurePass123!'
    })
    return client


@pytest.fixture
def auth_client_b(app, user_b):
    """Client authenticated as User Bob."""
    client = app.test_client()
    client.post('/api/auth/login', json={
        'email': 'bob@example.com',
        'password': 'PasswordBob456!'
    })
    return client
