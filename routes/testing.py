from flask import Blueprint, jsonify, current_app
from utils.populate_database import populate_database
from utils.timezone import utc_now, get_app_timezone, get_timezone_offset, is_valid_timezone
import os
import datetime
import platform
import time
testing_bp = Blueprint('testing', __name__, url_prefix='/testing')


@testing_bp.route('/reseed-database', methods=['GET'])
def reseed_database():
    """Deletes all data in the database and reseeds it with deterministic test data"""
    populate_database(os.environ['DATABASE_URL'])
    return "Database reseeded", 200


@testing_bp.route('/timezone/check', methods=['GET'])
def check_timezone():
    """
    Check application timezone configuration and system time.
    
    Returns information about:
    - Configured application timezone
    - Current UTC time
    - Current application timezone time
    - System timezone information
    - Timezone validation status
    """
    try:
        # Get application timezone
        app_tz_name = current_app.config.get('APP_TIMEZONE', 'UTC')
        app_tz_valid = is_valid_timezone(app_tz_name)
        
        # Get current times
        utc_current = utc_now()
        app_tz = get_app_timezone() if app_tz_valid else None
        app_current = utc_current.astimezone(app_tz) if app_tz else None
        
        # Get system timezone information
        system_timezone = None
        try:
            if platform.system() == 'Linux':
                # Try to read system timezone on Linux
                if os.path.exists('/etc/timezone'):
                    with open('/etc/timezone', 'r') as f:
                        system_timezone = f.read().strip()
                elif os.path.exists('/etc/localtime'):
                    # Try to resolve symlink
                    import os.path
                    localtime_path = os.path.realpath('/etc/localtime')
                    if 'zoneinfo' in localtime_path:
                        system_timezone = localtime_path.split('zoneinfo/')[-1]
        except Exception:
            pass
        
        # Get system time
        system_time = datetime.datetime.now()
        system_utc_time = datetime.datetime.utcnow()
        
        response = {
            'application': {
                'timezone': app_tz_name,
                'timezone_valid': app_tz_valid,
                'utc_offset': str(get_timezone_offset(app_tz_name)) if app_tz_valid else None,
                'current_utc': utc_current.isoformat(),
                'current_app_tz': app_current.isoformat() if app_current else None,
            },
            'system': {
                'platform': platform.system(),
                'platform_release': platform.release(),
                'system_timezone': system_timezone,
                'system_local_time': system_time.isoformat(),
                'system_utc_time': system_utc_time.isoformat(),
            },
            'validation': {
                'app_tz_configured': bool(app_tz_name),
                'app_tz_valid': app_tz_valid,
                'utc_consistent': True,  # We always use UTC internally
            },
            'timestamp': utc_current.isoformat(),
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'timestamp': datetime.datetime.utcnow().isoformat()
        }), 500


@testing_bp.route('/timezone/validate', methods=['GET'])
def validate_timezone():
    """
    Validate that the application timezone is properly configured.
    
    This endpoint is designed to be used in test pre-run sanity checks
    to ensure the environment is correctly configured.
    """
    try:
        # Get application timezone
        app_tz_name = current_app.config.get('APP_TIMEZONE', 'UTC')
        
        # Basic validation
        errors = []
        warnings = []
        
        # Check if timezone is set
        if not app_tz_name:
            errors.append('APP_TIMEZONE environment variable is not set')
        elif app_tz_name == 'UTC':
            warnings.append('APP_TIMEZONE is set to UTC (default) - consider setting a specific timezone for your region')
        
        # Check if timezone is valid
        if not is_valid_timezone(app_tz_name):
            errors.append(f'APP_TIMEZONE "{app_tz_name}" is not a valid IANA timezone identifier')
        
        # Check if we're in testing environment
        flask_env = os.environ.get('FLASK_ENV', 'production')
        if flask_env == 'testing':
            # In testing, we should have a specific timezone configured
            expected_tz = os.environ.get('EXPECTED_TEST_TIMEZONE', 'UTC')
            if app_tz_name != expected_tz:
                warnings.append(f'In testing environment, APP_TIMEZONE ({app_tz_name}) does not match EXPECTED_TEST_TIMEZONE ({expected_tz})')
        
        # Get current times for comparison
        utc_current = utc_now()
        system_utc = datetime.datetime.utcnow()
        
        # Check if system UTC time is close to our UTC time (within 5 seconds)
        time_diff = abs((utc_current - system_utc).total_seconds())
        if time_diff > 5:
            warnings.append(f'System UTC time differs from application UTC time by {time_diff:.1f} seconds')
        
        response = {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'timezone': app_tz_name,
            'flask_env': flask_env,
            'timestamp': utc_current.isoformat(),
        }
        
        status_code = 200 if len(errors) == 0 else 400
        return jsonify(response), status_code
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'valid': False,
            'timestamp': datetime.datetime.utcnow().isoformat()
        }), 500