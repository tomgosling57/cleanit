from flask_login import LoginManager
from app_factory import create_app

if __name__ == '__main__':
    login_manager = LoginManager()
    app_config = {
        'INSERT_DUMMY_DATA': True,
        'SEED_DATABASE_FOR_TESTING': True,
    }
    app = create_app(login_manager=login_manager, test_config=app_config)
    app.run(debug=True)