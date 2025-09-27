import os
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from werkzeug.security import generate_password_hash
from flask import g, current_app

# Define the base for declarative models
Base = declarative_base()

# Define the User model
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default='cleaner') # 'cleaner', 'team_leader', 'owner'

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

# Database initialization function
def init_db(app):
    database_path = os.path.join(app.root_path, 'instance', 'cleanit.db')
    engine = create_engine(f'sqlite:///{database_path}')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session

# Helper functions for database session management
def get_db():
    """Helper function to get or create a database connection for the current request."""
    if 'db' not in g:
        Session = current_app.config['SQLALCHEMY_SESSION']
        g.db = Session()
    return g.db

def teardown_db(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Function to create an initial owner user
def create_initial_owner(Session):
    session = Session()
    if not session.query(User).filter_by(role='owner').first():
        owner = User(username='owner', role='owner')
        owner.set_password('ownerpassword') # Default password for owner
        session.add(owner)
        session.commit()
        print("Initial owner user created.")
    session.close()
