from flask_login import LoginManager
from app_factory import create_app

if __name__ == '__main__':
    login_manager = LoginManager()
    app = create_app(login_manager=login_manager, config_override={'DEBUG': True, 'TESTING': True})
    app.run(debug=True)