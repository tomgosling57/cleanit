from flask import render_template, render_template_string, redirect, url_for, flash, request, jsonify, Response
from flask_login import current_user
from services.team_service import TeamService
from services.user_service import UserService
from database import get_db, teardown_db

def get_teams():
    if current_user.role not in ['owner']:
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    team_service = TeamService(db)
    teams = team_service.get_all_teams()
    
    # Convert teams to serializable dictionaries
    teams_data = [team.to_dict() for team in teams]

    teardown_db()
    return jsonify(teams_data)
