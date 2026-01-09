from flask import Blueprint, request, render_template
from flask_login import login_required
from controllers.teams_controller import TeamController
from database import teardown_db, get_db
from services.team_service import TeamService
from services.user_service import UserService

teams_bp = Blueprint('teams', __name__, url_prefix='/teams')

@teams_bp.teardown_request
def teardown_team_db(exception=None):
    teardown_db(exception)

def get_team_controller():
    """Create and return a TeamController instance with request-level database session."""
    db_session = get_db()
    team_service = TeamService(db_session)
    user_service = UserService(db_session)
    controller = TeamController(
        team_service=team_service,
        user_service=user_service
    )
    return controller

@teams_bp.route('/')
@login_required
def teams():
    controller = get_team_controller()
    return controller.get_teams()

@teams_bp.route('/team/<int:team_id>/edit_form', methods=['GET'])
@login_required
def get_edit_team_form(team_id):
    controller = get_team_controller()
    return controller.get_edit_team_form(team_id)

@teams_bp.route('/team/<int:team_id>/details', methods=['GET'])
@login_required
def get_team_details(team_id):
    controller = get_team_controller()
    return controller.get_team(team_id)

@teams_bp.route('/team/<int:team_id>/categorized_users', methods=['GET'])
@login_required
def get_categorized_users(team_id):
    controller = get_team_controller()
    return controller.get_categorized_team_users(team_id)

@teams_bp.route('/create_form', methods=['GET'])
@login_required
def get_create_team_form():
    controller = get_team_controller()
    return controller.get_create_team_form()

@teams_bp.route('/create', methods=['POST'])
@login_required
def create_team():
    controller = get_team_controller()
    return controller.create_team()

@teams_bp.route('/team/<int:team_id>/edit', methods=['POST'])
@login_required
def edit_team(team_id):
    controller = get_team_controller()
    return controller.edit_team(team_id)

@teams_bp.route('/team/<int:team_id>/delete', methods=['DELETE'])
@login_required
def delete_team(team_id):
    controller = get_team_controller()
    return controller.delete_team(team_id)

@teams_bp.route('/team/<int:team_id>/member/add', methods=['POST'])
@login_required
def add_team_member(team_id):
    user_id = request.json.get('user_id')
    old_team_id = request.json.get('old_team_id')
    controller = get_team_controller()
    return controller.add_team_member(team_id, user_id, old_team_id)

@teams_bp.route('/team/<int:team_id>/member/remove/<int:user_id>', methods=['DELETE'])
@login_required
def remove_team_member(team_id, user_id):
    controller = get_team_controller()
    return controller.remove_team_member(team_id, user_id)