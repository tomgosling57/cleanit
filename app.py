from flask_login import LoginManager
from app_factory import create_app
from utils.database import populate_database

if __name__ == '__main__':
    login_manager = LoginManager()
    app = create_app(login_manager=login_manager)
    populate_database(app.config['SQLALCHEMY_DATABASE_URI'])
    app.run(debug=True)