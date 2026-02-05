from config import DATETIME_FORMATS
from database import Job, Property, User, Assignment
from services.property_service import PropertyService
from services.assignment_service import AssignmentService
from sqlalchemy import and_
from sqlalchemy.orm import joinedload
from datetime import date, datetime, timedelta

from utils.timezone import from_app_tz, to_app_tz

class JobService:
    def __init__(self, db_session):
        self.db_session = db_session
        self.property_service = PropertyService(db_session)
        self.assignment_service = AssignmentService(db_session)
        
    def update_job(self, job_id, job_data):
        job = self.db_session.query(Job).filter_by(id=job_id).first()
        
        if not job:
            return None
        
        # Update job date time and handle times one conversion
        job_date = job_data['date'] if 'date' in job_data else to_app_tz(job.date)
        job_time = job_data['time'] if 'time' in job_data else to_app_tz(job.time)
        job_end_time = job_data['end_time'] if 'end_time' in job_data else to_app_tz(job.end_time)
        job_arrival_datetime = job_data['arrival_datetime'] if 'arrival_datetime' in job_data else to_app_tz(job.arrival_datetime)
        # Combine date and time strings into a single datetime string in the app's timezone
        start_datetime_str = f"{job_date} {job_time}"
        end_datetime_str = f"{job_date} {job_end_time}"
        # Convert to datetime object in app timezone, then store in UTC
        start_datetime = from_app_tz(datetime.fromisoformat(start_datetime_str))
        end_datetime = from_app_tz(datetime.fromisoformat(end_datetime_str))
        job.date = start_datetime.date()
        job.time = start_datetime.time()
        job.arrival_datetime = from_app_tz(datetime.fromisoformat(job_arrival_datetime)) if 'arrival_datetime' in job_data else job.arrival_datetime
        job.end_time = end_datetime.time()
        job.description = job_data.get('description', job.description)
        property_id = job_data.get('property_id')
        if property_id:
            property_obj = self.property_service.get_property_by_id(property_id)
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
        """
        Update job report text and completion status
        """
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
        """
        Retrieve all jobs for a specific property.
        """
        jobs = self.db_session.query(Job).options(joinedload(Job.property)).filter(Job.property_id == property_id).order_by(Job.date, Job.time).all()
        return jobs

    def get_filtered_jobs_by_property_id(self, property_id, start_date=None, end_date=None,
                                         show_past_jobs=False, show_completed=True):
        """
        Retrieve filtered jobs for a specific property with optional date range and filters.
        
        Args:
            property_id: ID of the property
            start_date: Start date for filtering (datetime.date in UTC)
            end_date: End date for filtering (datetime.date in UTC)
            show_past_jobs: If True, include jobs before today (default: False)
            show_completed: If True, include completed jobs (default: True)
            
        Returns:
            List of Job objects matching the filters, ordered by date and time
        """
        from utils.timezone import utc_now, today_in_app_tz
        from datetime import date as date_type
        
        query = self.db_session.query(Job).options(joinedload(Job.property)).filter(Job.property_id == property_id)
        
        # Apply date range filters
        if start_date:
            query = query.filter(Job.date >= start_date)
        if end_date:
            query = query.filter(Job.date <= end_date)
        
        # Apply past jobs filter
        if not show_past_jobs:
            # Get today's date in UTC for comparison
            today_utc = utc_now().date()
            query = query.filter(Job.date >= today_utc)
        
        # Apply completion status filter
        if not show_completed:
            query = query.filter(Job.is_complete == False)
        
        # Order by date and time
        query = query.order_by(Job.date, Job.time)
        
        return query.all()


    def get_jobs_for_user_on_date(self, user_id, team_id, date: date):
        user = self.db_session.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        # Subquery to get distinct job IDs that match the assignment criteria
        job_ids_subquery = self.db_session.query(Assignment.job_id).join(
            Job, Assignment.job_id == Job.id
        ).filter(
            and_(
                Job.date == date,
                (Assignment.user_id == user_id) | (Assignment.team_id == team_id)
            )
        ).distinct().subquery()
        
        # Now query jobs with properties using the subquery
        # Use .select() to explicitly convert subquery to select() for IN() clause
        jobs = self.db_session.query(Job).options(joinedload(Job.property)).filter(
            Job.id.in_(job_ids_subquery.select())
        ).order_by(Job.date, Job.time).all()
        
        return jobs

    def create_job(self, job_data):
        # Combine date and time strings into a single datetime string in the app's timezone
        start_datetime_str = f"{job_data['date']} {job_data['time']}"
        end_datetime_str = f"{job_data['date']} {job_data['end_time']}"
        # Convert to datetime object in app timezone, then store in UTC
        start_datetime = from_app_tz(datetime.fromisoformat(start_datetime_str))
        end_datetime = from_app_tz(datetime.fromisoformat(end_datetime_str))
        arrival_datetime = from_app_tz(datetime.fromisoformat(job_data['arrival_datetime'])) if 'arrival_datetime' in job_data else None
        new_job = Job(
            date=start_datetime.date(),
            time=start_datetime.time(),
            arrival_datetime=arrival_datetime,
            end_time=end_datetime.time(),
            description=job_data.get('description'),
            is_complete=False,
            job_type=job_data.get('job_type'),
            property_id=job_data['property_id']
        )
        self.db_session.add(new_job)
        self.db_session.commit()
        # Reload job with property details for rendering
        self.db_session.refresh(new_job)
        new_job.property = self.db_session.query(Property).filter_by(id=new_job.property_id).first()
        return new_job
    
    def remove_team_from_jobs(self, team_id):

        assignments = self.db_session.query(Assignment).filter_by(team_id=team_id).all()
        for assignment in assignments:
            self.db_session.delete(assignment)
        self.db_session.commit()

    def delete_job(self, job_id):
        job = self.db_session.query(Job).filter_by(id=job_id).first()
        if job:
            # Delete all associated assignments first
            assignments = self.assignment_service.get_assignments_for_job(job_id)
            for assignment in assignments:
                self.db_session.delete(assignment)
            
            self.db_session.delete(job)
            self.db_session.commit()
            return True
        return False
    
    def push_uncompleted_jobs_to_next_day(self):
        """Push all uncompleted jobs with a date before today to the next day."""
        today = date.today()
        uncompleted_jobs = self.db_session.query(Job).filter(
            and_(
                Job.date < today,
                Job.is_complete == False
            )
        ).all()
        
        for job in uncompleted_jobs:
            job.date += timedelta(days=1)
        
        self.db_session.commit()    