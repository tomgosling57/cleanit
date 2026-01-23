# app_factory.py
import os
import secrets
from flask import Flask, redirect, url_for, request, Response, abort, jsonify
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from config import Config, TestConfig, DebugConfig
from database import init_db, get_db, teardown_db
from routes.users import user_bp
from routes.jobs import job_bp
from routes.teams import teams_bp
from routes.properties import properties_bp
from routes.media import media_bp
from services.user_service import UserService
from utils.populate_database import populate_database
from utils.svg_helper import load_svg_icons
from utils.error_handlers import register_media_error_handlers, register_general_error_handlers

def create_app(login_manager=LoginManager(), config_override=dict()):
    """
    Creates and configures the Flask application.

    Args:
        login_manager (LoginManager, optional): The Flask-Login manager instance.
                                               Defaults to a new LoginManager().
        config_override (dict, optional): A dictionary of configuration overrides.
                                          Defaults to empty dict.

    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__, instance_relative_config=True)
    
    # Determine which configuration to use based on FLASK_ENV 
    env = os.getenv('FLASK_ENV')
    if not env:
        raise ValueError("FLASK_ENV environment variable is not set. Please set it to 'production', 'debug', or 'testing' by running the set_env.py script.")
    
    if env == 'testing':
        # FLASK_ENV=testing (Docker deployment)
        # Database population is handled by Docker command to avoid race conditions with multiple workers
        app.config.from_object(TestConfig)
    elif env == 'debug':
        # FLASK_ENV=debug (Docker deployment)
        # Database population is handled by Docker command to avoid race conditions with multiple workers
        app.config.from_object(DebugConfig)
    else:
        # Default: production (FLASK_ENV=production or not set)
        app.config.from_object(Config)
        if not app.config.get('SECRET_KEY'):
            abort(500, "SECRET_KEY is not set. Please set the SECRET_KEY environment variable for production.")
    
    # Configure logging based on environment
    import logging
    import sys
    
    # Remove existing handlers to prevent duplicate logs
    for handler in list(app.logger.handlers):
        app.logger.removeHandler(handler)
    
    # Create a StreamHandler to direct logs to stderr
    handler = logging.StreamHandler(sys.stderr)
    
    # Check if we should enable debug logging
    # Debug logging should be enabled when:
    # 1. FLASK_ENV is 'debug' or 'testing'
    # 2. app.config['DEBUG'] is True
    # 3. app.config['TESTING'] is True
    enable_debug = (
        env == 'debug' or
        env == 'testing' or
        app.config.get('DEBUG', False) or
        app.config.get('TESTING', False)
    )
    if enable_debug:
        app.logger.setLevel(logging.DEBUG)
        handler.setLevel(logging.DEBUG)
        # Format for debug environment
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
    else:
        # Production environment - only show warnings and errors
        app.logger.setLevel(logging.WARNING)
        handler.setLevel(logging.WARNING)
        # Simpler format for production
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
    
    app.logger.addHandler(handler)
    app.logger.propagate = True
    
    # Also configure werkzeug logger for request logging
    werkzeug_logger = logging.getLogger('werkzeug')
    if enable_debug:
        werkzeug_logger.setLevel(logging.DEBUG)
        # Add handler to werkzeug logger too
        werkzeug_handler = logging.StreamHandler(sys.stderr)
        werkzeug_handler.setLevel(logging.DEBUG)
        werkzeug_handler.setFormatter(formatter)
        werkzeug_logger.addHandler(werkzeug_handler)
        app.logger.info(f"Debug logging enabled (FLASK_ENV={env}, DEBUG={app.config.get('DEBUG', False)}, TESTING={app.config.get('TESTING', False)})")
    else:
        werkzeug_logger.setLevel(logging.WARNING)

    app.config.update(config_override)

    # Initialize CSRF protection, the token will be available in jinja templates via {{ csrf_token() }}
    csrf = CSRFProtect(app)
    Session = init_db(app.config['SQLALCHEMY_DATABASE_URI'])
    app.config['SQLALCHEMY_SESSION'] = Session

    # Initialize Libcloud storage driver
    from libcloud.storage.types import Provider
    from libcloud.storage.providers import get_driver
    import tempfile

    storage_provider = app.config.get('STORAGE_PROVIDER', 's3')

    if storage_provider == 's3':
        # Production: S3 Storage
        cls = get_driver(Provider.S3)
        
        # Get custom endpoint for S3-compatible services like MinIO
        endpoint_url = app.config.get('S3_ENDPOINT_URL')
        use_https = app.config.get('S3_USE_HTTPS', 'true').lower() == 'true'
        verify_ssl = app.config.get('S3_VERIFY_SSL', 'true').lower() == 'true'
        
        # Prepare driver arguments
        driver_args = {
            'key': app.config.get('AWS_ACCESS_KEY_ID'),
            'secret': app.config.get('AWS_SECRET_ACCESS_KEY'),
            'region': app.config.get('AWS_REGION', 'us-east-1')
        }
        
        # Add host parameter if custom endpoint is provided
        if endpoint_url:
            # Parse the endpoint URL to extract host
            from urllib.parse import urlparse
            parsed = urlparse(endpoint_url)
            driver_args['host'] = parsed.hostname
            if parsed.port:
                driver_args['port'] = parsed.port
            driver_args['secure'] = use_https
        
        driver = cls(**driver_args)
        
        # For S3-compatible services, we might need to handle SSL verification
        if endpoint_url and not verify_ssl:
            import warnings
            import urllib3
            warnings.filterwarnings('ignore', message='Unverified HTTPS request')
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        container = driver.get_container(app.config.get('S3_BUCKET'))
        app.logger.info(f"Using S3 storage with bucket: {app.config.get('S3_BUCKET')}")
        if endpoint_url:
            app.logger.info(f"Using custom endpoint: {endpoint_url}")
    
    elif storage_provider == 'temp':
        # Testing: Temporary storage (auto-cleaned)
        import tempfile
        upload_dir = app.config.get('UPLOAD_FOLDER')
        if not upload_dir or upload_dir == './uploads':
            # Create a temporary directory that will be cleaned up
            upload_dir = tempfile.mkdtemp(prefix='temp_uploads_')
            app.config['UPLOAD_FOLDER'] = upload_dir
            app.logger.info(f"Created temporary upload directory: {upload_dir}")
        
        # IMPORTANT: Create directory if it doesn't exist
        os.makedirs(upload_dir, exist_ok=True)

        cls = get_driver(Provider.LOCAL)
        driver = cls(upload_dir)
        container = driver.get_container('') # Use an empty string for the container name, making upload_dir the container
        app.logger.info(f"Using temporary storage at: {upload_dir}")
    
    else:
        # Development: Local Filesystem (explicit 'local' provider)
        upload_dir = app.config.get('UPLOAD_FOLDER', './uploads')

        # IMPORTANT: Create directory if it doesn't exist
        os.makedirs(upload_dir, exist_ok=True)

        cls = get_driver(Provider.LOCAL)
        driver = cls(upload_dir)
        container = driver.get_container('') # Use an empty string for the container name, making upload_dir the container
        app.logger.info(f"Using local storage at: {upload_dir}")

    app.config['STORAGE_DRIVER'] = driver
    app.config['STORAGE_CONTAINER'] = container
    
    login_manager.login_view = 'user.login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        _return = UserService(get_db()).get_user_by_id(user_id)
        teardown_db()
        return _return
    
    @login_manager.unauthorized_handler
    def unauthorized():
        # Check for HTMX requests first (they need special handling)
        if request.headers.get('HX-Request') == 'true':
            response = Response("Unauthorized", 401)
            response.headers['HX-Redirect'] = url_for('user.login')
            return response
        # Check for AJAX requests
        elif request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return Response("Unauthorized", 401)
        # Check for specific endpoints that need special handling
        elif request.endpoint == 'job.update_job_status':
            return Response("Unauthorized", 401)
        # Check if client prefers JSON over HTML
        elif request.accept_mimetypes.best == 'application/json':
            return jsonify({"error": "Unauthorized"}), 401
        # Default: redirect to login page
        else:
            return redirect(url_for('user.login'))
    
    @app.route('/')
    def index():
        return redirect(url_for('user.login'))
    
    @app.route('/health')
    def health():
        return jsonify({"status": "healthy"}), 200
    
    app.register_blueprint(user_bp)
    app.register_blueprint(job_bp)
    app.register_blueprint(teams_bp)
    app.register_blueprint(properties_bp)
    app.register_blueprint(media_bp)
    if env == 'testing':
        app.logger.info("Registering testing blueprint (FLASK_ENV=testing)")
        # Register testing blueprint only in testing environment
        from routes.testing import testing_bp
        app.register_blueprint(testing_bp)

    # Register global error handlers
    register_media_error_handlers(app)
    register_general_error_handlers(app, login_manager)

    with app.app_context():
        load_svg_icons(app)
    
    return app
