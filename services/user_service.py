from werkzeug.security import generate_password_hash, check_password_hash
from database import User, Team
from sqlalchemy.orm import joinedload

class UserService:
    def __init__(self, db_session):
        self.db_session = db_session

    def get_all_users(self):
        """Gets all users from the User table.
        
        Returns a list of User objects"""
        users = self.db_session.query(User).options(joinedload(User.team)).all()
        return users

    def get_users_by_role(self, role):
        """Gets users from the User table filtering by role.
        
        Returns a list of User objects"""
        users = self.db_session.query(User).filter_by(role=role).all()
        return users

    def get_user_by_id(self, user_id):
        """Gets a user from the User table with the given id.
        
        Returns a User object or None"""
        user = self.db_session.query(User).filter_by(id=user_id).first()
        return user

    def get_user_by_email(self, email):
        """"""
        user = self.db_session.query(User).filter_by(email=email).first()
        return user
    
    def authenticate_user(self, username, password):
        user = self.get_user_by_username(username)
        if user and check_password_hash(user.password_hash, password):
            return user
        return None

    def update_user(self, user_id, data):
        user = self.db_session.query(User).filter_by(id=user_id).first()
        if not user:
            return None
        
        if 'username' in data:
            user.username = data['username']
        if 'role' in data:
            user.role = data['role']
        if 'password' in data:
            user.set_password(data['password'])
        
        self.db_session.commit()
        return user

    def delete_user(self, user_id):
        """Deletes the user from the Use table with the given id.
        
        Returns true or false"""
        user = self.db_session.query(User).filter_by(id=user_id).first()
        if not user:
            return False
        
        self.db_session.delete(user)
        self.db_session.commit()
        return True

    def remove_team_from_users(self, team_id):
        """Removes the given team_id from all of the User objects within the User table.
        
        Returns None"""
        users = self.db_session.query(User).filter_by(team_id=team_id).all()
        for user in users:
            user.team_id = None
        self.db_session.commit()