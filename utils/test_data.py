"""
Test data constants for the CleanIt application.

This module contains all the test data constants used for populating the database
and for testing purposes. This allows tests to access the data without importing
the entire populate_database utility.
"""

from datetime import datetime, time, timedelta, date
from utils.timezone import get_app_timezone, today_in_app_tz, from_app_tz, to_app_tz

USER_DATA = {
    'admin': {
        'id': 1,
        'first_name': 'Ruby',
        'last_name': 'Redmond',
        'email': 'admin@example.com',
        'phone': '12345678',
        'role': 'admin',
        'password': 'admin_password'
    },
    'supervisor': {
        'id': 2,
        'first_name': 'Damo',
        'last_name': 'Brown',
        'email': 'supervisor@example.com',
        'role': 'supervisor',
        'password': 'supervisor_password'
    },
    'user': {
        'id': 3,
        'first_name': 'Manchan',
        'last_name': 'Fionn',
        'email': 'user@example.com',
        'role': 'user',
        'password': 'user_password'
    },
    'team_leader': {
        'id': 4,
        'first_name': 'Alice',
        'last_name': 'Smith',
        'email': 'teamleader@example.com',
        'role': 'user',
        'password': 'team_leader_password'
    }
}

# Property definitions
PROPERTY_DATA = {
    'anytown_property': {
        'id': 1,
        'address': '123 Main St, Anytown',
        'access_notes': 'Key under mat'
    },
    'teamville_property': {
        'id': 2,
        'address': '456 Oak Ave, Teamville',
        'access_notes': 'Code 1234'
    }
}

# Team definitions
TEAM_DATA = {
    'initial_team': {
        'id': 1,
        'name': 'Initial Team',
        'team_leader_key': 'admin',
        'members': ['admin', 'user']
    },
    'alpha_team': {
        'id': 2,
        'name': 'Alpha Team',
        'team_leader_key': 'supervisor',
        'members': ['supervisor']
    },
    'beta_team': {
        'id': 3,
        'name': 'Beta Team',
        'team_leader_key': 'team_leader',
        'members': ['team_leader']
    },
    'charlie_team': {
        'id': 4,
        'name': 'Charlie Team',
        'team_leader_key': None
    },
    'delta_team': {
        'id': 5,
        'name': 'Delta Team',
        'team_leader_key': None
    }
}

