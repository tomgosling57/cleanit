from flask import render_template, render_template_string, redirect, url_for, flash, request, jsonify, Response
from flask_login import current_user
from services.team_service import TeamService
from services.user_service import UserService
from config import DATETIME_FORMATS


class TeamController:
    """Controller class for team-related operations with dependency injection."""
    
    def __init__(self, team_service: TeamService, user_service: UserService):
        """
        Initialize the controller with injected service dependencies.
        
        Args:
            team_service: Service for team operations
            user_service: Service for user operations
        """
        self.team_service = team_service
        self.user_service = user_service

    def get_teams(self):
        if current_user.role not in ['admin']:
            return render_template('unauthorized.html'), 403

        teams = self.team_service.get_all_teams()
        return render_template('teams.html', teams=teams, DATETIME_FORMATS=DATETIME_FORMATS)

    def get_team(self, team_id):
        if current_user.role not in ['admin']:
            return jsonify({'error': 'Unauthorized'}), 403

        team = self.team_service.get_team(team_id)

        if team:
            team_data = team.to_dict()
            return jsonify(team_data)

        return render_template('_form_response.html', errors={'Get Failed': 'Team not found'}), 404

    def delete_team(self, team_id):
        if current_user.role not in ['admin']:
            return jsonify({'error': 'Unauthorized'}), 403

        team = self.team_service.get_team(team_id)

        if team:
            self.team_service.delete_team(team)
            all_teams = self.team_service.get_all_teams()
            return render_template('team_list.html', teams=all_teams, DATETIME_FORMATS=DATETIME_FORMATS)
            
        # Use render_template_string to combine both templates
        all_teams = self.team_service.get_all_teams()
        
        return render_template_string(
            """
            {% include 'team_list.html' %}
            {% include '_form_response.html' %}
            """,
            teams=all_teams,
            errors={'Delete Failed': 'Team not found'},
            DATETIME_FORMATS=DATETIME_FORMATS
        ), 200

    def create_team(self):
        if current_user.role not in ['admin']:
            return jsonify({'error': 'Unauthorized'}), 403

        team_name = request.form.get('team_name')
        member_ids = request.form.getlist('members')
        team_leader_id = request.form.get('team_leader_id')

        team_data = {
            'name': team_name,
            'members': [int(mid) for mid in member_ids if mid],
            'team_leader_id': int(team_leader_id) if team_leader_id else None
        }

        self.team_service.create_team(team_data)

        all_teams = self.team_service.get_all_teams()
        response = Response(render_template('team_list.html', teams=all_teams, DATETIME_FORMATS=DATETIME_FORMATS))
        response.headers['HX-Trigger'] = 'teamListUpdated'
        return response

    def get_create_team_form(self):
        if current_user.role not in ['admin']:
            return jsonify({'error': 'Unauthorized'}), 403

        # Categorize all users for the create form (all will be unassigned or on different teams)
        categorized_users = self.user_service.get_users_relative_to_team(None)

        return render_template('team_create_modal.html', current_members=categorized_users['current_members'], 
                               other_team_members=categorized_users['other_team_members'], 
                               non_team_members=categorized_users['unassigned'], DATETIME_FORMATS=DATETIME_FORMATS)

    def get_edit_team_form(self, team_id):
        if current_user.role not in ['admin']:
            return jsonify({'error': 'Unauthorized'}), 403

        team = self.team_service.get_team(team_id)

        if not team:
            return jsonify({'error': 'Team not found'}), 404

        # Categorize all users for the create form (all will be unassigned or on different teams)
        categorized_users = self.user_service.get_users_relative_to_team(team.id)
        return render_template('team_edit_modal.html', current_members=categorized_users['current_members'], 
                               other_team_members=categorized_users['other_team_members'], 
                               non_team_members=categorized_users['unassigned'], DATETIME_FORMATS=DATETIME_FORMATS, team=team)

    def get_categorized_team_users(self, team_id):
        if current_user.role not in ['admin']:
            return jsonify({'error': 'Unauthorized'}), 403

        categorized_users = self.team_service.get_categorized_users_for_team(team_id)

        # Convert User objects to dictionaries for JSON serialization
        serialized_users = {
            category: [user.to_dict() for user in users]
            for category, users in categorized_users.items()
        }
        return jsonify(serialized_users)

    def edit_team(self, team_id):
        if current_user.role not in ['admin']:
            return jsonify({'error': 'Unauthorized'}), 403

        team_name = request.form.get('team_name')
        member_ids = request.form.getlist('members')
        team_leader_id = request.form.get('team_leader_id')

        updated_team = self.team_service.update_team_details(team_id, team_name, member_ids, team_leader_id)

        if not updated_team:
            return render_template('_form_response.html', errors={'Update Failed': 'Team not found or update failed'}), 404

        all_teams = self.team_service.get_all_teams()
        response = Response(render_template_string("{% include 'team_list.html' %}", teams=all_teams, DATETIME_FORMATS=DATETIME_FORMATS))
        response.headers['HX-Trigger'] = 'teamListUpdated'
        return response

    def add_team_member(self, team_id, user_id, old_team_id):
        if current_user.role not in ['admin']:
            return jsonify({'error': 'Unauthorized'}), 403

        user = self.team_service.add_team_member(team_id, user_id)
        if user:
            old_team = self.team_service.get_team(old_team_id)
            new_team = self.team_service.get_team(team_id)

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

            return jsonify({
                'success': True,
                'oldTeam': old_team_html,
                'newTeam': new_team_html
            }), 200
        if user:
            return jsonify({'success': True}), 200

        return render_template('_form_response.html', errors={'Delete Failed': 'Team or User not found'}), 404

    def remove_team_member(self, team_id, user_id):
        if current_user.role not in ['admin']:
            return jsonify({'error': 'Unauthorized'}), 403

        user = self.team_service.remove_team_member(team_id, user_id)

        if user:
            all_teams = self.team_service.get_all_teams()
            response = Response(render_template('team_list.html', teams=all_teams, DATETIME_FORMATS=DATETIME_FORMATS))
            response.headers['HX-Trigger'] = 'teamListUpdated'
            return response

        return render_template('_form_response.html', errors={'Delete Failed': 'Team or User not found'}), 404