from werkzeug.security import check_password_hash
from database import User
from sqlalchemy.orm import joinedload
from utils.password_generator import generate_password_with_requirements

class UserService:
    def __init__(self, db_session):
        self.db_session = db_session

    def get_all_users(self):
        """Gets all users from the User table.
        
        Returns:
            A list of User objects
        """
        users = self.db_session.query(User).options(joinedload(User.team)).all()
        return users

    def get_users_by_role(self, role):
        """Gets users from the User table filtering by role.
        
        Returns:
            A list of User objects
        """
        users = self.db_session.query(User).filter_by(role=role).all()
        return users

    def get_user_by_id(self, user_id):
        """Gets a user from the User table with the given id.
        
        Returns:
            A User object or None
        """
        user = self.db_session.query(User).filter_by(id=user_id).first()
        return user

    def get_user_by_email(self, email):
        """Get a user from the User table with the given email.
        
        Returns:
            A User object or none
        """
        user = self.db_session.query(User).filter_by(email=email).first()
        return user

    def get_roles(self):
        """Gets the unique values for role from the User table.
        
        Returns:
            A list of strings
        """
        roles = self.db_session.query(User.role).distinct().all()
        roles = [''.join(role) for role in roles]
        return roles

    def authenticate_user(self, email, password):
        """Authenticate a user within the User table via email and password.
 
        Returns:
            User object or None
        """
        user = self.get_user_by_email(email)
        if user and check_password_hash(user.password_hash, password):
            return user
        return None

    def _create_user(self, first_name: str, last_name: str, email: str, password: str, role:str, phone:str=None, team_id: int=None):
        """Create a user within the user table with the given attributes. The email attribute must be unique.
        The password will be hashed internally before it is stored in the table. Returns none if the email is not unique.
        
        Args:
            first_name: The first name of the user.
            last_name: The last name of the user.
            email: The email of the user (must be unique).
            password: The plain text password for the user.
            role: The role of the user.
            phone: The phone number of the user (optional).
            team_id: The ID of the team the user belongs to (optional).

        Returns:
            The Created User object or None if the email is not unique.
        """
        existing_user = self.db_session.query(User).filter_by(email=email).first()

        # Return none if the email is not unique
        if existing_user:
            return None
        
        new_user = User(first_name=first_name, last_name=last_name, email=email, phone=phone, role=role, team_id=team_id)
        new_user.set_password(password)
        self.db_session.add(new_user)
        self.db_session.commit()
        self.db_session.refresh(new_user)
        return new_user

    def create_user(self, first_name: str, last_name: str, email: str, role:str, phone:str=None, team_id: int=None):
        """Creates a user in the database with a randomly generated password.
        
        Args:
            first_name: The first name of the user.
            last_name: The last name of the user.
            email: The email of the user.
            role: The role of the user.
            phone: The phone number of the user (optional).
            team_id: The ID of the team the user belongs to (optional).

        Returns:
            A tuple containing the User object and the generated password string.
        """
        password = generate_password_with_requirements()
        new_user = self._create_user(first_name=first_name, last_name=last_name, email=email, password=password, phone=phone, role=role, team_id=team_id)
        return new_user, password
    
    def update_user(self, user_id, data):
        """Update a user within the User table with the given data.
        
        Args:
            user_id: The ID of the user to update.
            data: A dictionary containing the fields to update (e.g., 'email', 'role', 'password').

        Returns:
            The updated User object or None if the user is not found.
        """
        user = self.db_session.query(User).filter_by(id=user_id).first()

        # Return if the user is not in the table
        if not user:
            return None
        
        if data.get('email'):
            user.email = data['email']
        if data.get('role'):
            user.role = data['role']
        if data.get('password'):
            user.set_password(data['password'])
        if data.get('first_name'):
            user.first_name = data['first_name']
        if data.get('last_name'):
            user.last_name = data['last_name']
        if data.get('phone'):
            user.phone = data['phone']

        self.db_session.commit()
        return user

    def delete_user(self, user_id):
        """Deletes the user from the User table with the given id.
        
        Args:
            user_id: The ID of the user to delete.

        Returns:
            True if the user was successfully deleted, False otherwise.
        """
        user = self.db_session.query(User).filter_by(id=user_id).first()
        if not user:
            return False
        
        self.db_session.delete(user)
        self.db_session.commit()
        return True

    def remove_team_from_users(self, team_id):
        """Removes the given team_id from all of the User objects within the User table.
        
        Args:
            team_id: The ID of the team to remove from users.

        Returns:
            None
        """
        users = self.db_session.query(User).filter_by(team_id=team_id).all()
        for user in users:
            user.team_id = None
        self.db_session.commit()

    def change_user_password(self, user: User, password: str):
        """Changes the password for the given user.
        
        Args:
            user: The User object to change the password for.
            password: The new plain text password.

        Returns:
            None
        """
        user.set_password(password)
        self.db_session.commit()
    
    def get_users_relative_to_team(self, team_id=None):
        """Gets users categorized by their relation to the given team_id.
        
        Args:
            team_id: The ID of the team to categorize users by.

        Returns:
            A dictionary with keys 'current_members', 'other_team_members', and 'unassigned' containing lists of User objects.
        """
        all_users = self.get_all_users()
        categorized_users = {
            'current_members': [user for user in all_users if user.team_id == team_id and team_id is not None],
            'other_team_members': [user for user in all_users if user.team_id is not None and user.team_id != team_id],
            'unassigned': [user for user in all_users if user.team_id is None]
        }
        return categorized_users