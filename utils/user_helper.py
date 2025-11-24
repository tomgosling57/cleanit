
from services.user_service import UserService

class UserHelper:
    """! @brief Helper class that performs form-related operations for the user controller.
    
    This class provides utility methods for cleaning and validating user form data,
    and interacts with the UserService for data persistence and retrieval.
    """

    def __init__(self, session):
        """! @brief Initializes the UserHelper with a database session.
        @param session The database session to be used by the user service.
        """
        self.session = session
        self.user_service = UserService(session)
    
    @staticmethod
    def clean_user_form_data(data, creation_form=False):
        """! @brief Cleans and extracts relevant user data from a form submission.
        @param data A dictionary containing the raw form data.
        @param creation_form A boolean indicating if the data is for a new user creation form.
        @return A dictionary containing the cleaned user data.
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
        """! @brief Validates the given form data for creating a user.
        @param data A dictionary containing the form data to validate.
        @param force_names A boolean indicating if first and last names should be validated.
        @return A list of error messages if there are missing fields or validation fails, otherwise None.
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
