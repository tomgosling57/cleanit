import secrets
import os

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
    STORAGE_PROVIDER = os.getenv('STORAGE_PROVIDER', 'local')
    S3_BUCKET = os.getenv('S3_BUCKET', 'your-bucket-name')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', 'your-access-key')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', 'your-secret-key')
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './uploads')

class TestConfig(Config):
    TESTING = True
    STORAGE_PROVIDER = 'local'
    UPLOAD_FOLDER = './uploads'