# Job definitions
# Note: These are template definitions that need to be processed with date calculations
JOB_TEMPLATES = [
    # Initial Team jobs
    {
        'id': 1,
        'date_offset': 0,  # today
        'start_time': (9, 0),
        'end_time': (11, 0),
        'description': 'Full house clean, focus on kitchen and bathrooms.',
        'property_key': 'anytown_property',
        'team_key': 'initial_team',
        'user_key': 'admin',
        'arrival_date_offset': 2,
        'complete': False
    },
    {
        'id': 2,
        'date_offset': 0,
        'start_time': (12, 0),
        'end_time': (14, 0),
        'description': '',
        'property_key': 'anytown_property',
        'team_key': 'initial_team',
        'user_key': None,
        'arrival_date_offset': 1,
        'complete': False
    },
    # Future Jobs
    {
        'id': 3,
        'date_offset': 1,
        'start_time': (14, 0),
        'end_time': (16, 0),
        'description': '',
        'property_key': 'anytown_property',
        'team_key': 'initial_team',
        'user_key': None,
        'arrival_date_offset': 0,
        'complete': False
    },
    {
        'id': 12,
        'date_offset': 1,
        'start_time': (10, 0),
        'end_time': (12, 0),
        'description': 'Future job: Deep clean carpets.',
        'property_key': 'anytown_property',
        'team_key': 'initial_team',
        'user_key': None,
        'arrival_date_offset': 0,
        'complete': False
    },
    {
        'id': 13,
        'date_offset': 5,
        'start_time': (13, 0),
        'end_time': (15, 0),
        'description': 'Future job: Window cleaning.',
        'property_key': 'teamville_property',
        'team_key': 'initial_team',
        'user_key': None,
        'arrival_date_offset': 0,
        'complete': False
    },
    {
        'id': 18,
        'date_offset': 7,
        'start_time': (9, 0),
        'end_time': (11, 0),
        'description': 'Future job: Full house clean.',
        'property_key': 'anytown_property',
        'team_key': 'initial_team',
        'user_key': None,
        'arrival_date_offset': 0,
        'complete': False
    },
    {
        'id': 19,
        'date_offset': 10,
        'start_time': (15, 0),
        'end_time': (17, 0),
        'description': 'Future job: Patio cleaning.',
        'property_key': 'teamville_property',
        'team_key': 'initial_team',
        'user_key': None,
        'arrival_date_offset': 0,
        'complete': False
    },
    # Past Jobs (complete)
    {
        'id': 14,
        'date_offset': -3,
        'start_time': (9, 0),
        'end_time': (11, 0),
        'description': 'Past job: Garden tidy-up.',
        'property_key': 'teamville_property',
        'team_key': 'initial_team',
        'user_key': None,
        'arrival_date_offset': 0,
        'complete': True
    },
    {
        'id': 15,
        'date_offset': -5,
        'start_time': (14, 0),
        'end_time': (16, 0),
        'description': 'Past job: Pool maintenance.',
        'property_key': 'anytown_property',
        'team_key': 'initial_team',
        'user_key': None,
        'arrival_date_offset': 0,
        'complete': True
    },
    {
        'id': 16,
        'date_offset': -7,
        'start_time': (10, 0),
        'end_time': (12, 0),
        'description': 'Past job: Roof inspection.',
        'property_key': 'teamville_property',
        'team_key': 'initial_team',
        'user_key': None,
        'arrival_date_offset': 0,
        'complete': True
    },
    {
        'id': 17,
        'date_offset': -10,
        'start_time': (8, 0),
        'end_time': (10, 0),
        'description': 'Past job: Driveway cleaning.',
        'property_key': 'anytown_property',
        'team_key': 'initial_team',
        'user_key': None,
        'arrival_date_offset': 0,
        'complete': True
    },
    # Alpha Team jobs
    {
        'id': 4,
        'date_offset': 0,
        'start_time': (10, 0),
        'end_time': (12, 0),
        'description': '',
        'property_key': 'teamville_property',
        'team_key': 'alpha_team',
        'user_key': None,
        'arrival_date_offset': 0,
        'complete': False
    },
    {
        'id': 8,
        'date_offset': 0,
        'start_time': (12, 30),
        'end_time': (14, 30),
        'description': '',
        'property_key': 'teamville_property',
        'team_key': 'alpha_team',
        'user_key': None,
        'arrival_date_offset': 1,
        'complete': False
    },
    {
        'id': 9,
        'date_offset': 0,
        'start_time': (9, 0),
        'end_time': (10, 30),
        'description': "Don't let the cat outside",
        'property_key': 'anytown_property',
        'team_key': 'alpha_team',
        'user_key': None,
        'arrival_date_offset': 2,
        'complete': False
    },
    {
        'id': 10,
        'date_offset': 0,
        'start_time': (18, 30),
        'end_time': (20, 30),
        'description': '',
        'property_key': 'anytown_property',
        'team_key': 'alpha_team',
        'user_key': 'user',
        'arrival_date_offset': 1,
        'complete': False
    },
    # Beta Team jobs
    {
        'id': 5,
        'date_offset': 0,
        'start_time': (13, 0),
        'end_time': (15, 0),
        'description': 'Beta Team Job: Garden maintenance.',
        'property_key': 'anytown_property',
        'team_key': 'beta_team',
        'user_key': None,
        'arrival_date_offset': 0,
        'complete': False
    },
    {
        'id': 11,
        'date_offset': -1,
        'start_time': (8, 0),
        'end_time': (10, 0),
        'description': 'Beta Team Job: Pool cleaning.',
        'property_key': 'anytown_property',
        'team_key': 'beta_team',
        'user_key': None,
        'arrival_date_offset': 0,
        'complete': False
    },
    # Charlie Team job
    {
        'id': 6,
        'date_offset': 0,
        'start_time': (9, 30),
        'end_time': (11, 30),
        'description': 'Charlie Team Job: Roof and gutter clean.',
        'property_key': 'teamville_property',
        'team_key': 'charlie_team',
        'user_key': None,
        'arrival_date_offset': 0,
        'complete': False
    },
    # Delta Team job
    {
        'id': 7,
        'date_offset': 0,
        'start_time': (15, 0),
        'end_time': (17, 0),
        'description': 'Delta Team Job: Driveway pressure wash.',
        'property_key': 'anytown_property',
        'team_key': 'delta_team',
        'user_key': None,
        'arrival_date_offset': 0,
        'complete': False
    }
]

