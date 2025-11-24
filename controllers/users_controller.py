from flask import request, jsonify, render_template, redirect, url_for, flash, session, abort, current_app
from services.team_service import TeamService
from utils.http import validate_request_host
from database import get_db, teardown_db
from services.user_service import UserService
from flask_login import login_user, current_user, fresh_login_required

from utils.user_helper import UserHelper

def list_all_users_view():
    """List all users with their teams and roles for the owner view."""
    if not current_user.is_authenticated or current_user.role != 'owner':
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    user_service = UserService(db)


    users = user_service.get_all_users()
    # Prepare data for rendering, including team names
    users_data = []
    for user in users:
        user_teams = [user.team.name] if user.team else []
        users_data.append({
            'username': f"{user.first_name} {user.last_name}",
            'role': user.role,
            'teams': user_teams
        })
    teardown_db()
    return render_template('users.html', users=users_data)

def list_users():
    """List all users (API endpoint)"""
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
    """Get a specific user by ID"""
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
    """User login"""
    _return = render_template('login.html')
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
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
    """Renders the update form for the given user id."""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db = get_db()
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    roles = user_service.get_roles()
    return render_template('user_update_form.html', user=user, roles=roles)

def update_user(user_id):
    """Update user details in the database."""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.form.to_dict()
    if not data:
        return jsonify({'error': 'Invalid data provided'}), 400

    # Clean the user form data and handle errors
    db = get_db()
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    user_helper = UserHelper(db)
    data = user_helper.clean_user_form_data(data)
    errors = user_helper.validate_user_form_data(data)
    # Render errors to the UI
    if errors:
        return render_template('user_update_form.html', user=user, errors=errors)
    
    # Update the database if there are no errors
    user = user_service.update_user(user_id, data)
    if user:
        users = user_service.get_all_users()
        teardown_db()
        return render_template('user_list_fragment', users=users)
    else:
        return render_template('user_update_form.html', user=user, errors=['User update failed.'])

def get_user_creation_form(user_id):
    """Renders the update form for the given user id."""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db = get_db()
    user_service = UserService(db)
    team_service = TeamService(db)
    roles = user_service.get_roles()
    teams = team_service.get_all_teams()
    return render_template('user_creation_form.html', roles=roles, teams=teams)

def create_user(user_id):
    """Create user in the database."""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.form.to_dict()
    if not data:
        return jsonify({'error': 'Invalid data provided'}), 400

    # Clean the user form data and handle errors
    db = get_db()
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    user_helper = UserHelper(db)
    # Extract and validate user attributes from form data
    data = user_helper.clean_user_form_data(data) 
    # Validate with force_names=True to make sure first and last names are presentp
    errors = user_helper.validate_user_form_data(data, force_names=True)
    # Render errors to the UI
    if errors:
        return render_template('user_creation_form.html', user=user, errors=errors)
    
    # Create the user in the database if there are no errors
    user, password = user_service.create_user(**data)
    if user:
        users = user_service.get_all_users()
        teardown_db()
        return render_template('user_list_fragment', users=users)
    else:
        return render_template('user_creation_form.html', user=user, errors=['User update failed.'])

def delete_user(user_id):
    """Delete a user"""
    db = get_db()
    user_service = UserService(db)
    success = user_service.delete_user(user_id)
    teardown_db()
    if success:
        return redirect(url_for('user.list_all_users_view'), code=303)
    else:
        return jsonify({'error': 'User not found'}), 404
