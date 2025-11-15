from database import Assignment, User, Job
from sqlalchemy.orm import joinedload
from datetime import date

class AssignmentService:
    def __init__(self, db_session):
        self.db_session = db_session
    
    def get_assignments_for_user_on_date(self, user_id, team_id, date: date):
        user = self.db_session.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        # Get all Assignment entries for this user
        assignments = self.db_session.query(Assignment).join(Job).filter(Job.date == date).filter(
            Assignment.user_id == user_id or Assignment.team_id == team_id
        ).options(joinedload(Assignment.job, innerjoin=True)).all()

        # Extract job IDs from Assignment entries
        job_ids = list(set(jc.job_id for jc in assignments))
        
        # Query for jobs using the extracted job IDs
        jobs = self.db_session.query(Job).options(joinedload(Job.property)).filter(Job.id.in_(job_ids)).all()
        return jobs