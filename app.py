from flask import Flask, render_template, request, url_for, session, Response, redirect
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

@login_manager.unauthorized_handler
def unauthorized():
    # Check if this is an HTMX request
    if request.headers.get('HX-Request') == 'true':
        response = Response("Unauthorized", 401)
        response.headers['HX-Redirect'] = url_for('user.login')
        return response
    # Check if this is an AJAX request (X-Requested-With header)
    elif request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # For regular AJAX requests, return 401 with "Unauthorized" text
        return Response("Unauthorized", 401)
    # Check if this is a job status update endpoint (which should return 401 for AJAX)
    elif request.endpoint == 'job.update_job_status':
        # For job status updates, return 401 with "Unauthorized" text
        return Response("Unauthorized", 401)
    else:
        # For regular browser requests (page refreshes), redirect to login
        return redirect(url_for('user.login'))

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == "cleaner":
            return redirect(url_for('job.cleaner_jobs'))
        else:
            return redirect(url_for('job.manage_jobs'))
    return redirect(url_for('user.login'))

if __name__ == '__main__':
    app.run(debug=True)
