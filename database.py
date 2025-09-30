import os
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date, Time, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from werkzeug.security import generate_password_hash
from flask import g, current_app
from flask_login import UserMixin
from datetime import date, time

# Define the base for declarative models
Base = declarative_base()

# Define the User model
class User(Base, UserMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default='cleaner') # 'cleaner', 'team_leader', 'owner'

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

class Property(Base):
    __tablename__ = 'properties'
    id = Column(Integer, primary_key=True)
    address = Column(String, nullable=False)
    access_notes = Column(String)

    jobs = relationship("Job", back_populates="property")

    def __repr__(self):
        return f"<Property(id={self.id}, address='{self.address}')>"

class Job(Base):
    __tablename__ = 'jobs'

    id = Column(Integer, primary_key=True)
    job_title = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    duration = Column(String, nullable=False)
    description = Column(String)
    assigned_cleaners = Column(String) # Comma-separated cleaner IDs
    is_complete = Column(Boolean, default=False)
    job_type = Column(String)
    report = Column(String) # Sensitive, only for Team Leader/Owner

    property_id = Column(Integer, ForeignKey('properties.id'))
    property = relationship("Property", back_populates="jobs")

    def __repr__(self):
        return f"<Job(id={self.id}, job_title='{self.job_title}', date='{self.date}', is_complete='{self.is_complete}')>"

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

def create_initial_cleaner(Session):
    session = Session()
    if not session.query(User).filter_by(username='cleaner').first():
        cleaner = User(username='cleaner', role='cleaner')
        cleaner.set_password('cleanerpassword')
        session.add(cleaner)
        session.commit()
        print("Initial cleaner user created.")
    session.close()

def create_initial_property_and_job(Session):
    session = Session()
    cleaner = session.query(User).filter_by(username='cleaner').first()
    if cleaner and not session.query(Property).first():
        # Create a property
        property1 = Property(address='123 Main St, Anytown', access_notes='Key under mat')
        session.add(property1)
        session.commit()
        print("Initial property created.")

        # Create a job for today
        today = date.today()
        job1 = Job(
            job_title='Morning Clean',
            date=today,
            time=time(9, 0),
            duration='2 hours',
            description='Full house clean, focus on kitchen and bathrooms.',
            assigned_cleaners=str(cleaner.id),
            is_complete=False,
            property=property1
        )
        session.add(job1)
        session.commit()
        print("Initial job created for cleaner.")
    session.close()
