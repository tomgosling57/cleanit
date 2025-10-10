
from flask import Blueprint, request, jsonify, render_template
from database import db_session, teardown_db
from flask_login import login_required, current_user
from controllers import teams_controller

teams_bp = Blueprint('teams', __name__)

@teams_bp.teardown_request
def teardown_request(exception=None):
    teams_controller.teardown_db(exception)