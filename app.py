from flask import Flask, render_template, request, redirect, url_for, session
import os
from database import init_db, create_initial_owner, create_initial_cleaner, create_initial_property_and_job, get_db, teardown_db
from routes.users import user_bp
from routes.jobs import job_bp
import secrets
from flask_login import LoginManager, current_user
from services.user_service import UserService
app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'user.login'
# TODO: Remove random secret
app.config['SECRET_KEY'] = secrets.token_bytes(32)

# Create the 'instance' folder if it doesn't exist
instance_path = os.path.join(app.root_path, 'instance')
os.makedirs(instance_path, exist_ok=True)

# Initialize the database and create an initial owner
Session = init_db(app)
create_initial_owner(Session)
create_initial_cleaner(Session)
create_initial_property_and_job(Session)
app.config['SQLALCHEMY_SESSION'] = Session

# Register blueprints
app.register_blueprint(user_bp)
app.register_blueprint(job_bp)

@login_manager.user_loader
def load_user(user_id):
    _return = UserService(get_db()).get_user_by_id(user_id)
    teardown_db()
    return _return

@app.route('/')
def index():
    welcome_message = "Welcome to CleanIt! Database initialized. <a href='/users/'>View Users</a>"
    if current_user.is_authenticated:
        welcome_message = f"Welcome to CleanIt, {current_user.username}! Database initialized. <a href='/users/'>View Users</a>"
    return welcome_message

if __name__ == '__main__':
    app.run(debug=True)
