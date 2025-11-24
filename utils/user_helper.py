
from services.user_service import UserService

class UserHelper:
    """Helper class that performs form-related operations for the user controller.
    
    This class provides utility methods for cleaning and validating user form data,
    and interacts with the UserService for data persistence and retrieval.
    """

    def __init__(self, session):
        """Initializes the UserHelper with a database session.
        
        Args:
            session: The database session to be used by the user service.
        """
        self.session = session
        self.user_service = UserService(session)
    
    @staticmethod
    def clean_user_form_data(data, creation_form=False):
        """Cleans and extracts relevant user data from a form submission.
        
        Args:
            data: A dictionary containing the raw form data.
            creation_form: A boolean indicating if the data is for a new user creation form.

        Returns:
            A dictionary containing the cleaned user data.
        """
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
        
        Args:
            data: A dictionary containing the form data to validate.
            force_names: A boolean indicating if first and last names should be validated.

        Returns:
            A list of error messages if there are missing fields or validation fails, otherwise None.
        """
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
