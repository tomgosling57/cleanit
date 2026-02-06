from flask import Blueprint, jsonify, current_app, request
from flask_login import login_required
from utils.populate_database import insert_dummy_data
from utils.timezone import (
    utc_now, get_app_timezone, get_timezone_offset, is_valid_timezone,
    compare_times, compare_timezones, compare_environment_times
)
from database import get_db
from routes.properties import get_property_controller
testing_bp = Blueprint('testing', __name__, url_prefix='/testing')


@testing_bp.route('/reseed-database', methods=['GET'])
def reseed_database():
    """Deletes all data in the database and reseeds it with deterministic test data"""
    insert_dummy_data(existing_session=get_db())
    return "Database reseeded", 200


@testing_bp.route('/timezone', methods=['GET'])
def timezone_system():
    system_tz = get_app_timezone().key

    return jsonify({
        'system_timezone': system_tz,
        'current_time_utc': utc_now().isoformat(),
        'APP_TIMEZONE': current_app.config['APP_TIMEZONE'],
    })