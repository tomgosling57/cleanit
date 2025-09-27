from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, current_app, g, session
from werkzeug.security import check_password_hash
from database import User

# Create the user blueprint
user_bp = Blueprint('user', __name__, url_prefix='/users')

# This function will be called after each request, even if an exception occurs
@user_bp.teardown_request
def teardown_db(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def get_db():
    """Helper function to get or create a database connection for the current request."""
    if 'db' not in g:
        Session = current_app.config['SQLALCHEMY_SESSION']
        g.db = Session()
    return g.db

@user_bp.route('/')
def list_users():
    """List all users"""
    db = get_db()
    users = db.query(User).all()
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'role': user.role
    } for user in users])

@user_bp.route('/<int:user_id>')
def get_user(user_id):
    """Get a specific user by ID"""
    db = get_db()
    user = db.query(User).filter_by(id=user_id).first()
    if user:
        return jsonify({
            'id': user.id,
            'username': user.username,
            'role': user.role
        })
    else:
        return jsonify({'error': 'User not found'}), 404

@user_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'cleaner')
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('register.html')
        
        db = get_db()
        # Check if username already exists
        existing_user = db.query(User).filter_by(username=username).first()
        if existing_user:
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        # Create new user
        new_user = User(username=username, role=role)
        new_user.set_password(password)
        db.add(new_user)
        db.commit()
        
        flash('User registered successfully!', 'success')
        return redirect(url_for('user.login'))
    
    return render_template('register.html')

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        db = get_db()
        user = db.query(User).filter_by(username=username).first()
        _failed = False
        if not user: 
            _failed = True
        if not _failed and check_password_hash(user.password_hash, password):
            flash(f'Welcome back, {user.username}!', 'success')
            # Cache the cookie info
            session['user_id'] = user.id
            session['username'] = username
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@user_bp.route('/<int:user_id>/update', methods=['PUT'])
def update_user(user_id):
    """Update user information"""
    data = request.get_json()
    db = get_db()
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if 'username' in data:
        user.username = data['username']
    if 'role' in data:
        user.role = data['role']
    if 'password' in data:
        user.set_password(data['password'])
    
    db.commit()
    return jsonify({
        'id': user.id,
        'username': user.username,
        'role': user.role
    })

@user_bp.route('/<int:user_id>/delete', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user"""
    db = get_db()
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    db.delete(user)
    db.commit()
    return jsonify({'message': 'User deleted successfully'})
