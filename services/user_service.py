from werkzeug.security import generate_password_hash, check_password_hash
from database import User

class UserService:
    def __init__(self, db_session):
        self.db_session = db_session

    def list_users(self):
        users = self.db_session.query(User).all()
        return [{'id': user.id, 'username': user.username, 'role': user.role} for user in users]

    def get_user_by_id(self, user_id):
        user = self.db_session.query(User).filter_by(id=user_id).first()
        if user:
            return {'id': user.id, 'username': user.username, 'role': user.role}
        return None

    def get_user_by_username(self, username):
        user = self.db_session.query(User).filter_by(username=username).first()
        return user

    def register_user(self, username, password, role='cleaner'):
        existing_user = self.get_user_by_username(username)
        if existing_user:
            return None, 'Username already exists'
        
        new_user = User(username=username, role=role)
        new_user.set_password(password)
        self.db_session.add(new_user)
        self.db_session.commit()
        return {'id': new_user.id, 'username': new_user.username, 'role': new_user.role}, None

    def authenticate_user(self, username, password):
        user = self.get_user_by_username(username)
        if user and check_password_hash(user.password_hash, password):
            return {'id': user.id, 'username': user.username, 'role': user.role}
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
        return {'id': user.id, 'username': user.username, 'role': user.role}

    def delete_user(self, user_id):
        user = self.db_session.query(User).filter_by(id=user_id).first()
        if not user:
            return False
        
        self.db_session.delete(user)
        self.db_session.commit()
        return True