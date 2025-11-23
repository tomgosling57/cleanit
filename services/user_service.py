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
        """Get a user from the User table with the given email.
        
        Returns a User object or none"""
        user = self.db_session.query(User).filter_by(email=email).first()
        return user
    
    def authenticate_user(self, email, password):
        """Authenticate a user within the User table via email and password.

        Returns User object or None"""
        user = self.get_user_by_email(email)
        if user and check_password_hash(user.password_hash, password):
            return user
        return None

    def create_user(self, first_name: str, last_name: str, email: str, password: str, role:str, phone:str=None, team_id: int=None):
        """Create a user within the user table with the given attributes. The email attribute must be unique. 
        The password will be hashed internally before it is stored in the table. Returns none if the email is not unique.
        
        Returns the Created User or None"""
        existing_user = self.db_session.query(User).filter_by(email=email).first()

        # Return none if the email is not unique
        if existing_user:
            return None
        
        new_user = User(first_name=first_name, last_name=last_name, email=email, phone=phone, role=role, team_id=team_id)
        new_user.set_password(password)
        self.db_session.add(new_user)
        self.db_session.refresh(new_user)
        self.db_session.commit()
        return new_user
    
    def update_user(self, user_id, data):
        """Update a user within the User table with the given data.
        
        Returns the updated User object or None"""
        user = self.db_session.query(User).filter_by(id=user_id).first()

        # Return if the user is not in the table
        if not user:
            return None
        
        if 'email' in data:
            user.username = data['email']
        if 'role' in data:
            user.role = data['role']
        if 'password' in data:
            user.set_password(data['password'])
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'phone' in data:
            user.phone = data['phone']

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