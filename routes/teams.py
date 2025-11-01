from flask import Blueprint, request
from flask_login import login_required
from controllers import teams_controller
from database import teardown_db

teams_bp = Blueprint('teams', __name__, url_prefix='/teams')

@teams_bp.teardown_request
def teardown_team_db(exception=None):
    teardown_db(exception)

@teams_bp.route('/')
@login_required
def teams():
    return teams_controller.get_teams()

@teams_bp.route('/team/<int:team_id>/details', methods=['GET'])
@login_required
def get_team_details(team_id):
    return teams_controller.get_team(team_id)

@teams_bp.route('/team/create', methods=['POST'])
@login_required
def create_team():
    team_data = request.get_json()
    return teams_controller.create_team(team_data)

@teams_bp.route('/team/<int:team_id>/delete', methods=['DELETE'])
@login_required
def delete_team(team_id):
    return teams_controller.delete_team(team_id)

@teams_bp.route('/team/<int:team_id>/member/add', methods=['POST'])
@login_required
def add_team_member(team_id):
    user_id = request.json.get('user_id')
    return teams_controller.add_team_member(team_id, user_id)

@teams_bp.route('/team/<int:team_id>/member/remove', methods=['DELETE'])
@login_required
def remove_team_member(team_id):
    user_id = request.json.get('user_id')
    return teams_controller.remove_team_member(team_id, user_id)