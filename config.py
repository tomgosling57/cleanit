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
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_bytes(32)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{os.path.join("instance", "cleanit.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Cloud-first storage configuration
    STORAGE_PROVIDER = os.getenv('STORAGE_PROVIDER', 's3')  # Default to S3 for production
    S3_BUCKET = os.getenv('S3_BUCKET', 'your-bucket-name')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', 'your-access-key')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', 'your-secret-key')
    
    # For development/testing with local storage
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './uploads')
    
    # Environment detection
    ENV = os.getenv('FLASK_ENV', 'production')

class TestConfig(Config):
    TESTING = True
    STORAGE_PROVIDER = 'temp'  # Use temporary storage for tests
    UPLOAD_FOLDER = tempfile.mkdtemp(prefix='test_uploads_')  # Temporary directory for tests