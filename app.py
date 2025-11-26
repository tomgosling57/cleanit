from flask import request, url_for, Response, redirect
from database import get_db, teardown_db
from flask_login import LoginManager, current_user
from services.user_service import UserService
from app_factory import create_app

login_manager = LoginManager()
app = create_app(login_manager=login_manager)

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
    return redirect(url_for('job.timetable'))

if __name__ == '__main__':
    app.run(debug=True)
