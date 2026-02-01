from database import Team, User, Job, Assignment
from services.job_service import JobService
from services.user_service import UserService
from sqlalchemy.orm import joinedload

class TeamService:
    def __init__(self, db_session):
        self.db_session = db_session
        self.job_service = JobService(self.db_session)
        self.user_service = UserService(self.db_session)
    def get_all_teams(self):
        teams = self.db_session.query(Team)\
            .options(joinedload(Team.members), joinedload(Team.team_leader))\
            .order_by(Team.id.asc())\
            .all()
        return teams
        
    def get_team(self, team_id):
        team = self.db_session.query(Team).options(joinedload(Team.members)).filter(Team.id == team_id).first()
        return team

    def update_team(self, team):
        self.db_session.add(team)
        self.db_session.commit()
        self.db_session.refresh(team)
        return team

    def set_team_leader(self, team_id, user_id=None):
        team = self.get_team(team_id)
        if team:
            team.team_leader_id = user_id 
            if user_id:
                member_ids = [member.id for member in team.members] if team.members else []
                if user_id not in member_ids:
                    self.add_team_member(team_id, user_id)
                self.db_session.commit()
                self.db_session.refresh(team)
                if not user_id:
                    self.auto_assign_team_leader(team)
        return team

    def auto_assign_team_leader(self, team):
        if not team:
            return None

        # Validate current team leader
        if team.team_leader_id:
            current_leader_is_member = False
            for member in team.members:
                if member.id == team.team_leader_id:
                    current_leader_is_member = True
                    break
            if not current_leader_is_member:
                team.team_leader_id = None # Clear stale leader ID

        if not team.team_leader_id: # Now check if a leader needs to be assigned
            for member in team.members:
                if member.role in ['supervisor', 'admin']:
                    team.team_leader_id = member.id
                    self.db_session.commit()
                    self.db_session.refresh(team)
                    return team
        self.db_session.commit() # Commit if leader was cleared but no new leader assigned
        self.db_session.refresh(team)
        return team
    
    def update_team_details(self, team_id, team_name, member_ids, team_leader_id):
        team = self.get_team(team_id)
        if not team:
            return None

        team.name = team_name
        # self.update_team(team)

        # Update members
        current_member_ids = {member.id for member in team.members} if team.members else set()
        new_member_ids = {int(mid) for mid in member_ids if mid}
        print(f"current_members: {current_member_ids}\nnew_members: {new_member_ids}")
        # Add new members
        for member_id in new_member_ids - current_member_ids:
            self.add_team_member(team_id, member_id)

        # Update team leader
        if team_leader_id:
            self.set_team_leader(team_id, int(team_leader_id))
        else:
            self.set_team_leader(team_id, None)
            self.auto_assign_team_leader(team)                               
        self.db_session.refresh(team)
        return team

    def add_team_member(self, team_id, user_id):
        team = self.get_team(team_id)
        user = self.user_service.get_user_by_id(user_id)
        old_team_id = user.team_id if user else None
        old_team = self.get_team(old_team_id) if old_team_id else None
        if team and user:
            # Update user and new team 
            user.team_id = team.id
            team.members.append(user)
            self.auto_assign_team_leader(team)
            # Update old team if applicable
            if old_team:
                self.set_team_leader(old_team.id, None) # Remove the team leader
                self.auto_assign_team_leader(old_team) # Auto reassign new leader
            self.db_session.commit()
            self.db_session.refresh(team) # Refresh team to reflect changes
            return user
        return None

    def remove_team_member(self, team_id, user_id):
        team = self.get_team(team_id)
        user = self.user_service.get_user_by_id(user_id)
        if team and user and user in team.members:
            user.team_id = None
            team.members.remove(user)
            if team.team_leader_id == user.id:
                team.team_leader_id = None
                self.auto_assign_team_leader(team)
            self.db_session.commit()
            return user
        return None

    def create_team(self, team_data):
        member_ids = team_data.get('members', [])
        team_leader_id = team_data.get('team_leader_id')
        if team_leader_id and team_leader_id not in member_ids:
            member_ids.append(team_leader_id)
        members = self.db_session.query(User).options(joinedload(User.team).joinedload(Team.members)).filter(User.id.in_(member_ids)).all()
        new_team = Team(
            name=team_data.get('name'),
            team_leader_id=team_leader_id,
            members=members
        )
        self.db_session.add(new_team)
        self.db_session.commit()
        # Reload job with property details for rendering
        self.db_session.refresh(new_team)
        for member in members:
            member.team_id = new_team.id
        self.db_session.commit()
        return new_team

    def delete_team(self, team):
        self.job_service.remove_team_from_jobs(team.id)
        self.user_service.remove_team_from_users(team.id)
        self.db_session.delete(team)
        self.db_session.commit()

    def get_categorized_users_for_team(self, team_id):
        all_users = self.db_session.query(User).all()
        
        on_this_team = []
        on_a_different_team = []
        unassigned = []

        for user in all_users:
            if user.team_id == team_id:
                on_this_team.append(user)
            elif user.team_id is not None:
                on_a_different_team.append(user)
            else:
                unassigned.append(user)
        
        return {
            'on_this_team': on_this_team,
            'on_a_different_team': on_a_different_team,
            'unassigned': unassigned
        }