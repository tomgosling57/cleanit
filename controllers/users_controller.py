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

    This function retrieves all users from the database, enriches their data with team information,
    and renders the 'users.html' template. Access is restricted to authenticated users with the 'owner' role.

    Returns:
        A rendered HTML component displaying all users and their details, or a JSON error if unauthorized.
    """
    if not current_user.is_authenticated or current_user.role != 'owner':
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    user_service = UserService(db)


    users = user_service.get_all_users()

    teardown_db()
    return render_template('users.html', users=users)


def get_user_update_password_form(user_id):
    """Renders the 'user_update_password_form.html'.
    
    Returns:
        A rendered HTML form."""
    if not current_user.is_authenticated or current_user.role != 'owner':
        return jsonify({'error': 'Unauthorized'}), 403
    db = get_db()
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    return render_template('user_update_password_form.html', user=user)


def update_user_password(user_id):
    """Updates the current user's password.
    
    Returns new password string or none"""
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
    if authenticated_user and new_password and new_password_confirmation and new_password == new_password_confirmation:
        user_service.change_user_password(authenticated_user, new_password)
        message = "Updated password successfully."
        user = authenticated_user
    elif not authenticated_user:
        errors = {'incorrect_password': 'The old password is incorrect.'}
    else:
        errors = {'password_confirmation': 'The new password and the confirmation did not match.'}    
    return render_template('_errors.html',  errors=errors if len(errors.keys()) > 0 else None, message=message, user=user)
    

def get_user_profile():
    """This function renders the 'user_update_form.html' template with the details of the current user.
    
    Returns:
        A rendered HTML page containing the current users details."""
    if not current_user.is_authenticated: 
        return jsonify({'error': 'Unauthorized'}), 403
    db = get_db()    
    user_service = UserService(db)
    roles = user_service.get_roles()
    return render_template('user_profile.html', user_profile=True, user=current_user, roles=roles)


def update_user_profile():
    """This function leverages _update_user to update the current user in the database and re render the update form with the updated details.
    
    Returns:
        A rendered HTML page containing the updated users details."""
    if not current_user.is_authenticated: 
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    user, errors = _update_user(current_user.id, db)    
    return render_template('user_update_form.html', user=user, errors=errors, user_profile=True, message="User updated successfully."), 200

def list_users():
    """API endpoint to list all users.

    Retrieves all users from the database and returns their ID, full name, role, and team ID.
    This endpoint is intended for API consumption.

    Returns:
        A JSON array of user data, or a JSON error if an internal server error occurs.
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
        A JSON object containing categorized user lists, or a JSON error if unauthorized.
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
        user_id: The unique identifier of the user to retrieve.

    Returns:
        A JSON object containing the user's data if found, or a JSON error if the user is not found or an internal server error occurs.
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
        A rendered HTML login page, a redirect response on successful login, or an abort(400) on invalid host.
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
        user_id: The unique identifier of the user to update.

    Returns:
        A rendered HTML form for user updates, or a JSON error if unauthorized.
    """
    if not current_user.is_authenticated:
        return jsonify({'error': 'Unauthorized'}), 403
    db = get_db()
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    roles = user_service.get_roles()
    return render_template('user_update_form.html', user=user, roles=roles)


def _update_user(user_id, db):
    """Updates the user in the database with the current form data.
    
    Args:
        user_id: The unique identifier of the user to update.
    
    Returns:
        The updated user object."""
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
        user_id: The unique identifier of the user to update.

    Returns:
        A rendered HTML user update form with errors, or a rendered user list fragment on success,
        or a JSON error if unauthorized or invalid data is provided.
    """
    if not current_user.is_authenticated:
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()    
    user, errors = _update_user(user_id, db)
    # Render errors to the UI
    if errors:
        # Return failure a HTTP status to prevent the javascript from closing the modal
        return render_template('_errors.html', errors=errors), 400
    
    if user:
        user_service = UserService(db)
        users = user_service.get_all_users()
        teardown_db()
        user_list_fragment = render_template('user_list_fragment.html', users=users)
        form_errors = render_template('_errors.html', message="User updated successfully.")
        return f"{user_list_fragment}\n{form_errors}"
    else:
        # Return failure a HTTP status to prevent the javascript from closing the modal
        return render_template('_errors.html', errors={'database_error':'User update failed'}), 500

def get_user_creation_form():
    """Renders the user creation form.

    This function retrieves available roles, then renders the 'user_creation_form.html' template.
    Access is restricted to authenticated users.

    Returns:
        A rendered HTML form for user creation, or a JSON error if unauthorized.
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
        A rendered HTML user creation form with errors, or a rendered user list fragment on success,
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
        return render_template('_errors.html', errors=errors), 400
    
    # Create the user in the database if there are no errors
    user, password = user_service.create_user(**data)
    if user:
        users = user_service.get_all_users()
        teardown_db()
        user_list_fragment = render_template('user_list_fragment.html', users=users)
        form_errors = render_template('_errors.html', copy_content=password, copy_content_name="password")
        return f"{user_list_fragment}\n{form_errors}"
    else:
        return render_template('_errors.html', errors={'database_error':'User update failed'}), 500

def delete_user(user_id):
    """Deletes a user from the database.

    This function attempts to delete a user identified by `user_id`.
    On successful deletion, it redirects to the 'user.list_all_users_view'.
    If the user is not found, it returns a JSON error.

    Args:
        user_id: The unique identifier of the user to delete.

    Returns:
        A redirect response on successful deletion, or a JSON error if the user is not found.
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
    form_errors = render_template('_errors.html', errors=errors)
    return f"{user_list_fragment}\n{form_errors}"