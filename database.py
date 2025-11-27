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
    role = Column(String, nullable=False, default='cleaner') # 'cleaner', 'team_leader', 'owner'
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

    jobs = relationship("Job", back_populates="property")

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
    report = Column(String) # Sensitive, only for Team Leader/Owner

    property_id = Column(Integer, ForeignKey('properties.id'))
    property = relationship("Property", back_populates="jobs")

    assignments = relationship("Assignment", back_populates="job")
 
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
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True) # For individual cleaners
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=True) # For assigned teams

    job = relationship("Job", back_populates="assignments")
    user = relationship("User", foreign_keys=[user_id])  
    team = relationship("Team", foreign_keys=[team_id])

    __table_args__ = (UniqueConstraint('job_id', 'user_id', name='_job_user_uc'),
                      UniqueConstraint('job_id', 'team_id', name='_job_team_uc'),
                      )

# Database initialization function
def init_db(app, database_path: str):
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
def create_initial_users(Session):
    session = Session()
    # create user with owner role
    if not session.query(User).filter_by(role='owner').first():
        owner = User(first_name='Lily', last_name='Hargrave', email='owner@example.com', phone='12345678', role='owner')
        owner.set_password('owner_password') # Default password for owner
        session.add(owner)
        session.commit()
        print("Initial owner user created.")

    # create user with team_leader role
    if not session.query(User).filter_by(email='team_leader@example.com').first():
        team_leader = User(first_name='Benjara', last_name="Brown", email='team_leader@example.com', role='team_leader')
        team_leader.set_password('team_leader_password')
        session.add(team_leader)
        session.commit()
        print("Initial team leader user created.")

    # create user with cleaner role
    if not session.query(User).filter_by(email='cleaner@example.com').first():
        cleaner = User(first_name='Tom', last_name='Gosling', email='cleaner@example.com', role='cleaner')
        cleaner.set_password('cleaner_password')
        session.add(cleaner)
        session.commit()
        print("Initial cleaner user created.")
    
    session.close()


def create_initial_property_and_job(Session):
    session = Session()
    cleaner = session.query(User).filter_by(email='cleaner@example.com').first()
    if cleaner and not session.query(Property).first():
        # Create a property
        property1 = Property(address='123 Main St, Anytown', access_notes='Key under mat')
        session.add(property1)
        session.commit()
        print("Initial property created.")

        # Create a job for today
        today = date.today()
        job1 = Job(
            date=today,
            time=time(9, 0),
            arrival_datetime=datetime.combine(today + timedelta(days=2), time(8, 45)), # Added arrival datetime
            end_time=time(11, 0), # Assuming a 2-hour job for initial data
            description='Full house clean, focus on kitchen and bathrooms.',
            is_complete=False,
            property=property1
        )
        session.add(job1)
        session.commit()

        # Assign the cleaner to the job
        assignment1 = Assignment(job_id=job1.id, user_id=cleaner.id)
        job_team1 = Assignment(job_id=job1.id, team_id=1)
        session.add(assignment1)
        session.add(job_team1)
        session.commit()
        print("Initial job created and assigned to cleaner.")

        # Create two back-to-back jobs for today
        job2 = Job(
            date=today,
            time=time(12, 0),
            arrival_datetime=datetime.combine(today + timedelta(days=1), time(11, 45)), # Added arrival datetime
            end_time=time(14, 0),
            description='Back-to-back job 1: Kitchen deep clean.',
            is_complete=False,
            property=property1
        )
        session.add(job2)
        session.commit()

        job3 = Job(
            date=today,
            time=time(14, 0),
            arrival_datetime=datetime.combine(today, time(13, 45)), # Added arrival datetime
            end_time=time(16, 0),
            description='Back-to-back job 2: Bathroom deep clean.',
            is_complete=False,
            property=property1
        )
        session.add(job3)
        session.commit()

        # Assign the cleaner to the back-to-back jobs
        assignment2 = Assignment(job_id=job2.id, user_id=cleaner.id)
        job_team2 = Assignment(job_id=job2.id, team_id=1)
        session.add(assignment2)
        session.add(job_team2)
        session.commit()

        assignment3 = Assignment(job_id=job3.id, user_id=cleaner.id)
        job_team3 = Assignment(job_id=job3.id, team_id=1)
        session.add(assignment3)
        session.add(job_team3)
        session.commit()
        print("Two back-to-back jobs created and assigned to cleaner.")

    session.close()

def _create_team(session, team_name, team_leader_id, members=None):
    team = session.query(Team).filter_by(name=team_name).first()
    if not team:
        team = Team(name=team_name, team_leader_id=team_leader_id)
        session.add(team)
        session.commit()
        print(f"{team_name} created with team leader ID {team_leader_id}.")
        if members:
            for member in members:
                member.team_id = team.id
            session.commit()
            print(f"Members assigned to {team_name}.")
    return team

