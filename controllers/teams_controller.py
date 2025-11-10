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
        teardown_db()
        return redirect(url_for('teams.get_teams'), code=303)

    teardown_db()
    return jsonify({'error': 'Team not found'}), 404

def create_team(team_data):
    if current_user.role not in ['owner']:
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    team_service = TeamService(db)
    team_service.create_team(team_data)

    teardown_db()
    return redirect(url_for('teams.get_teams'), code=303)

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
        {% include 'team_edit_modal_content.html' with context %}
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
        teardown_db()
        return render_template('team_list.html', teams=team_service.get_all_teams())

    teardown_db()
    return jsonify({'error': 'Team or User not found'}), 404