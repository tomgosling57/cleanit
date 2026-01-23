from flask import Blueprint, current_app
from utils.populate_database import populate_database
testing_bp = Blueprint('testing', __name__, url_prefix='/testing')


@testing_bp.route('/reseed-database', methods=['GET'])
def reseed_database():
    """Deletes all data in the database and reseeds it with deterministic test data"""
    populate_database(current_app.config['SQLALCHEMY_DATABASE_URI'])
    return "Database reseeded", 200