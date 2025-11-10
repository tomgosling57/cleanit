from flask import request, jsonify, render_template, redirect, url_for, flash, session, abort, current_app
from utils.http import validate_request_host
from database import get_db, teardown_db
from services.user_service import UserService
from flask_login import login_user, current_user, fresh_login_required

def list_all_users_view():
    """List all users with their teams and roles for the owner view."""
    if not current_user.is_authenticated or current_user.role != 'owner':
        flash('Unauthorized access.', 'error')
        return redirect(url_for('job.timetable'))

    db = get_db()
    user_service = UserService(db)
    try:
        users = user_service.get_all_users()
        # Prepare data for rendering, including team names
        users_data = []
        for user in users:
            user_teams = [user.team.name] if user.team else []
            users_data.append({
                'username': user.username,
                'role': user.role,
                'teams': user_teams
            })
        return render_template('users.html', users=users_data)
    except Exception as e:
        current_app.logger.error(f"Error listing users: {e}")
        flash('An error occurred while fetching users.', 'error')
        return redirect(url_for('job.timetable'))
    finally:
        teardown_db()

def list_users():
    """List all users (API endpoint)"""
    db = get_db()
    user_service = UserService(db)
    try:
        users = user_service.get_all_users()
        users_data = [{
            'id': user.id,
            'username': user.username,
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

def register():
    """Register a new user"""    
    _return = redirect(url_for('user.login'))
    
    if current_user.role == 'owner' and request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'cleaner')
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('register.html')
        
        db = get_db()
        user_service = UserService(db)
        new_user, error = user_service.register_user(username, password, role)
        teardown_db()
        
        if error:
            flash(error, 'error')
            return render_template('register.html')
        
        flash('User registered successfully!', 'success')
    # If session role is owner and get request then rendered registered template
    elif current_user.role == 'owner':
        _return = render_template('register.html')
    # If session user role is cleaner then redirect to index
    elif current_user.role == 'cleaner':
        _return = redirect(url_for('job.timetable'))

    return _return

def login():
    """User login"""
    _return = render_template('login.html')
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        db = get_db()
        user_service = UserService(db)
        user = user_service.authenticate_user(username, password)
        teardown_db()
        
        if user:
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            next = request.args.get('next')
            if not validate_request_host(next, request.host, current_app.debug):
                _return = abort(400)
            _return = redirect(next or url_for('job.timetable')) # Redirect to job.timetable after successful login
        else:
            flash('Invalid username or password', 'error')
    
    return _return

def update_user(user_id):
    """Update user information"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid data provided'}), 400

    allowed_fields = ['username', 'password', 'role']
    if not any(field in data for field in allowed_fields):
        return jsonify({'error': 'No valid fields provided for update'}), 400

    db = get_db()
    user_service = UserService(db)
    user = user_service.update_user(user_id, data)
    teardown_db()
    if user:
        return redirect(url_for('user.list_all_users_view'), code=303)
    else:
        return jsonify({'error': 'User not found'}), 404

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
