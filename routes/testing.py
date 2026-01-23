from flask import Blueprint
from utils.populate_database import populate_database
import os
testing_bp = Blueprint('testing', __name__, url_prefix='/testing')


@testing_bp.route('/reseed-database', methods=['GET'])
def reseed_database():
    """Deletes all data in the database and reseeds it with deterministic test data"""
    populate_database(os.environ['DATABASE_URL'])
    return "Database reseeded", 200