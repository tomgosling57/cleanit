from database import Job, Property, User
from sqlalchemy import and_, or_
from sqlalchemy.orm import joinedload
from datetime import date

class JobService:
    def __init__(self, db_session):
        self.db_session = db_session

    def get_cleaner_jobs_for_today(self, cleaner_id):
        today = date.today()
        jobs = self.db_session.query(Job).join(Property).filter(
            and_(
                Job.assigned_cleaners.like(f"%{cleaner_id}%"),
                Job.date == today
            )
        ).all()
        for job in jobs:
            print(f"Job ID: {job.id}, Title: {job.job_title}")
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

        job.job_title = job_data.get('job_title', job.job_title)
        job.date = job_data.get('date', job.date)
        job.time = job_data.get('time', job.time)
        job.duration = job_data.get('duration', job.duration)
        job.description = job_data.get('description', job.description)
        job.assigned_cleaners = job_data.get('assigned_cleaners', job.assigned_cleaners)
        property_address = job_data.get('property_address')
        if property_address:
            property_obj = self.get_property_by_address(property_address)
            if not property_obj:
                property_obj = self.create_property(property_address)
            job.property_id = property
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

    def get_property_by_address(self, address):
        return self.db_session.query(Property).filter_by(address=address).first()

    def create_property(self, address, access_notes=None):
        new_property = Property(address=address, access_notes=access_notes)
        self.db_session.add(new_property)
        self.db_session.commit()
        return new_property

    def create_job(self, job_data):
        new_job = Job(
            job_title=job_data['job_title'],
            date=job_data['date'],
            time=job_data['time'],
            duration=job_data['duration'],
            description=job_data.get('description'),
            assigned_cleaners=job_data.get('assigned_cleaners'),
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

        jobs = self.db_session.query(Job).filter(
            or_(
                Job.assigned_teams.like(f'%,{team_id},%'),
                Job.assigned_teams == f'{team_id}'
            )
        ).all()
        for job in jobs:
            job.assigned_teams = job.assigned_teams.replace(f'%,{team_id},%', '')
        self.db_session.commit()