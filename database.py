import os
import random
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date, Time, Boolean, UniqueConstraint, func, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from werkzeug.security import generate_password_hash
from flask import g, current_app
from flask_login import UserMixin
from datetime import date, time, timedelta, datetime

# Define the base for declarative models
Base = declarative_base()

# Define the User model
class User(Base, UserMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    phone = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default='user') # 'user', 'supervisor', 'admin'
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=True)
    team = relationship("Team", back_populates="members", foreign_keys=[team_id])
    
    assignments = relationship("Assignment", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, first_name='{self.first_name}', last_name='{self.last_name}', email='{self.email} role='{self.role}')>"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'role': self.role,
            'team_id': self.team_id
        }

class Property(Base):
    __tablename__ = 'properties'
    id = Column(Integer, primary_key=True)
    address = Column(String, nullable=False)
    access_notes = Column(String)
    notes = Column(String)

    jobs = relationship("Job", back_populates="property")
    property_images = relationship("PropertyImage", back_populates="property")

    def __repr__(self):
        return f"<Property(id={self.id}, address='{self.address}')>"

class Team(Base):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    team_leader_id = Column(Integer, ForeignKey('users.id'))
    team_leader = relationship("User", foreign_keys=[team_leader_id])
    members = relationship("User", back_populates="team", foreign_keys=[User.team_id])

    assignments = relationship("Assignment", back_populates="team")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'team_leader_id': self.team_leader_id,
            'team_leader': self.team_leader.to_dict() if self.team_leader else None,
            'members': [member.to_dict() for member in self.members]
        }

    def __repr__(self):
        return f"<Team(id={self.id}, name='{self.name}', team_leader_id={self.team_leader_id}), members={self.members}>"

class Job(Base):
    __tablename__ = 'jobs'

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    arrival_datetime = Column(DateTime, nullable=True)
    end_time = Column(Time, nullable=False)
    description = Column(String)
    is_complete = Column(Boolean, default=False)
    job_type = Column(String)
    report = Column(String) # Sensitive, only for Supervisor/admin

    property_id = Column(Integer, ForeignKey('properties.id'))
    property = relationship("Property", back_populates="jobs")

    assignments = relationship("Assignment", back_populates="job")
    job_images = relationship("JobImage", back_populates="job")
 
    @hybrid_property
    def arrival_date(self):
        if self.arrival_datetime:
            return self.arrival_datetime.date()
        return None

    @arrival_date.expression
    def arrival_date(cls):
        return func.date(cls.arrival_datetime)

    @hybrid_property
    def arrival_time_only(self):
        if self.arrival_datetime:
            return self.arrival_datetime.time()
        return None

    @arrival_time_only.expression
    def arrival_time_only(cls):
        return func.time(cls.arrival_datetime)

    def __repr__(self):
        return f"<Job(id={self.id}, date='{self.date}', time='{self.time}', arrival_datetime='{self.arrival_datetime}', end_time='{self.end_time}', is_complete='{self.is_complete}')>"

    @hybrid_property
    def duration(self):
        if self.time and self.end_time:
            # Calculate duration in minutes
            start_datetime = datetime.combine(self.date, self.time)
            end_datetime = datetime.combine(self.date, self.end_time)
            
            # Handle cases where end_time is on the next day (e.g., 22:00 - 02:00)
            if end_datetime < start_datetime:
                end_datetime += timedelta(days=1)

            duration_timedelta = end_datetime - start_datetime
            total_minutes = int(duration_timedelta.total_seconds() / 60)
            
            hours = total_minutes // 60
            minutes = total_minutes % 60
            
            if minutes > 0:
                return f"{hours}h {minutes}m"
            return f"{hours}h"
        return None

    @duration.expression
    def duration(cls):
        # This is a placeholder for a more complex SQL expression if needed
        # For now, it returns a string representation, which is not directly sortable/filterable in SQL
        # A more robust solution for SQL querying would involve storing duration or a calculated field
        return func.printf('%dh %dm',
                           (func.julianday(cls.end_time) - func.julianday(cls.time)) * 24,
                           ((func.julianday(cls.end_time) - func.julianday(cls.time)) * 24 * 60) % 60
                          )

class Assignment(Base):
    __tablename__ = 'assignments'
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('jobs.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True) # For individual users
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=True) # For assigned teams

    job = relationship("Job", back_populates="assignments")
    user = relationship("User", foreign_keys=[user_id])  
    team = relationship("Team", foreign_keys=[team_id])

    __table_args__ = (UniqueConstraint('job_id', 'user_id', name='_job_user_uc'),
                      UniqueConstraint('job_id', 'team_id', name='_job_team_uc'),
                      )

