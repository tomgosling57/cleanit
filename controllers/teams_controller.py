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

def add_team_member(team_id, user_id):
    if current_user.role not in ['owner']:
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    team_service = TeamService(db)
    user = team_service.add_team_member(team_id, user_id)

    if user:
        teardown_db()
        return redirect(url_for('teams.get_teams'), code=303)

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
        return redirect(url_for('teams.get_teams'), code=303)

    teardown_db()
    return jsonify({'error': 'Team or User not found'}), 404