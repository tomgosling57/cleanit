# app_factory.py
import os
import secrets
from flask import Flask, redirect, url_for, request, Response
from flask_login import LoginManager
from database import init_db, create_initial_users, create_initial_property_and_job, create_initial_team, get_db, teardown_db
from routes.users import user_bp
from routes.jobs import job_bp
from routes.teams import teams_bp
from routes.properties import properties_bp
from services.user_service import UserService

def create_app(login_manager=LoginManager(), test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    secret_key = test_config.get('SECRET_KEY') if test_config and 'SECRET_KEY' in test_config else secrets.token_bytes(32)
    app.config.from_mapping(
        SECRET_KEY=secret_key,
        DATABASE=os.path.join(app.instance_path, 'cleanit.db'),
        SQLALCHEMY_DATABASE_URI=f'sqlite:///{os.path.join(app.instance_path, "cleanit.db")}',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    
    if test_config is not None:
        app.config.update(test_config)
    
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    Session = init_db(app, app.config['DATABASE'])
    create_initial_users(Session)
    create_initial_team(Session)
    create_initial_property_and_job(Session)
    app.config['SQLALCHEMY_SESSION'] = Session
    
    login_manager.login_view = 'user.login'
    login_manager.init_app(app)
    
    # MOVE THESE HERE:
    @login_manager.user_loader
    def load_user(user_id):
        _return = UserService(get_db()).get_user_by_id(user_id)
        teardown_db()
        return _return
    
    @login_manager.unauthorized_handler
    def unauthorized():
        if request.headers.get('HX-Request') == 'true':
            response = Response("Unauthorized", 401)
            response.headers['HX-Redirect'] = url_for('user.login')
            return response
        elif request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return Response("Unauthorized", 401)
        elif request.endpoint == 'job.update_job_status':
            return Response("Unauthorized", 401)
        else:
            return redirect(url_for('user.login'))
    
    @app.route('/')
    def index():
        return redirect(url_for('user.login'))
    
    app.register_blueprint(user_bp)
    app.register_blueprint(job_bp)
    app.register_blueprint(teams_bp)
    app.register_blueprint(properties_bp)
    
    return app