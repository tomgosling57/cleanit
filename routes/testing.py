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

@testing_bp.route('/property/<int:property_id>/jobs/filtered', methods=['GET'])
@login_required
def test_filtered_property_jobs(property_id):
    """Test endpoint to verify filtered jobs logic for a property.
    
    This endpoint is used in integration tests to validate that the filtering logic
    for property jobs is working correctly based on date range and other filters.
    
    Query Parameters:
    - start_date: ISO format date string to filter jobs starting from this date
    - end_date: ISO format date string to filter jobs up to this date
    - show_past: Boolean flag to show past jobs (default: false)
    - show_completed: Boolean flag to show completed jobs (default: true)
    
    Returns:
    JSON response containing the filtered list of jobs."""
    controller = get_property_controller()
    jobs = controller._get_filtered_property_jobs(property_id)
    print(f"Filtered {len(jobs)} jobs for property {property_id}: {[job.to_dict() for job in jobs]}")  # Debug print
    return jsonify({
        'jobs': [job.to_dict() for job in jobs],
    })