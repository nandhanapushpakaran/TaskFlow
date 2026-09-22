"""
Application factory for TaskFlow.
Initializes extensions, registers blueprints, serves frontend files, and sets up security headers.
"""
import os
import logging
from flask import Flask, jsonify, request, send_from_directory, redirect
from flask_login import LoginManager, current_user
from dotenv import load_dotenv

from backend.models import db, User

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login user loader callback."""
    try:
        return db.session.get(User, int(user_id))
    except Exception:
        return None


@login_manager.unauthorized_handler
def handle_unauthorized():
    """Return JSON 401 for API routes, redirect to login page for browser navigation."""
    if request.path.startswith('/api/'):
        return jsonify({
            'error': 'unauthorized',
            'message': 'Your session has expired or you are not logged in. Please log in again.'
        }), 401
    return redirect('/login.html')


def create_app(test_config=None):
    """Create and configure the TaskFlow Flask application."""
    load_dotenv()

    # Determine base directory
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    frontend_dir = os.path.join(base_dir, 'frontend')
    instance_dir = os.path.join(base_dir, 'instance')
    os.makedirs(instance_dir, exist_ok=True)

    app = Flask(
        __name__,
        instance_path=instance_dir,
        static_folder=frontend_dir,
        static_url_path=''
    )

    # Default configuration
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'tf-dev-insecure-key-replace-in-production-12345'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(instance_dir, "task_manager.db")}'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1')
    )

    if test_config is not None:
        app.config.update(test_config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register blueprints
    from backend.auth import auth_bp
    from backend.tasks import tasks_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)

    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'ok',
            'message': 'TaskFlow API is healthy and operational.'
        }), 200

    # Frontend Page Routes
    @app.route('/')
    @app.route('/index.html')
    def index():
        if not current_user.is_authenticated:
            return redirect('/login.html')
        return send_from_directory(frontend_dir, 'index.html')

    @app.route('/login.html')
    def login_page():
        if current_user.is_authenticated:
            return redirect('/')
        return send_from_directory(frontend_dir, 'login.html')

    @app.route('/register.html')
    def register_page():
        if current_user.is_authenticated:
            return redirect('/')
        return send_from_directory(frontend_dir, 'register.html')

    # Static assets fallback routes
    @app.route('/css/<path:filename>')
    def serve_css(filename):
        return send_from_directory(os.path.join(frontend_dir, 'css'), filename)

    @app.route('/js/<path:filename>')
    def serve_js(filename):
        return send_from_directory(os.path.join(frontend_dir, 'js'), filename)

    # Custom Error Handlers
    @app.errorhandler(404)
    def handle_404(e):
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'not_found',
                'message': 'The requested API resource was not found.'
            }), 404
        return redirect('/')

    @app.errorhandler(500)
    def handle_500(e):
        logger.error(f"Unhandled server exception: {str(e)}", exc_info=True)
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'server_error',
                'message': 'An unexpected server error occurred. Please try again later.'
            }), 500
        return jsonify({
            'error': 'server_error',
            'message': 'An unexpected server error occurred.'
        }), 500

    # Security headers on all responses
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        return response

    # Create tables automatically for local run
    with app.app_context():
        db.create_all()

    return app
