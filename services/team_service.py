from database import Team, Job
from services.job_service import JobService
from services.user_service import UserService
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

class TeamService:
    def __init__(self, db_session):
        self.db_session = db_session
        self.job_service = JobService(self.db_session)
        self.user_service = UserService(self.db_session)
    def get_all_teams(self):
        teams = self.db_session.query(Team).options(joinedload(Team.members), joinedload(Team.team_leader)).all()
        return teams
        
    def get_team(self, team_id):
        team = self.db_session.query(Team).options(joinedload(Team.members)).filter(Team.id == team_id).first()
        return team

    def add_member_to_team(self, team, user):
        user.team_id = team.id
        team.members.append(user)
        self.db_session.commit()

        return user

    def remove_member_from_team(self, team, user):
        if user in team.members:
            team.members.remove(user)
            user.team_id = None
            self.db_session.commit()

    def create_team(self, team_data):
        new_team = Team(
            name=team_data['name'],
            team_leader_id=team_data.get('team_leader_id'),
            members=team_data.get('members', [])
        )
        self.db_session.add(new_team)
        self.db_session.commit()
        # Reload job with property details for rendering
        self.db_session.refresh(new_team)
        return new_team

    def delete_team(self, team):
        self.job_service.remove_team_from_jobs(team.id)
        self.user_service.remove_team_from_users(team.id)
        self.db_session.delete(team)
        self.db_session.commit()