class Image(Base):
    __tablename__ = 'images'
    
    id = Column(Integer, primary_key=True)
    file_name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    
    property_images = relationship("PropertyImage", back_populates="image")
    job_images = relationship("JobImage", back_populates="image")
    
    def __repr__(self):
        return f"<Image(id={self.id}, file_name='{self.file_name}')>"

class PropertyImage(Base):
    __tablename__ = 'property_images'
    
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('properties.id'), nullable=False)
    image_id = Column(Integer, ForeignKey('images.id'), nullable=False)
    
    property = relationship("Property", back_populates="property_images")
    image = relationship("Image", back_populates="property_images")
    
    __table_args__ = (UniqueConstraint('property_id', 'image_id', name='_property_image_uc'),)
    
    def __repr__(self):
        return f"<PropertyImage(id={self.id}, property_id={self.property_id}, image_id={self.image_id})>"

class JobImage(Base):
    __tablename__ = 'job_images'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('jobs.id'), nullable=False)
    image_id = Column(Integer, ForeignKey('images.id'), nullable=False)
    
    job = relationship("Job", back_populates="job_images")
    image = relationship("Image", back_populates="job_images")
    
    __table_args__ = (UniqueConstraint('job_id', 'image_id', name='_job_image_uc'),)
    
    def __repr__(self):
        return f"<JobImage(id={self.id}, job_id={self.job_id}, image_id={self.image_id})>"

