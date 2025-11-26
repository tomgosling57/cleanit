import os
import secrets
from flask.app import Flask
from flask_login.login_manager import LoginManager
from database import init_db, create_initial_users, create_initial_property_and_job, create_initial_team
from routes.users import user_bp
from routes.jobs import job_bp
from routes.teams import teams_bp
from routes.properties import properties_bp

def create_app(login_manager=LoginManager(), test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=secrets.token_hex(16),
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

    app.config['SECRET_KEY'] = secrets.token_bytes(32)

    app.register_blueprint(user_bp)
    app.register_blueprint(job_bp)
    app.register_blueprint(teams_bp)
    app.register_blueprint(properties_bp)

    return app
