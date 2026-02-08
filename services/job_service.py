from collections import defaultdict
from flask import current_app, has_app_context
from config import DATETIME_FORMATS
from database import Job, Property, Team, User, Assignment
from services.property_service import PropertyService
from services.assignment_service import AssignmentService
from sqlalchemy import DateTime, and_, cast, func
from sqlalchemy.orm import joinedload
from datetime import date, datetime, timedelta

from tests.db_helpers import get_database_url
from utils.timezone import from_app_tz, to_app_tz, utc_now, today_in_app_tz

def combine_date_time_sql(date_column, time_column):
    """
    Database-agnostic function to combine date and time columns in SQL.
    
    Args:
        date_column: SQLAlchemy Date column
        time_column: SQLAlchemy Time column
    
    Returns:
        SQLAlchemy expression that combines date and time
    """
    if has_app_context():
        db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
    else:
        from tests.db_helpers import get_database_url
        db_uri = get_database_url()
    
    # Detect database type from URI
    if db_uri.startswith('sqlite'):
        # SQLite: datetime(date, time)
        return func.datetime(date_column, time_column)
    elif 'postgresql' in db_uri or db_uri.startswith('postgres'):
        # PostgreSQL: CAST(date AS timestamp) + time
        return cast(date_column, DateTime) + time_column
    elif 'mysql' in db_uri:
        # MySQL: TIMESTAMP(CONCAT(date, ' ', time))
        return func.timestamp(func.concat(date_column, ' ', time_column))
    else:
        # Default fallback (SQLite syntax)
        return func.datetime(date_column, time_column)
    
    
