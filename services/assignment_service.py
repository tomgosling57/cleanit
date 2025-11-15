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
    
    def create_assignment(self, job_id, user_id=None, team_id=None):
        if not user_id and not team_id:
            return None
        assignment = Assignment(job_id=job_id, user_id=user_id, team_id=team_id)
        self.db_session.add(assignment)
        self.db_session.commit()
        return assignment
    
    def delete_assignment(self, assignment_id):
        assignment = self.db_session.query(Assignment).filter(Assignment.id == assignment_id).first()
        if assignment:
            self.db_session.delete(assignment)
            self.db_session.commit()
            return True
        return False
    
    def get_assignments_for_job(self, job_id):
        assignments = self.db_session.query(Assignment).filter(Assignment.job_id == job_id).all()
        return assignments