def create_initial_team(Session):
    session = Session()
    
    owner = session.query(User).filter_by(role='owner').first()
    team_leader_user = session.query(User).filter_by(email='team_leader@example.com').first()
    cleaner = session.query(User).filter_by(email='cleaner@example.com').first()

    if owner and cleaner and team_leader_user:
        initial_team = _create_team(session, 'Initial Team', owner.id, members=[owner, cleaner])
        alpha_team = _create_team(session, 'Alpha Team', team_leader_user.id, members=[team_leader_user])
        beta_team = _create_team(session, 'Beta Team', team_leader_user.id)
        charlie_team = _create_team(session, 'Charlie Team', team_leader_user.id)
        delta_team = _create_team(session, 'Delta Team', team_leader_user.id)
    else:
        print("Owner, team_leader, or cleaner user not found. Team creation skipped.")
    
    session.close()

def _create_job(session, date, time, end_time, description, property_obj, team_obj=None, user_obj=None):
    # Randomize arrival date: same day, day after, or two days after
    days_offset = random.choice([0, 1, 2])
    arrival_date_for_job = date + timedelta(days=days_offset)
    
    job = Job(
        date=date,
        time=time,
        arrival_datetime=datetime.combine(arrival_date_for_job, time) - timedelta(minutes=15),
        end_time=end_time,
        description=description,
        is_complete=False,
        property=property_obj
    )
    session.add(job)
    session.commit()
    print(f"Job '{description}' created.")

    if user_obj:
        assignment = Assignment(job_id=job.id, user_id=user_obj.id)
        session.add(assignment)
        session.commit()
        print(f"Job '{description}' assigned to user {user_obj.first_name} {user_obj.last_name}.")
    
    if team_obj:
        assignment = Assignment(job_id=job.id, team_id=team_obj.id)
        session.add(assignment)
        session.commit()
        print(f"Job '{description}' assigned to team {team_obj.name}.")
    return job

def create_initial_property_and_job(Session):
    session = Session()
    cleaner = session.query(User).filter_by(email='cleaner@example.com').first()
    initial_team = session.query(Team).filter_by(name='Initial Team').first()
    alpha_team = session.query(Team).filter_by(name='Alpha Team').first()
    beta_team = session.query(Team).filter_by(name='Beta Team').first()
    charlie_team = session.query(Team).filter_by(name='Charlie Team').first()
    delta_team = session.query(Team).filter_by(name='Delta Team').first()

    property1 = session.query(Property).filter_by(address='123 Main St, Anytown').first()
    property_alpha = session.query(Property).filter_by(address='456 Oak Ave, Teamville').first()

    if not property1:
        property1 = Property(address='123 Main St, Anytown', access_notes='Key under mat')
        session.add(property1)
        session.commit()
        print("Initial property '123 Main St, Anytown' created.")
    
    if not property_alpha:
        property_alpha = Property(address='456 Oak Ave, Teamville', access_notes='Code 1234')
        session.add(property_alpha)
        session.commit()
        print("Property '456 Oak Ave, Teamville' created for Alpha Team.")

    today = date.today()

    # Initial jobs
    if cleaner and initial_team and not session.query(Job).filter(Job.date == today, Job.description.like('Full house clean%')).first():
        _create_job(session, today, time(9, 0), time(11, 0), 'Full house clean, focus on kitchen and bathrooms.', property1, team_obj=initial_team, user_obj=cleaner)
        _create_job(session, today, time(12, 0), time(14, 0), 'Back-to-back job 1: Kitchen deep clean.', property1, team_obj=initial_team, user_obj=cleaner)
        _create_job(session, today, time(14, 0), time(16, 0), 'Back-to-back job 2: Bathroom deep clean.', property1, team_obj=initial_team, user_obj=cleaner)

    # Alpha Team job
    if alpha_team and property_alpha and not session.query(Job).filter(Job.description.like('Alpha Team Job%')).first():
        _create_job(session, today, time(10, 0), time(12, 0), 'Alpha Team Job: Exterior window clean.', property_alpha, team_obj=alpha_team)

    # Beta Team job
    if beta_team and property1 and not session.query(Job).filter(Job.description.like('Beta Team Job%')).first():
        _create_job(session, today, time(13, 0), time(15, 0), 'Beta Team Job: Garden maintenance.', property1, team_obj=beta_team)

    # Charlie Team job
    if charlie_team and property_alpha and not session.query(Job).filter(Job.description.like('Charlie Team Job%')).first():
        _create_job(session, today, time(9, 30), time(11, 30), 'Charlie Team Job: Roof and gutter clean.', property_alpha, team_obj=charlie_team)

    # Delta Team job
    if delta_team and property1 and not session.query(Job).filter(Job.description.like('Delta Team Job%')).first():
        _create_job(session, today, time(15, 0), time(17, 0), 'Delta Team Job: Driveway pressure wash.', property1, team_obj=delta_team)

    session.close()

