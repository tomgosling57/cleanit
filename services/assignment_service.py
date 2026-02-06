# services/assignment_service.py
from collections import defaultdict
from database import Assignment, User, Job, Team
from sqlalchemy import and_
from sqlalchemy.orm import joinedload
from datetime import date

class AssignmentService:
    def __init__(self, db_session):
        self.db_session = db_session
    
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

    def get_assignments_for_jobs(self, job_ids):
        assignments = self.db_session.query(Assignment).filter(Assignment.job_id.in_(job_ids)).all()
        return assignments
    
    def update_assignments(self, job_id, team_ids=[], user_ids=[]):
        # First, delete existing assignments for the job
        self.db_session.query(Assignment).filter(Assignment.job_id == job_id).delete()
        self.db_session.commit()

        # Create new assignments for teams
        for team_id in team_ids:
            self.create_assignment(job_id=job_id, team_id=team_id)

        # Create new assignments for users
        for user_id in user_ids:
            self.create_assignment(job_id=job_id, user_id=user_id)

    def update_job_team_assignment(self, job, new_team, old_team=None):
        """
        Updates a job's team assignment by removing the old team and adding the new team.
        Assumes a job can only be assigned to one team at a time for drag-and-drop reassignments.
        If a job can have multiple teams, this logic needs to be adjusted.
        """
        # Remove the old team assignment for the job
        if old_team:
            self.db_session.query(Assignment).filter(
                and_(
                    Assignment.job_id == job.id,
                    Assignment.team_id == old_team.id
                )
            ).delete()
            self.db_session.commit()    

        # Add the new team assignment for the job
    
        # Check if an assignment to the new team already exists to prevent duplicates
        existing_assignment = self.db_session.query(Assignment).filter(
            and_(
                Assignment.job_id == job_id,
                Assignment.team_id == new_team_id
            )
        ).first()
        if not existing_assignment:
            self.create_assignment(job_id=job.id, team_id=new_team.id)
        else:
            return {"Job already assigned": f"Job {job.id} is already assigned to team {new_team.id}. No new assignment created."}

    def user_assigned_to_job(self, user_id, job_id):
        assignment = self.db_session.query(Assignment).filter(
            and_(
                Assignment.job_id == job_id,
                Assignment.user_id == user_id
            )
        ).first()
        return assignment is not None

    def team_assigned_to_job(self, team_id, job_id):
        assignment = self.db_session.query(Assignment).filter(
            and_(
                Assignment.job_id == job_id,
                Assignment.team_id == team_id
            )
        ).first()
        return assignment is not None    

    def get_users_for_job(self, job_id):
        assignments = self.db_session.query(Assignment).filter(
            and_(
                Assignment.job_id == job_id,
                Assignment.user_id != None
            )
        ).all()
        cleaners = self.db_session.query(User).filter(User.id.in_([assignment.user_id for assignment in assignments])).all()
        return cleaners

    def get_teams_for_job(self, job_id):
        assignments = self.db_session.query(Assignment).filter(
            and_(
                Assignment.job_id == job_id,
                Assignment.team_id != None
            )
        ).all()
        teams = self.db_session.query(Team).filter(Team.id.in_([assignment.team_id for assignment in assignments])).all()
        return teams