class JobService:
    def __init__(self, db_session):
        self.db_session = db_session
        self.property_service = PropertyService(db_session)
        self.assignment_service = AssignmentService(db_session)
    
    def _parse_job_times(self, job_data):
        """
        Helper to convert app timezone date/time strings to UTC datetime objects.
        
        Args:
            job_data: Dict with 'date', 'time', 'end_time', and optionally 'arrival_datetime'
        
        Returns:
            Dict with UTC date, time, end_time, and arrival_datetime
        """
        # Parse date and times in app timezone
        start_datetime_str = f"{job_data['date']} {job_data['time']}"
        end_datetime_str = f"{job_data['date']} {job_data['end_time']}"
        
        # Convert to UTC
        start_datetime_utc = from_app_tz(datetime.fromisoformat(start_datetime_str))
        end_datetime_utc = from_app_tz(datetime.fromisoformat(end_datetime_str))
        
        result = {
            'date': start_datetime_utc.date(),
            'time': start_datetime_utc.time(),
            'end_time': end_datetime_utc.time(),
        }
        
        # Handle optional arrival_datetime
        if 'arrival_datetime' in job_data and job_data['arrival_datetime']:
            arrival_datetime_utc = from_app_tz(job_data['arrival_datetime'])
            result['arrival_datetime'] = arrival_datetime_utc
        
        return result
        
    def create_job(self, job_data):
        """
        Create a new job. Expects job_data with date/time in app timezone.
        """
        # Convert times to UTC
        utc_times = self._parse_job_times(job_data)
        
        # Create job with UTC times
        new_job = Job(
            date=utc_times['date'],
            time=utc_times['time'],
            end_time=utc_times['end_time'],
            arrival_datetime=utc_times.get('arrival_datetime'),
            description=job_data.get('description'),
            is_complete=False,
            job_type=job_data.get('job_type'),
            property_id=job_data['property_id']
        )
        
        self.db_session.add(new_job)
        self.db_session.commit()
        self.db_session.refresh(new_job)
        
        return new_job
    
    def update_job(self, job_id, job_data):
        """
        Update an existing job. Expects job_data with date/time in app timezone.
        """
        job = self.db_session.query(Job).filter_by(id=job_id).first()
        
        if not job:
            return None
        
        # Convert times to UTC
        utc_times = self._parse_job_times(job_data)
        
        # Update job fields
        job.date = utc_times['date']
        job.time = utc_times['time']
        job.end_time = utc_times['end_time']
        
        if 'arrival_datetime' in utc_times:
            job.arrival_datetime = utc_times['arrival_datetime']
        
        job.description = job_data.get('description', job.description)
        
        if 'property_id' in job_data:
            property_obj = self.property_service.get_property_by_id(job_data['property_id'])
            if property_obj:
                job.property_id = property_obj.id
        
        self.db_session.commit()
        return job

    def update_job_completion_status(self, job_id, is_complete):
        job = self.db_session.query(Job).filter_by(id=job_id).first()
        if job:
            job.is_complete = is_complete
            self.db_session.commit()
            self.db_session.refresh(job)
            return job
        return None

    def update_job_report_and_completion(self, job_id, report_text, is_complete=True):
        job = self.db_session.query(Job).filter_by(id=job_id).first()
        if job:
            job.report = report_text
            job.is_complete = is_complete
            self.db_session.commit()
            self.db_session.refresh(job)
            return job
        return None

    def get_job_details(self, job_id, include_access_notes=False):
        job = self.db_session.query(Job).options(joinedload(Job.property)).filter(Job.id == job_id).first()
        if job and not include_access_notes:
            job.property.access_notes = None
        return job
    
    def get_all_jobs(self):
        jobs = self.db_session.query(Job).options(joinedload(Job.property)).order_by(Job.date, Job.time).all()
        return jobs
    
    def get_jobs_by_property_id(self, property_id):
        jobs = self.db_session.query(Job).options(joinedload(Job.property)).filter(Job.property_id == property_id).order_by(Job.date, Job.time).all()
        return jobs

    def get_filtered_jobs_by_property_id(self, property_id, start_date=None, end_date=None, show_completed=True):
        """
        Retrieve filtered jobs for a specific property.
        
        Args:
            property_id: ID of the property
            start_date: Start date in app timezone (datetime.date)
            end_date: End date in app timezone (datetime.date)
            show_completed: If True, include completed jobs
        """
        query = self.db_session.query(Job).options(joinedload(Job.property)).filter(Job.property_id == property_id)
        
        # Convert app timezone dates to UTC datetime for comparison
        # Filter by job start datetime (in UTC) falling within the date range
        if start_date:
            start_datetime_utc = from_app_tz(datetime.combine(start_date, datetime.min.time()))
            query = query.filter(combine_date_time_sql(Job.date, Job.time) >= start_datetime_utc)
        
        if end_date:
            end_datetime_utc = from_app_tz(datetime.combine(end_date, datetime.max.time()))
            query = query.filter(combine_date_time_sql(Job.date, Job.time) <= end_datetime_utc)
        
        if not show_completed:
            query = query.filter(Job.is_complete == False)
        
        return query.order_by(Job.date, Job.time).all()

    def get_jobs_for_user_on_date(self, user_id, team_id, date_obj: date):
        """
        Get jobs for a user/team on a specific date.
        
        Args:
            user_id: User ID
            team_id: Team ID
            date_obj: Date in app timezone (datetime.date)
        """
        user = self.db_session.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        # Convert app timezone date to UTC datetime range
        # A single app timezone day may span two UTC days
        start_of_day_app = datetime.combine(date_obj, datetime.min.time())
        end_of_day_app = datetime.combine(date_obj, datetime.max.time())
        
        start_of_day_utc = from_app_tz(start_of_day_app)
        end_of_day_utc = from_app_tz(end_of_day_app)
        
        # Query jobs where the job's start datetime (in app timezone) falls within the date
        # We need to check if datetime.combine(Job.date, Job.time) converted to app timezone
        # falls within the app timezone date range.
        # Since we can't easily do timezone conversion in SQL, we filter by UTC datetime
        # range that corresponds to the app timezone date.
        job_ids_subquery = self.db_session.query(Assignment.job_id).join(
            Job, Assignment.job_id == Job.id
        ).filter(
            and_(
                # Create datetime from Job.date and Job.time (both in UTC)
                # and check if it falls within the UTC datetime range
                combine_date_time_sql(Job.date, Job.time) >= start_of_day_utc,
                combine_date_time_sql(Job.date, Job.time) <= end_of_day_utc,
                (Assignment.user_id == user_id) | (Assignment.team_id == team_id)
            )
        ).distinct().subquery()
        
        jobs = self.db_session.query(Job).options(joinedload(Job.property)).filter(
            Job.id.in_(job_ids_subquery.select())
        ).order_by(Job.date, Job.time).all()
        
        return jobs

    def remove_team_from_jobs(self, team_id):
        assignments = self.db_session.query(Assignment).filter_by(team_id=team_id).all()
        for assignment in assignments:
            self.db_session.delete(assignment)
        self.db_session.commit()

    def delete_job(self, job_id):
        job = self.db_session.query(Job).filter_by(id=job_id).first()
        if job:
            assignments = self.assignment_service.get_assignments_for_job(job_id)
            for assignment in assignments:
                self.db_session.delete(assignment)
            
            self.db_session.delete(job)
            self.db_session.commit()
            return True
        return False
    
    def push_uncompleted_jobs_to_next_day(self):
        """Push all uncompleted jobs with a date before today to the next day."""
        # Get today's date in app timezone
        today_app = today_in_app_tz()
        # Convert to UTC datetime at start of day for comparison
        today_start_utc = from_app_tz(datetime.combine(today_app, datetime.min.time()))
        
        # Find jobs where the job's start datetime (in UTC) is before today in app timezone
        uncompleted_jobs = self.db_session.query(Job).filter(
            and_(
                combine_date_time_sql(Job.date, Job.time) < today_start_utc,
                Job.is_complete == False
            )
        ).all()
        
        for job in uncompleted_jobs:
            job.date += timedelta(days=1)
        
        self.db_session.commit()
        current_app.logger.debug(f"Pushed {len(uncompleted_jobs)} uncompleted jobs to the next day.")
    
    def get_jobs_grouped_by_team_for_date(self, date_obj: date):
        """
        Get jobs grouped by team for a specific date.
        
        Args:
            date_obj: Date in app timezone (datetime.date)
        """        # Convert app timezone date to UTC datetime range
        start_of_day_app = datetime.combine(date_obj, datetime.min.time())
        end_of_day_app = datetime.combine(date_obj, datetime.max.time())
        
        start_of_day_utc = from_app_tz(start_of_day_app)
        end_of_day_utc = from_app_tz(end_of_day_app)
        
        # Query jobs with their team assignments for the specified date
        jobs_with_teams = self.db_session.query(Job, Team).join(
            Assignment, Job.id == Assignment.job_id
        ).join(
            Team, Assignment.team_id == Team.id
        ).filter(
            and_(
                combine_date_time_sql(Job.date, Job.time) >= start_of_day_utc,
                combine_date_time_sql(Job.date, Job.time) <= end_of_day_utc
            )
        ).all()
        
        # Group jobs by team
        jobs_by_team = defaultdict(list)
        for job, team in jobs_with_teams:
            jobs_by_team[team].append(job)
        
        return dict(jobs_by_team)