# Convenience functions for accessing data
def get_user_data(user_key):
    """Get user data by key."""
    return USER_DATA.get(user_key)

def get_property_data(property_key):
    """Get property data by key."""
    return PROPERTY_DATA.get(property_key)

def get_team_data(team_key):
    """Get team data by key."""
    return TEAM_DATA.get(team_key)

def get_job_templates():
    """Get all job templates."""
    return JOB_TEMPLATES


def get_job_data_by_id(job_id, reference_date=None):
    """
    Get job data by ID as it would appear in the database.
    
    Args:
        job_id: The ID of the job to retrieve
        reference_date: Optional reference date (datetime.date in app timezone).
                       If None, uses today_in_app_tz().
    
    Returns:
        dict: Job data dictionary with fields matching the Job model attributes.
              Dates and times are converted to application timezone.
              Returns None if job_id not found.
    """
    # Find the job template
    job_template = None
    for template in JOB_TEMPLATES:
        if template['id'] == job_id:
            job_template = template
            break
    
    if not job_template:
        return None
    
    # Use reference date or today
    if reference_date is None:
        reference_date = today_in_app_tz()
    
    # Calculate the actual job date
    job_date = reference_date + timedelta(days=job_template['date_offset'])
    
    # Create time objects
    start_time_obj = time(*job_template['start_time'])
    end_time_obj = time(*job_template['end_time'])
    
    # Calculate arrival datetime
    arrival_date = job_date + timedelta(days=job_template['arrival_date_offset'])
    arrival_datetime = datetime.combine(arrival_date, start_time_obj)
    
    # Convert to application timezone for display
    app_tz = get_app_timezone()
    job_date = to_app_tz(datetime.combine(job_date, time(0, 0))).date()    
    # Note: In the database, dates/times are stored in UTC
    # For test data representation, we'll provide both UTC and app timezone versions
    job_data = {
        'id': job_template['id'],
        'date': job_date,  # Date in app timezone
        'start_time': start_time_obj,
        'end_time': end_time_obj,
        'arrival_datetime': arrival_datetime,
        'description': job_template['description'],
        'is_complete': job_template['complete'],
        'job_type': None,  # Not specified in templates
        'report': None,    # Not specified in templates
        'property_id': PROPERTY_DATA[job_template['property_key']]['id'] if job_template['property_key'] else None,
        'property_key': job_template['property_key'],
        'team_key': job_template['team_key'],
        'user_key': job_template['user_key'],
    }
    
    # Add UTC versions for consistency with Job.to_dict()
    job_data['date_utc'] = job_date.isoformat()
    job_data['start_time_utc'] = start_time_obj.isoformat()
    job_data['end_time_utc'] = end_time_obj.isoformat()
    job_data['arrival_datetime_utc'] = arrival_datetime.isoformat() if arrival_datetime else None
    
    return job_data


def get_all_job_data(reference_date=None):
    """
    Get all job data as it would appear in the database.
    
    Args:
        reference_date: Optional reference date (datetime.date in app timezone).
                       If None, uses today_in_app_tz().
    
    Returns:
        list: List of job data dictionaries for all jobs.
    """
    if reference_date is None:
        reference_date = today_in_app_tz()
    
    jobs = []
    for template in JOB_TEMPLATES:
        job_data = get_job_data_by_id(template['id'], reference_date)
        if job_data:
            jobs.append(job_data)
    
    return jobs