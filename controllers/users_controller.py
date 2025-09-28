from flask import request, jsonify, render_template, redirect, url_for, flash, session
from database import get_db, teardown_db
from services.user_service import UserService

def list_users():
    """List all users"""
    db = get_db()
    user_service = UserService(db)
    try:
        users = user_service.list_users()
        return jsonify(users)
    except Exception as e:
        return jsonify({'error': 'Internal Server Error'}), 500
    finally:
        teardown_db()

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
    session_user_role = session.get('role')
    _return = redirect(url_for('user.login'))
    
    if session_user_role == 'owner' and request.method == 'POST':
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
    elif session_user_role == 'owner':
        _return = render_template('register.html')
    # If session user role is cleaner then redirect to index
    elif session_user_role == 'cleaner':
        _return = redirect(url_for('index'))

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
            flash(f'Welcome back, {user["username"]}!', 'success')
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            _return = redirect(url_for('index'))
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
        return jsonify(user), 200
    else:
        return jsonify({'error': 'User not found'}), 404

def delete_user(user_id):
    """Delete a user"""
    db = get_db()
    user_service = UserService(db)
    success = user_service.delete_user(user_id)
    teardown_db()
    if success:
        return jsonify({'message': 'User deleted successfully'})
    else:
        return jsonify({'error': 'User not found'}), 404