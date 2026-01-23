import secrets
import os
import tempfile

DATETIME_FORMATS = {
    "DATE_FORMAT": "%d-%m-%Y",
    "DATE_FORMAT_FLATPICKR": "d-m-Y",
    "DATETIME_FORMAT": "%d-%m-%Y %H:%M",
    "DATETIME_FORMAT_FLATPICKR": "d-m-Y H:i",
    "DATETIME_FORMAT_JOBS_JS": "j F Y, H:i",
    "DATETIME_FORMAT_JOBS_PY": "%d %B %Y, %H:%M",
    "TIME_FORMAT": "%H:%M",
    "TIME_FORMAT_FLATPICKR": "H:i"
}

class Config:
    """
    Base configuration class for CleanIt application.
    
    The FLASK_ENV environment variable determines which configuration is used:
    - 'production': Default configuration (this class)
    - 'debug': Debug configuration with auto-reloading and debug features
    - 'testing': Testing configuration that seeds the database after each test
    
    Environment variable FLASK_ENV must be one of: production, debug, testing
    """
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_bytes(32)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{os.path.join("instance", "cleanit.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Cloud-first storage configuration
    STORAGE_PROVIDER = os.getenv('STORAGE_PROVIDER', 's3')  # Default to S3 for production
    S3_BUCKET = os.getenv('S3_BUCKET', 'your-bucket-name')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', 'your-access-key')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', 'your-secret-key')
    
    # S3-compatible service configuration (for MinIO, etc.)
    S3_ENDPOINT_URL = os.getenv('S3_ENDPOINT_URL')
    S3_USE_HTTPS = os.getenv('S3_USE_HTTPS', 'true')
    S3_VERIFY_SSL = os.getenv('S3_VERIFY_SSL', 'true')
    
    # For development/testing with local and temporary storage
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './uploads')
    
    # Environment detection - used to determine runtime configuration
    # Valid values: 'production', 'debug', 'testing'
    ENV = os.getenv('FLASK_ENV', 'production')

class DebugConfig(Config):
    """
    Debug configuration for development.
    
    Enabled when FLASK_ENV=debug. Features include:
    - Auto-reloading on code changes
    - Debug mode enabled
    - Detailed error pages with stack traces
    - Local storage for easier development
    """
    DEBUG = True
    # Use local storage for development by default
    STORAGE_PROVIDER = os.getenv('STORAGE_PROVIDER', 's3')
    # Ensure upload folder exists for local storage
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './uploads')

class TestConfig(Config):
    """
    Testing configuration for automated tests.
    
    Enabled when FLASK_ENV=testing
    Features include:
    - Temporary storage that auto-cleans after tests
    - Testing mode enabled
    - Isolated database for test data
    """
    TESTING = True
    UPLOAD_FOLDER = tempfile.mkdtemp(prefix='test_uploads_')  # Temporary directory for tests
