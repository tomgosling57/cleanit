# app_factory.py
import os
import secrets
from flask import Flask, redirect, url_for, request, Response, abort
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from config import Config, TestConfig
from database import init_db, get_db, teardown_db
from routes.users import user_bp
from routes.jobs import job_bp
from routes.teams import teams_bp
from routes.properties import properties_bp
from routes.storage import storage_bp
from services.user_service import UserService
from utils.populate_database import populate_database
from utils.svg_helper import load_svg_icons

def create_app(login_manager=LoginManager(), config_override=dict()):
    """
    Creates and configures the Flask application.

    Args:
        login_manager (LoginManager, optional): The Flask-Login manager instance.
                                               Defaults to a new LoginManager().
        test_config (dict, optional): A dictionary of configuration overrides for testing.
                                      Defaults to None.

    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__, instance_relative_config=True)
    if config_override.get('TESTING', False):
        app.config.from_object(TestConfig)
        populate_database(app.config['SQLALCHEMY_DATABASE_URI'])
    else:
        app.config.from_object(Config)
        if not app.config.get('SECRET_KEY'):
            abort(500, "SECRET_KEY is not set. Please set the SECRET_KEY environment variable for production.")
    
    if app.config.get('TESTING', False):
        import logging
        import sys
        app.logger.setLevel(logging.DEBUG)
        # Remove existing handlers to prevent duplicate logs in tests
        for handler in list(app.logger.handlers):
            app.logger.removeHandler(handler)
        # Add a StreamHandler to direct logs to stderr, which pytest captures
        handler = logging.StreamHandler(sys.stderr)
        handler.setLevel(logging.DEBUG)
        app.logger.addHandler(handler)
        app.logger.propagate = True

    app.config.update(config_override)

    # Initialize CSRF protection, the token will be available in jinja templates via {{ csrf_token() }}
    csrf = CSRFProtect(app)
    Session = init_db(app.config['SQLALCHEMY_DATABASE_URI'])
    app.config['SQLALCHEMY_SESSION'] = Session

    # Initialize Libcloud storage driver
    from libcloud.storage.types import Provider
    from libcloud.storage.providers import get_driver
    import os
    import tempfile

    storage_provider = app.config.get('STORAGE_PROVIDER', 's3')

    if storage_provider == 's3':
        # Production: S3 Storage
        cls = get_driver(Provider.S3)
        driver = cls(
            app.config.get('AWS_ACCESS_KEY_ID'),
            app.config.get('AWS_SECRET_ACCESS_KEY'),
            region=app.config.get('AWS_REGION', 'us-east-1')
        )
        container = driver.get_container(app.config.get('S3_BUCKET'))
        app.logger.info(f"Using S3 storage with bucket: {app.config.get('S3_BUCKET')}")
    
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
        if request.headers.get('HX-Request') == 'true':
            response = Response("Unauthorized", 401)
            response.headers['HX-Redirect'] = url_for('user.login')
            return response
        elif request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return Response("Unauthorized", 401)
        elif request.endpoint == 'job.update_job_status':
            return Response("Unauthorized", 401)
        else:
            return redirect(url_for('user.login'))
    
    @app.route('/')
    def index():
        return redirect(url_for('user.login'))
    
    app.register_blueprint(user_bp)
    app.register_blueprint(job_bp)
    app.register_blueprint(teams_bp)
    app.register_blueprint(properties_bp)
    app.register_blueprint(storage_bp)

    with app.app_context():
        load_svg_icons(app)
    
    return app

