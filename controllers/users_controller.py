import html
from flask import render_template_string, request, jsonify, render_template, redirect, url_for, flash, session, abort, current_app
from services.team_service import TeamService
from utils.http import validate_request_host
from database import get_db, teardown_db
from services.user_service import UserService
from flask_login import login_user, current_user, fresh_login_required

from utils.user_helper import UserHelper

def list_all_users_view():
    """Renders the user management page for owners.

    This function retrieves all users from the database and renders the 'users.html' template.
    Access is restricted to authenticated users with the 'owner' role.

    Returns:
        flask.Response: A rendered HTML component displaying all users and their details,
                        or a JSON error if unauthorized.
    """
    if not current_user.is_authenticated or current_user.role != 'owner':
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    user_service = UserService(db)


    users = user_service.get_all_users()

    teardown_db()
    return render_template('users.html', users=users)


def get_user_update_password_form(user_id):
    """Renders the user password update form.

    Args:
        user_id (int): The unique identifier of the user whose password is to be updated. Access is restricted to authenticated users.

    Returns:
        flask.Response: A rendered HTML form for updating the user's password,
                        or a JSON error if unauthorized.
    """
    if not current_user.is_authenticated:
        return jsonify({'error': 'Unauthorized'}), 403
    db = get_db()
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    return render_template('user_update_password_form.html', user=user, current_user=current_user)


def update_user_password(user_id):
    """Updates a user's password.

    This function handles the submission of the password update form. It validates the old password
    and ensures the new password and its confirmation match. If successful, the user's password
    is updated. Access is restricted to authenticated users.

    Args:
        user_id (int): The unique identifier of the user whose password is to be updated.

    Returns:
        flask.Response: A rendered HTML fragment displaying success or error messages,
                        or a JSON error if unauthorized or the user is not found.
    """
    if not current_user.is_authenticated:
        return jsonify({'error': 'Unauthorized'}), 403

    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    new_password_confirmation = request.form.get('new_password_confirmation')
    db = get_db()
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    errors = {}
    message = None
    if not user:
        return jsonify({'error': 'User not found'}), 404
    else:
        authenticated_user =  user_service.authenticate_user(user.email, old_password)
    if current_user.role == 'owner':
        # Owners can change password without old password
        authenticated_user = user        
    if authenticated_user and new_password and new_password_confirmation and new_password == new_password_confirmation:
        user_service.change_user_password(authenticated_user, new_password)
        message = "Updated password successfully."
        user = authenticated_user
    elif not authenticated_user:
        errors = {'incorrect_password': 'The old password is incorrect.'}
    else:
        errors = {'password_confirmation': 'The new password and the confirmation did not match.'}    
    return render_template('_form_response.html',  errors=errors if len(errors.keys()) > 0 else None, message=message, user=user)
    

def get_user_profile():
    """Renders the user profile page for the current authenticated user.

    This function retrieves the current user's details and available roles, then renders the
    'user_profile.html' template. Access is restricted to authenticated users.

    Returns:
        flask.Response: A rendered HTML page displaying the current user's profile,
                        or a JSON error if unauthorized.
    """
    if not current_user.is_authenticated: 
        return jsonify({'error': 'Unauthorized'}), 403
    db = get_db()    
    user_service = UserService(db)
    roles = user_service.get_roles()
    return render_template('user_profile.html', user_profile=True, user=current_user, roles=roles, current_user=current_user)


def update_user_profile():
    """Updates the current authenticated user's profile.

    This function processes form data to update the current user's details. It leverages the
    `_update_user` helper function for data cleaning, validation, and database update.
    On successful update, it re-renders the 'user_update_form.html' with the updated details.
    Access is restricted to authenticated users.

    Returns:
        flask.Response: A rendered HTML page containing the updated user's details,
                        or a JSON error if unauthorized.
    """
    if not current_user.is_authenticated: 
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    user, errors = _update_user(current_user.id, db)    
    return render_template('user_update_form.html', user=user, errors=errors, user_profile=True, message="User updated successfully."), 200

