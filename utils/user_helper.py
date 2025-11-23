
from services.user_service import UserService
from utils.password_generator import generate_strong_password

class UserHelper:

    def __init__(self, session):
        self.session = session
        self.user_service = UserService(session)
    
    @staticmethod
    def _extract_user_form_data(data):
        _return = {
            'id': data.get('id'),
            'email': data.get('email'),
            'first_name': data.get('first_name'),
            'last_name': data.get('last_name'),
            'password': data.get('password'),
            'phone': data.get('phone'),
            'role': data.get('role'),
            'team_id': data.get('team_id')
        }
        return _return

    def create_user(self, data):
        errors = []
        
        if 'password' not in data:
            data['password'] = generate_strong_password()

        user = self.user_service.create_user(data)

    def validate_create_user_data(self, data):
        """Validates the given form data for creating a user.
        
        Returns a list of errors or none"""
        errors = []
        if 'email' in data:
            if self.user_service.get_user_by_email(data['email']):
                errors.append('That email is already registered')            
        if 'email' not in data:
            errors.append('Missing email')
        
        if 'first_name' not in data:
            errors.append('Missing first name')

        if 'last_name' not in data:
            errors.append('Missing last name')
        
        if 'role' not in data:
            errors.append('Missing user role')

        # Return the error messages if the array is non empty
        if len(errors) > 0:
            return errors
        # Else return none
        return None
