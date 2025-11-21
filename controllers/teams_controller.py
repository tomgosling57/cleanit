from flask import render_template, render_template_string, redirect, url_for, flash, request, jsonify, Response
from flask_login import current_user
from services.team_service import TeamService
from services.user_service import UserService
from database import get_db, teardown_db

def get_teams():
    if current_user.role not in ['owner']:
        return render_template('unauthorized.html'), 403

    db = get_db()
    team_service = TeamService(db)
    teams = team_service.get_all_teams()

    teardown_db()
    return render_template('teams.html', teams=teams)

def get_team(team_id):
    if current_user.role not in ['owner']:
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    team_service = TeamService(db)
    team = team_service.get_team(team_id)

    if team:
        team_data = team.to_dict()
        teardown_db()
        return jsonify(team_data)

    teardown_db()
    return jsonify({'error': 'Team not found'}), 404

def delete_team(team_id):
    if current_user.role not in ['owner']:
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    team_service = TeamService(db)
    team = team_service.get_team(team_id)

    if team:
        team_service.delete_team(team)
        all_teams = team_service.get_all_teams()
        teardown_db()
        response = Response(render_template_string(''))
        response.headers['HX-Trigger'] = 'teamListUpdated'
        return response

    teardown_db()
    return jsonify({'error': 'Team not found'}), 404

def create_team():
    if current_user.role not in ['owner']:
        return jsonify({'error': 'Unauthorized'}), 403

    team_name = request.form.get('team_name')
    member_ids = request.form.getlist('members')
    team_leader_id = request.form.get('team_leader_id')

    team_data = {
        'name': team_name,
        'members': [int(mid) for mid in member_ids if mid],
        'team_leader_id': int(team_leader_id) if team_leader_id else None
    }

    db = get_db()
    team_service = TeamService(db)
    team_service.create_team(team_data)

    all_teams = team_service.get_all_teams()
    teardown_db()
    response = Response(render_template('team_list.html', teams=all_teams))
    response.headers['HX-Trigger'] = 'teamListUpdated'
    return response

def get_create_team_form():
    if current_user.role not in ['owner']:
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    user_service = UserService(db)
    all_users = user_service.get_all_users()
    teardown_db()

    # Categorize all users for the create form (all will be unassigned or on different teams)
    categorized_users = {
        'on_this_team': [], # No users on "this team" for a new team
        'on_a_different_team': [user for user in all_users if user.team_id is not None],
        'unassigned': [user for user in all_users if user.team_id is None]
    }

    return render_template_string(
        """
        {% include 'team_create_modal.html' with context %}
        """,
        categorized_users=categorized_users
    )

def get_edit_team_form(team_id):
    if current_user.role not in ['owner']:
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    team_service = TeamService(db)
    team = team_service.get_team(team_id)

    if not team:
        teardown_db()
        return jsonify({'error': 'Team not found'}), 404

    teardown_db()
    return render_template_string(
        """
        {% include 'team_edit_modal.html' with context %}
        """,
        team=team
    )

def get_categorized_team_users(team_id):
    if current_user.role not in ['owner']:
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    team_service = TeamService(db)
    categorized_users = team_service.get_categorized_users_for_team(team_id)
    teardown_db()

    # Convert User objects to dictionaries for JSON serialization
    serialized_users = {
        category: [user.to_dict() for user in users]
        for category, users in categorized_users.items()
    }
    return jsonify(serialized_users)


def edit_team(team_id):
    if current_user.role not in ['owner']:
        return jsonify({'error': 'Unauthorized'}), 403

    team_name = request.form.get('team_name')
    member_ids = request.form.getlist('members')
    team_leader_id = request.form.get('team_leader_id')

    db = get_db()
    team_service = TeamService(db)
    user_service = UserService(db)

    updated_team = team_service.update_team_details(team_id, team_name, member_ids, team_leader_id)

    if not updated_team:
        teardown_db()
        return jsonify({'error': 'Team not found or update failed'}), 404

    all_teams = team_service.get_all_teams()
    teardown_db()
    response = Response(render_template_string("{% include 'team_list.html' %}", teams=all_teams))
    response.headers['HX-Trigger'] = 'teamListUpdated'
    return response

def add_team_member(team_id, user_id, old_team_id):
    if current_user.role not in ['owner']:
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    team_service = TeamService(db)
    user = team_service.add_team_member(team_id, user_id)
    if user:
        old_team = team_service.get_team(old_team_id)
        new_team = team_service.get_team(team_id)

        old_team_html = render_template_string(
            """
            {% include 'team_card.html' with context %}
            """,
            team=old_team
        ) if old_team else None

        new_team_html = render_template_string(
            """
            {% include 'team_card.html' with context %}
            """,
            team=new_team
        ) if new_team else None

        teardown_db()
        return jsonify({
            'success': True,
            'oldTeam': old_team_html,
            'newTeam': new_team_html
        }), 200
    if user:
        teardown_db()
        return jsonify({'success': True}), 200

    teardown_db()
    return jsonify({'error': 'Team or User not found'}), 404

def remove_team_member(team_id, user_id):
    if current_user.role not in ['owner']:
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    team_service = TeamService(db)
    user = team_service.remove_team_member(team_id, user_id)

    if user:
        all_teams = team_service.get_all_teams()
        teardown_db()
        response = Response(render_template('team_list.html', teams=all_teams))
        response.headers['HX-Trigger'] = 'teamListUpdated'
        return response

    teardown_db()
    return jsonify({'error': 'Team or User not found'}), 404