def list_users():
    """API endpoint to list all users.

    Retrieves all users from the database and returns their ID, full name, role, and team ID.
    This endpoint is is intended for API consumption.

    Returns:
        flask.Response: A JSON array of user data, or a JSON error if an internal server error occurs.
    """
    db = get_db()
    user_service = UserService(db)
    try:
        users = user_service.get_all_users()
        users_data = [{
            'id': user.id,
            'username': f"{user.first_name} {user.last_name}",
            'role': user.role,
            'team_id': user.team_id
        } for user in users]
        return jsonify(users_data)
    except Exception as e:
        current_app.logger.error(f"Error listing users via API: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500
    finally:
        teardown_db()

def get_all_categorized_users():
    """Retrieves all users categorized by their team assignment.

    This function fetches all users and categorizes them into 'on_this_team' (empty for new teams),
    'on_a_different_team', and 'unassigned'. Access is restricted to authenticated users with the 'owner' role.

    Returns:
        flask.Response: A JSON object containing categorized user lists, or a JSON error if unauthorized.
    """
    if current_user.role not in ['owner']:
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    user_service = UserService(db)
    all_users = user_service.get_all_users()
    teardown_db()

    categorized_users = {
        'on_this_team': [], # For a new team, no users are "on this team"
        'on_a_different_team': [user.to_dict() for user in all_users if user.team_id is not None],
        'unassigned': [user.to_dict() for user in all_users if user.team_id is None]
    }
    return jsonify(categorized_users)

def get_user(user_id):
    """Retrieves a specific user by their ID.

    Args:
        user_id (int): The unique identifier of the user to retrieve.

    Returns:
        flask.Response: A JSON object containing the user's data if found,
                        or a JSON error if the user is not found or an internal server error occurs.
    """
    db = get_db()
    user_service = UserService(db)
    try:
        user = user_service.get_user_by_id(user_id)
        if user:
            return jsonify(user)
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': 'Internal Server Error'}), 500
    finally:
        teardown_db()

def login():
    """Handles user login functionality.

    This function processes both GET and POST requests for user login.
    - GET: Renders the login form.
    - POST: Authenticates the user based on provided email and password. If successful,
            logs the user in, flashes a success message, and redirects to the 'job.timetable' page
            or a 'next' URL if provided and validated. If authentication fails, flashes an error message.

    Returns:
        flask.Response: A rendered HTML login page, a redirect response on successful login,
                        or an abort(400) on invalid host.
    """
    _return = render_template('login.html')
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        password = html.unescape(password)
        db = get_db()
        user_service = UserService(db)
        user = user_service.authenticate_user(email, password)
        teardown_db()
        
        if user:
            login_user(user)
            flash(f'Welcome back, {user.first_name}!', 'success')
            next = request.args.get('next')
            if not validate_request_host(next, request.host, current_app.debug):
                _return = abort(400)
            _return = redirect(next or url_for('job.timetable')) # Redirect to job.timetable after successful login
        else:
            flash('Invalid email or password', 'error')
    
    return _return

def get_user_update_form(user_id):
    """Renders the user update form for a specific user.

    This function retrieves the user details and available roles, then renders the 'user_update_form.html' template.
    Access is restricted to authenticated users.

    Args:
        user_id (int): The unique identifier of the user to update.

    Returns:
        flask.Response: A rendered HTML form for user updates, or a JSON error if unauthorized.
    """
    if not current_user.is_authenticated:
        return jsonify({'error': 'Unauthorized'}), 403
    db = get_db()
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    roles = user_service.get_roles()
    return render_template('user_update_form.html', user=user, roles=roles, current_user=current_user)


def _update_user(user_id, db):
    """Helper function to update a user in the database with the current form data.

    This function cleans and validates the form data before attempting to update the user.

    Args:
        user_id (int): The unique identifier of the user to update.
        db: The database connection object.

    Returns:
        tuple: A tuple containing the updated user object and a dictionary of errors (if any).
    """
    data = request.form.to_dict()
    if not data:
        return jsonify({'error': 'Invalid data provided'}), 400

    # Clean the user form data and handle errors    
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    user_helper = UserHelper(db)
    data = user_helper.clean_user_form_data(data)
    errors = user_helper.validate_user_form_data(data)
    # Update the database if there are no errors
    return user_service.update_user(user_id, data), errors


def update_user(user_id):
    """Updates an existing user's details in the database.

    This function processes form data to update a user. It cleans and validates the input data.
    If there are validation errors, it re-renders the update form with error messages.
    On successful update, it renders the 'user_list_fragment' with the updated list of users.
    Access is restricted to authenticated users.

    Args:
        user_id (int): The unique identifier of the user to update.

    Returns:
        flask.Response: A rendered HTML user update form with errors, or a rendered user list fragment on success,
                        or a JSON error if unauthorized or invalid data is provided.
    """
    if not current_user.is_authenticated:
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()    
    user, errors = _update_user(user_id, db)
    # Render errors to the UI
    if errors:
        # Return failure a HTTP status to prevent the javascript from closing the modal
        return render_template('_form_response.html', errors=errors), 400
    
    if user:
        user_service = UserService(db)
        users = user_service.get_all_users()
        teardown_db()
        user_list_fragment = render_template('user_list_fragment.html', users=users)
        form_response = render_template('_form_response.html', message="User updated successfully.")
        return f"{user_list_fragment}\n{form_response}"
    else:
        # Return failure a HTTP status to prevent the javascript from closing the modal
        return render_template('_form_response.html', errors={'database_error':'User update failed'}), 500

def get_user_creation_form():
    """Renders the user creation form.

    This function retrieves available roles, then renders the 'user_creation_form.html' template.
    Access is restricted to authenticated users.

    Returns:
        flask.Response: A rendered HTML form for user creation, or a JSON error if unauthorized.
    """
    if not current_user.is_authenticated:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db = get_db()
    user_service = UserService(db)
    roles = user_service.get_roles()
    return render_template('user_creation_form.html', roles=roles)

def create_user():
    """Creates a new user in the database.

    This function processes form data to create a new user. It cleans and validates the input data,
    ensuring first and last names are present. If there are validation errors, it re-renders the
    creation form with error messages. On successful creation, it renders the 'user_list_fragment.html'
    with the updated list of users. Access is restricted to authenticated users.

    Returns:
        flask.Response: A rendered HTML user creation form with errors, or a rendered user list fragment on success,
                        or a JSON error if unauthorized or invalid data is provided.
    """
    if not current_user.is_authenticated:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.form.to_dict()
    if not data:
        # Return failure a HTTP status to prevent the javascript from closing the modal
        return jsonify({'error': 'Invalid data provided'}), 400

    # Clean the user form data and handle errors
    db = get_db()
    user_service = UserService(db)
    user_helper = UserHelper(db)
    # Extract and validate user attributes from form data
    data = user_helper.clean_user_form_data(data, creation_form=True) 
    errors = user_helper.validate_user_form_data(data, creation_form=True)
    # Render errors to the UI
    if errors:
        # Return failure a HTTP status to prevent the javascript from closing the modal
        return render_template('_form_response.html', errors=errors), 400
    
    # Create the user in the database if there are no errors
    user, password = user_service.create_user(**data)
    if user:
        users = user_service.get_all_users()
        teardown_db()
        user_list_fragment = render_template('user_list_fragment.html', users=users)
        form_response = render_template('_form_response.html', copy_content=password, copy_content_name="password")
        return f"{user_list_fragment}\n{form_response}"
    else:
        return render_template('_form_response.html', errors={'database_error':'User update failed'}), 500

def delete_user(user_id):
    """Deletes a user from the database.

    This function attempts to delete a user identified by `user_id`.
    On successful deletion, it renders the 'user_list_fragment' with the updated list of users.
    If the user is not found or deletion fails, it renders an error message.

    Args:
        user_id (int): The unique identifier of the user to delete.

    Returns:
        flask.Response: A rendered HTML fragment displaying the updated user list and any error messages.
    """
    db = get_db()
    user_service = UserService(db)
    success = user_service.delete_user(user_id)
    users = user_service.get_all_users()
    teardown_db()
    errors = None
    if not success:
        errors = {'delete_user': 'Failed to delete user'}
    user_list_fragment = render_template('user_list_fragment.html', users=users)
    form_response = render_template('_form_response.html', errors=errors)
    return f"{user_list_fragment}\n{form_response}"