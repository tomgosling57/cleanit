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

    def get_cleaner_jobs_for_today(self, cleaner_id):
        today = date.today()
        jobs = self.db_session.query(Job).join(Property).filter(
            and_(
                Job.assigned_cleaners.like(f"%{cleaner_id}%"),
                Job.date == today
            )
        ).all()
        for job in jobs:
            if job.property:
                print(f"  Property Address: {job.property.address}")
                print(f"  Property ID: {job.property_id}")
            else:
                print("  No property associated.")

        return jobs

    def update_job(self, job_id, job_data):
        job = self.db_session.query(Job).filter_by(id=job_id).first()
        if not job:
            return None
        job.date = job_data.get('date', job.date)
        job.time = job_data.get('time', job.time)
        job.arrival_time = job_data.get('arrival_time', job.arrival_time)
        job.end_time = job_data.get('end_time', job.end_time)
        job.description = job_data.get('description', job.description)
        job.assigned_cleaners = job_data.get('assigned_cleaners', job.assigned_cleaners)
        property_address = job_data.get('property_address')
        if property_address:
            property_obj = self.property_service.get_property_by_address(property_address)
            if not property_obj:
                property_obj = self.property_service.create_property(property_address)
            job.property_id = property_obj.id
        self.db_session.commit()
        return job

    def update_job_completion_status(self, job_id, is_complete):
        job = self.db_session.query(Job).filter_by(id=job_id).first()
        if job:
            job.is_complete = is_complete
            self.db_session.commit()
            return job
        return None

    def get_job_details(self, job_id):
        job = self.db_session.query(Job).options(joinedload(Job.property)).filter(Job.id == job_id).first()
        return job
    
    def get_all_jobs(self):
        jobs = self.db_session.query(Job).options(joinedload(Job.property))
        return jobs
    
    def get_back_to_back_jobs_for_date(self, target_date: date, threshold_minutes: int = 15):
        """
        Identifies jobs on a specific date that are back-to-back within a given threshold.
        Returns a list of job IDs that are considered back-to-back.
        """
        jobs_on_date = self.db_session.query(Job).filter(Job.date == target_date).order_by(Job.time).all()
        
        back_to_back_job_ids = set()

        for i in range(len(jobs_on_date) - 1):
            current_job = jobs_on_date[i]
            next_job = jobs_on_date[i+1]

            # Combine date with time to create datetime objects for comparison
            current_job_end_datetime = datetime.combine(target_date, current_job.end_time)
            next_job_start_datetime = datetime.combine(target_date, next_job.time)

            time_difference = next_job_start_datetime - current_job_end_datetime
            
            # Check if the time difference is positive (next job starts after current job ends)
            # and within the configurable threshold
            if timedelta(minutes=0) <= time_difference <= timedelta(minutes=threshold_minutes):
                back_to_back_job_ids.add(current_job.id)
                back_to_back_job_ids.add(next_job.id)
                
        return list(back_to_back_job_ids)

    def create_job(self, job_data):
        new_job = Job(
            date=job_data['date'],
            time=job_data['time'],
            arrival_time=job_data.get('arrival_time'),
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