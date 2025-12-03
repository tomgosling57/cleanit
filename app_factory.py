# app_factory.py
import os
import secrets
from flask import Flask, redirect, url_for, request, Response
from flask_login import LoginManager
from config import Config, TestConfig
from database import init_db, get_db, teardown_db
from routes.users import user_bp
from routes.jobs import job_bp
from routes.teams import teams_bp
from routes.properties import properties_bp
from services.user_service import UserService

def create_app(login_manager=LoginManager(), test_config=None):
    """
    Creates and configures the Flask application.

    Args:
        login_manager (LoginManager, optional): The Flask-Login manager instance.
                                               Defaults to a new LoginManager().
        test_config (dict, optional): A dictionary of configuration overrides for testing.
                                      Defaults to None.

    Returns:
        Flask: The configured Flask application instance.
    """
    app = Flask(__name__, instance_relative_config=True)
    if test_config:
        app.config.from_object(TestConfig)
        app.config.update(test_config) # Apply additional test config overrides

        try: # Ensure the instance directory exists
            os.makedirs(app.instance_path)
        except OSError:
            pass
    else: 
        app.config.from_object(Config)
    
    Session = init_db(app.config['DATABASE'])
    app.config['SQLALCHEMY_SESSION'] = Session
    
    login_manager.login_view = 'user.login'
    login_manager.init_app(app)
    
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