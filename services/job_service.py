from database import Job, Property, User
from sqlalchemy import and_
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

    def update_job_status(self, job_id, status):
        job = self.db_session.query(Job).filter_by(id=job_id).first()
        if job:
            job.status = status
            self.db_session.commit()
            return job
        return None

    def get_job_details(self, job_id):
        job = self.db_session.query(Job).options(joinedload(Job.property)).filter(Job.id == job_id).first()
        return job