"""
Authentication test suite for TaskFlow.
Tests registration, login, session persistence, logout, input validation, and password security.
"""
import pytest
from backend.models import User


def test_registration_success(client, app):
    """Registering with valid data succeeds and logs user in automatically."""
    response = client.post('/api/auth/register', json={
        'name': 'Jane Doe',
        'email': 'Jane.Doe@example.com',
        'password': 'SecurePassword123',
        'confirm_password': 'SecurePassword123'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['message'] == 'Account created successfully!'
    assert data['user']['name'] == 'Jane Doe'
    assert data['user']['email'] == 'jane.doe@example.com'
    assert 'password' not in data['user']
    assert 'password_hash' not in data['user']

    # Verify user can access authenticated /me endpoint immediately
    me_resp = client.get('/api/auth/me')
    assert me_resp.status_code == 200
    assert me_resp.get_json()['user']['email'] == 'jane.doe@example.com'


def test_registration_duplicate_email_fails(client):
    """Registration with duplicate email fails with validation error."""
    payload = {
        'name': 'Original User',
        'email': 'duplicate@example.com',
        'password': 'Password123!',
        'confirm_password': 'Password123!'
    }
    first_resp = client.post('/api/auth/register', json=payload)
    assert first_resp.status_code == 201

    # Second attempt with same email in different case
    dup_payload = {
        'name': 'Duplicate User',
        'email': 'DUPLICATE@example.com',
        'password': 'Password123!',
        'confirm_password': 'Password123!'
    }
    dup_resp = client.post('/api/auth/register', json=dup_payload)
    assert dup_resp.status_code == 400
    data = dup_resp.get_json()
    assert data['error'] == 'validation_error'
    assert 'email' in data['fields']


def test_registration_validation_failures(client):
    """Registration fails with appropriate validation messages for invalid inputs."""
    # Short password
    res = client.post('/api/auth/register', json={
        'name': 'Valid Name',
        'email': 'valid@example.com',
        'password': 'short',
        'confirm_password': 'short'
    })
    assert res.status_code == 400
    assert 'password' in res.get_json()['fields']

    # Invalid email
    res = client.post('/api/auth/register', json={
        'name': 'Valid Name',
        'email': 'not-an-email',
        'password': 'validpassword123',
        'confirm_password': 'validpassword123'
    })
    assert res.status_code == 400
    assert 'email' in res.get_json()['fields']

    # Password mismatch
    res = client.post('/api/auth/register', json={
        'name': 'Valid Name',
        'email': 'valid@example.com',
        'password': 'validpassword123',
        'confirm_password': 'differentpassword123'
    })
    assert res.status_code == 400
    assert 'confirm_password' in res.get_json()['fields']

    # Name too short
    res = client.post('/api/auth/register', json={
        'name': 'A',
        'email': 'valid@example.com',
        'password': 'validpassword123',
        'confirm_password': 'validpassword123'
    })
    assert res.status_code == 400
    assert 'name' in res.get_json()['fields']


def test_password_is_hashed(app):
    """Verify password is never stored as plaintext in the database."""
    with app.app_context():
        user = User(name="Test User", email="hashed@example.com")
        user.set_password("MySecretPassword999!")
        assert user.password_hash != "MySecretPassword999!"
        assert user.check_password("MySecretPassword999!") is True
        assert user.check_password("WrongPassword") is False
        assert "password_hash" not in user.to_dict()


def test_login_success(client, user_a):
    """User can log in with correct credentials."""
    res = client.post('/api/auth/login', json={
        'email': 'alice@example.com',
        'password': 'SecurePass123!'
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['user']['email'] == 'alice@example.com'

    # Check authenticated session
    me_resp = client.get('/api/auth/me')
    assert me_resp.status_code == 200
    assert me_resp.get_json()['user']['id'] == user_a.id


def test_login_invalid_credentials_fail(client, user_a):
    """Login with wrong password fails with friendly error message."""
    res = client.post('/api/auth/login', json={
        'email': 'alice@example.com',
        'password': 'IncorrectPassword!'
    })
    assert res.status_code == 401
    data = res.get_json()
    assert data['error'] == 'auth_error'
    assert "Invalid email or password" in data['message']


def test_logout(auth_client_a):
    """Logging out destroys the session."""
    logout_res = auth_client_a.post('/api/auth/logout')
    assert logout_res.status_code == 200

    # User is no longer authenticated
    me_res = auth_client_a.get('/api/auth/me')
    assert me_res.status_code == 401


def test_unauthenticated_api_is_rejected(client):
    """Unauthenticated access to protected routes returns 401 JSON."""
    res = client.get('/api/tasks')
    assert res.status_code == 401
    assert res.is_json
    assert res.get_json()['error'] == 'unauthorized'
