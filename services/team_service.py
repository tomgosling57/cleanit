from database import Team, User
from sqlalchemy import and_
from sqlalchemy.orm import joinedload

class TeamService:
    def __init__(self, db_session):
        self.db_session = db_session

    def get_team_members(self, team_id):
        team = self.db_session.query(Team).options(joinedload(Team.members)).filter_by(id=team_id).first()
        return team.members if team else []

    def add_member_to_team(self, team_id, user_id):
        team_member = TeamMembers(team_id=team_id, user_id=user_id)
        self.db_session.add(team_member)
        self.db_session.commit()
        return team_member

    def remove_member_from_team(self, team_id, user_id):
        team_member = self.db_session.query(TeamMembers).filter_by(team_id=team_id, user_id=user_id).first()
        if team_member:
            self.db_session.delete(team_member)
            self.db_session.commit()
            return team_member

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
        new_team.members = self.db_session.query(User).filter(User.id.in_([member.id for member in new_team.members])).all()
        return new_team