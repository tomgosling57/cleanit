
from flask import Blueprint, request, jsonify, render_template
from database import teardown_db
from flask_login import login_required, current_user
from controllers import teams_controller

teams_bp = Blueprint('teams', __name__, url_prefix='/teams')

@teams_bp.teardown_request
def teardown_job_db(exception=None):
    teardown_db(exception)

@teams_bp.route('/', methods=['GET'])
@login_required
def get_teams():
    return teams_controller.get_teams()

@teams_bp.route('/<int:team_id>', methods=['GET'])
@login_required
def get_team(team_id):
    return teams_controller.get_team(team_id)

@teams_bp.route('/<int:team_id>', methods=['DELETE'])
@login_required
def delete_team(team_id):
    return teams_controller.delete_team(team_id)

@teams_bp.route('/', methods=['POST'])
@login_required
def create_team():
    team_data = request.get_json()
    return teams_controller.create_team(team_data)