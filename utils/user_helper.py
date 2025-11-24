
from services.user_service import UserService

class UserHelper:

    def __init__(self, session):
        self.session = session
        self.user_service = UserService(session)
    
    @staticmethod
    def clean_user_form_data(data, creation_form=False):
        _return = {
            'email': data.get('email'),
            'first_name': data.get('first_name'),
            'last_name': data.get('last_name'),
            'phone': data.get('phone'),
            'role': data.get('role'),
            'team_id': data.get('team_id')
        }
        if not creation_form:
            _return['id'] = data.get('id')
            _return['password'] = data.get('password')
        return _return
    
    def validate_user_form_data(self, data, force_names=False):
        """Validates the given form data for creating a user. 
        Returns a list of error messages if if there are missing fields.  

        First and last name will only be validated if force_names is True.
        
        Returns a list of errors or none"""
        errors = []
        if 'email' in data:
            if self.user_service.get_user_by_email(data['email']):
                errors.append('That email is already registered')            
        if 'email' not in data:
            errors.append('Missing email')
        
        if 'first_name' not in data and force_names:
            errors.append('Missing first name')

        if 'last_name' not in data and force_names:
            errors.append('Missing last name')
        
        if 'role' not in data:
            errors.append('Missing user role')

        # Return the error messages if the array is non empty
        if len(errors) > 0:
            return errors
        # Else return none
        return None
