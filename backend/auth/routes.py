"""
Authentication endpoints for TaskFlow.
Handles registration, login, logout, and current user retrieval.
"""
from flask import request, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from backend.models import db, User
from backend.utils import validate_registration_data, validation_error_response
from . import auth_bp


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user, hash password, and automatically log in."""
    data = request.get_json(silent=True)
    is_valid, errors, cleaned = validate_registration_data(data)

    if not is_valid:
        return validation_error_response(errors)

    # Check for existing email (case-insensitive check)
    existing_user = User.query.filter_by(email=cleaned['email']).first()
    if existing_user:
        return validation_error_response({'email': 'An account with this email address already exists.'})

    # Create new user
    user = User(
        name=cleaned['name'],
        email=cleaned['email']
    )
    user.set_password(cleaned['password'])

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return jsonify({
            'error': 'server_error',
            'message': 'Failed to create user account. Please try again.'
        }), 500

    # Automatically log the newly registered user in
    login_user(user, remember=True)

    return jsonify({
        'message': 'Account created successfully!',
        'user': user.to_dict()
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate an existing user and create a session."""
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({
            'error': 'validation_error',
            'message': 'Please provide email and password.'
        }), 400

    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not email or not password:
        return jsonify({
            'error': 'auth_error',
            'message': 'Both email and password are required.'
        }), 400

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({
            'error': 'auth_error',
            'message': 'Invalid email or password. Please try again.'
        }), 401

    login_user(user, remember=True)

    return jsonify({
        'message': 'Logged in successfully!',
        'user': user.to_dict()
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """End the current user's session."""
    logout_user()
    return jsonify({
        'message': 'Logged out successfully.'
    }), 200


@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Return the authenticated user or 401 if unauthenticated."""
    if not current_user.is_authenticated:
        return jsonify({
            'error': 'unauthorized',
            'message': 'Authentication required. Please log in.'
        }), 401

    return jsonify({
        'user': current_user.to_dict()
    }), 200