# Database initialization function
def init_db(database_uri: str):
    """
    Initializes the database and creates all tables.

    Args:
        database_path (str): The path to the SQLite database file.
        seed_data (bool): If True, the database will be seeded with deterministic test data.
    """
    engine = create_engine(database_uri)
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
    """Closes the database session at the end of a request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def create_initial_users(session):
    """
    Creates a set of deterministic initial users (admin, supervisor, user)
    and clears any existing users to ensure a clean state.

    Args:
        session: The SQLAlchemy session.

    Returns:
        tuple: A tuple containing the created admin, supervisor, and user User objects.
    """
    session.query(User).delete()
    session.commit()

    admin = User(id=1, first_name='Lily', last_name='Hargrave', email='admin@example.com', phone='12345678', role='admin')
    admin.set_password('admin_password')
    session.add(admin)

    supervisor = User(id=2, first_name='Benjara', last_name="Brown", email='supervisor@example.com', role='supervisor')
    supervisor.set_password('supervisor_password')
    session.add(supervisor)

    user = User(id=3, first_name='Tom', last_name='Gosling', email='user@example.com', role='user')
    user.set_password('user_password')
    session.add(user)
    
    session.commit()
    print("Initial users created for deterministic testing.")
    return admin, supervisor, user

def _create_team(session, team_name, team_leader_id=None, members=None, team_id=None):
    """
    Helper function to create or update a team with deterministic data.

    Args:
        session: The SQLAlchemy session.
        team_name (str): The name of the team.
        team_leader_id (int): The ID of the team leader.
        members (list, optional): A list of User objects to assign to the team. Defaults to None.
        team_id (int, optional): The explicit ID for the team. If None, SQLAlchemy assigns one.

    Returns:
        Team: The created or updated Team object.
    """
    team = session.query(Team).filter_by(name=team_name).first()
    if team:
        team.team_leader_id = team_leader_id
    else:
        team = Team(id=team_id, name=team_name, team_leader_id=team_leader_id)
        session.add(team)
    session.commit()

    if members:
        for member in members:
            member.team_id = team.id
        session.commit()
    return team

def create_initial_teams(session, admin, supervisor_user, user):
    """
    Creates a set of deterministic initial teams and clears any existing teams
    to ensure a clean state.

    Args:
        session: The SQLAlchemy session.
        admin (User): The admin User object.
        supervisor_user (User): The supervisor User object.
        user (User): The user User object.

    Returns:
        tuple: A tuple containing the created initial_team, alpha_team, beta_team,
               charlie_team, and delta_team objects.
    """
    session.query(Team).delete()
    session.commit()

    initial_team = _create_team(session, 'Initial Team', admin.id, members=[admin, user], team_id=1)
    alpha_team = _create_team(session, 'Alpha Team', supervisor_user.id, members=[supervisor_user], team_id=2)
    beta_team = _create_team(session, 'Beta Team', team_id=3)
    charlie_team = _create_team(session, 'Charlie Team', team_id=4)
    delta_team = _create_team(session, 'Delta Team', team_id=5)
    
    print("Initial teams created for deterministic testing.")
    return initial_team, alpha_team, beta_team, charlie_team, delta_team

def _create_job(session, date, time, end_time, description, property_obj, team_obj=None, user_obj=None, job_id=None, arrival_date_offset=0):
    """
    Helper function to create a job with deterministic data.

    Args:
        session: The SQLAlchemy session.
        date (date): The date of the job.
        time (time): The start time of the job.
        end_time (time): The end time of the job.
        description (str): The description of the job.
        property_obj (Property): The Property object associated with the job.
        team_obj (Team, optional): The Team object assigned to the job. Defaults to None.
        user_obj (User, optional): The User object assigned to the job. Defaults to None.
        job_id (int, optional): The explicit ID for the job. If None, SQLAlchemy assigns one.
        arrival_date_offset (int): The number of days to offset the arrival date from the job date.

    Returns:
        Job: The created Job object.
    """
    arrival_date_for_job = date + timedelta(days=arrival_date_offset)
    
    job = Job(
        id=job_id,
        date=date,
        time=time,
        arrival_datetime=datetime.combine(arrival_date_for_job, time),
        end_time=end_time,
        description=description,
        is_complete=False,
        property=property_obj
    )
    session.add(job)
    session.commit()

    if user_obj:
        assignment = Assignment(job_id=job.id, user_id=user_obj.id)
        session.add(assignment)
        session.commit()
    
    if team_obj:
        assignment = Assignment(job_id=job.id, team_id=team_obj.id)
        session.add(assignment)
        session.commit()
    return job

def create_initial_properties_and_jobs(session, admin, user, initial_team, alpha_team, beta_team, charlie_team, delta_team):
    """
    Creates a set of deterministic initial properties and jobs, and clears any existing
    properties, jobs, and assignments to ensure a clean state.

    Args:
        session: The SQLAlchemy session.
        admin (User): The admin User object.
        user (User): The user User object.
        initial_team (Team): The 'Initial Team' object.
        alpha_team (Team): The 'Alpha Team' object.
        beta_team (Team): The 'Beta Team' object.
        charlie_team (Team): The 'Charlie Team' object.
        delta_team (Team): The 'Delta Team' object.

    Returns:
        tuple: A tuple containing the created property1 and property_alpha objects.
    """
    session.query(Assignment).delete()
    session.query(Job).delete()
    session.query(Property).delete()
    session.commit()

    property1 = Property(id=1, address='123 Main St, Anytown', access_notes='Key under mat')
    session.add(property1)
    
    property_alpha = Property(id=2, address='456 Oak Ave, Teamville', access_notes='Code 1234')
    session.add(property_alpha)
    session.commit()
    print("Initial properties created for deterministic testing.")

    today = date.today()

    # Initial jobs
    _create_job(session, today, time(9, 0), time(11, 0), 'Full house clean, focus on kitchen and bathrooms.', property1, team_obj=initial_team, user_obj=admin, job_id=1, arrival_date_offset=2)
    _create_job(session, today, time(12, 0), time(14, 0), '', property1, team_obj=initial_team, job_id=2, arrival_date_offset=1)
    _create_job(session, today, time(14, 0), time(16, 0), '', property1, team_obj=initial_team, job_id=3, arrival_date_offset=0)
    
    # Alpha Team job
    _create_job(session, today, time(10, 0), time(12, 0), '', property_alpha, team_obj=alpha_team, job_id=4)
    _create_job(session, today, time(12, 30), time(14, 30), '', property_alpha, team_obj=alpha_team, job_id=8, arrival_date_offset=1)
    _create_job(session, today, time(9, 0), time(10, 30), "Don't let the cat outside", property1, team_obj=alpha_team, job_id=9, arrival_date_offset=2)
    _create_job(session, today, time(18, 30), time(20, 30), '', property1, team_obj=alpha_team, user_obj=user, job_id=10, arrival_date_offset=1)


    # Beta Team job
    _create_job(session, today, time(13, 0), time(15, 0), 'Beta Team Job: Garden maintenance.', property1, team_obj=beta_team, job_id=5)
    _create_job(session, today - timedelta(days=1), time(8, 0), time(10, 0), 'Beta Team Job: Pool cleaning.', property1, team_obj=beta_team, job_id=11)

    # Charlie Team job
    _create_job(session, today, time(9, 30), time(11, 30), 'Charlie Team Job: Roof and gutter clean.', property_alpha, team_obj=charlie_team, job_id=6)

    # Delta Team job
    _create_job(session, today, time(15, 0), time(17, 0), 'Delta Team Job: Driveway pressure wash.', property1, team_obj=delta_team, job_id=7)
    print("Initial jobs created and assigned for deterministic testing.")
    return property1, property_alpha

def insert_dummy_data(Session):
    """
    Populates the database with a consistent set of deterministic test data.
    This includes users, teams, properties, and jobs.
    This function clears existing data before seeding to ensure a clean state.

    Args:
        Session: The SQLAlchemy session factory.
    """
    session = Session()
    
    admin, supervisor_user, user = create_initial_users(session)
    initial_team, alpha_team, beta_team, charlie_team, delta_team = create_initial_teams(session, admin, supervisor_user, user)
    create_initial_properties_and_jobs(session, admin, user, initial_team, alpha_team, beta_team, charlie_team, delta_team)
    
    session.close()