from database import Job, Property, User, Assignment
from services.property_service import PropertyService
from services.assignment_service import AssignmentService
from sqlalchemy import and_
from sqlalchemy.orm import joinedload
from datetime import date, datetime, timedelta

class JobService:
    def __init__(self, db_session):
        self.db_session = db_session
        self.property_service = PropertyService(db_session)
        self.assignment_service = AssignmentService(db_session)
        
    def update_job(self, job_id, job_data):
        job = self.db_session.query(Job).filter_by(id=job_id).first()
        if not job:
            return None
        job.date = job_data.get('date', job.date)
        job.time = job_data.get('time', job.time)
        job.arrival_datetime = job_data.get('arrival_datetime', job.arrival_datetime)
        job.end_time = job_data.get('end_time', job.end_time)
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

    def get_job_details(self, job_id):
        job = self.db_session.query(Job).options(joinedload(Job.property)).filter(Job.id == job_id).first()
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


    def get_jobs_for_user_on_date(self, user_id, team_id, date: date):
        user = self.db_session.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        # Get all Assignment entries for this user
        # Query for distinct Job objects directly, joining with Assignment and ordering
        jobs = self.db_session.query(Job).options(joinedload(Job.property)).join(Assignment).filter(
            and_(
                Job.date == date,
                (Assignment.user_id == user_id) | (Assignment.team_id == team_id)
            )
        ).order_by(Job.date, Job.time).group_by(Job.id).all() # Using group_by for distinct jobs and preserving order

        return jobs

    def create_job(self, job_data):
        new_job = Job(
            date=job_data['date'],
            time=job_data['time'],
            arrival_datetime=job_data.get('arrival_datetime'),
            end_time=job_data['end_time'],
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