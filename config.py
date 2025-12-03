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
BACK_TO_BACK_THRESHOLD = 15 # MINUTES

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_bytes(32)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{os.path.join("instance", "cleanit.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SEED_DATABASE_FOR_TESTING = False
    INSERT_DUMMY_DATA = False

class TestConfig(Config):
    TESTING = True
    SEED_DATABASE_FOR_TESTING = True
    INSERT_DUMMY_DATA = True