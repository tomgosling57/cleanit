import os
import random
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date, Time, Boolean, UniqueConstraint, func, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from werkzeug.security import generate_password_hash
from flask import g, current_app
from flask_login import UserMixin
from datetime import date, time, timedelta, datetime

from config import DATETIME_FORMATS
from utils.timezone import to_app_tz

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
    property_media = relationship("PropertyMedia", back_populates="property")

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
    job_media = relationship("JobMedia", back_populates="job")
 
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

    @hybrid_property
    def display_date(self):
        # Instance-level: self.date is an actual date object
        return to_app_tz(datetime.combine(self.date, self.time)).strftime(DATETIME_FORMATS['DATE_FORMAT'])

    @display_date.expression
    def display_date(cls):
        # Class-level: For SQL queries, return the date column itself
        # The comparison should be done against the raw date, not the formatted string
        return cls.date

    @hybrid_property
    def display_time(self):
        return to_app_tz(datetime.combine(self.date, self.time)).strftime(DATETIME_FORMATS['TIME_FORMAT'])

    @display_time.expression
    def display_time(cls):
        return cls.time

    @hybrid_property
    def display_end_time(self):
        return to_app_tz(datetime.combine(self.date, self.end_time)).strftime(DATETIME_FORMATS['TIME_FORMAT'])

    @display_end_time.expression
    def display_end_time(cls):
        return cls.end_time

    @hybrid_property
    def display_arrival_time(self):
        return to_app_tz(self.arrival_datetime).strftime(DATETIME_FORMATS['TIME_FORMAT']) if self.arrival_datetime else None

    @display_arrival_time.expression
    def display_arrival_time(cls):
        return func.time(cls.arrival_datetime)

    @hybrid_property
    def display_arrival_date(self):
        return to_app_tz(self.arrival_datetime).strftime(DATETIME_FORMATS['DATE_FORMAT']) if self.arrival_datetime else None

    @display_arrival_date.expression
    def display_arrival_date(cls):
        return func.date(cls.arrival_datetime)

    @hybrid_property
    def display_arrival_datetime(self):
        return to_app_tz(self.arrival_datetime).strftime(DATETIME_FORMATS['DATETIME_FORMAT']) if self.arrival_datetime else None

    @display_arrival_datetime.expression
    def display_arrival_datetime(cls):
        return cls.arrival_datetime

    def __repr__(self):
        return f"<Job(id={self.id}, date='{self.date}', time='{self.time}', arrival_datetime='{self.arrival_datetime}', end_time='{self.end_time}', is_complete='{self.is_complete}')>"

    def to_dict(self, include_report=False):
        data = {
            'id': self.id,
            'date_utc': self.date.isoformat(),
            'time_utc': self.time.isoformat(),
            'arrival_datetime_utc': self.arrival_datetime.isoformat() if self.arrival_datetime else None,
            'end_time_utc': self.end_time.isoformat(),
            'description': self.description,
            'is_complete': self.is_complete,
            'job_type': self.job_type,
            'property_id': self.property_id,
        }
        if include_report:
            data['report'] = self.report
        return data
    
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

class Media(Base):
    __tablename__ = 'media'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False, unique=True)
    file_path = Column(String, nullable=False)
    media_type = Column(String, nullable=False)
    mimetype = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    upload_date = Column(DateTime, nullable=False, default=func.now())
    description = Column(String, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    resolution = Column(String, nullable=True)
    codec = Column(String, nullable=True)
    aspect_ratio = Column(String, nullable=True)
    
    property_media = relationship("PropertyMedia", back_populates="media")
    job_media = relationship("JobMedia", back_populates="media")
    
    def __repr__(self):
        return f"<Media(id={self.id}, filename='{self.filename}', media_type='{self.media_type}')>"
    
    @hybrid_property
    def display_upload_date(self):
        return to_app_tz(self.upload_date).strftime(DATETIME_FORMATS['DATE_FORMAT'])

class PropertyMedia(Base):
    __tablename__ = 'property_media'
    
    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('properties.id'), nullable=False)
    media_id = Column(Integer, ForeignKey('media.id'), nullable=False)
    
    property = relationship("Property", back_populates="property_media")
    media = relationship("Media", back_populates="property_media")
    
    __table_args__ = (UniqueConstraint('property_id', 'media_id', name='_property_media_uc'),)
    
    def __repr__(self):
        return f"<PropertyMedia(id={self.id}, property_id={self.property_id}, media_id={self.media_id})>"

class JobMedia(Base):
    __tablename__ = 'job_media'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('jobs.id'), nullable=False)
    media_id = Column(Integer, ForeignKey('media.id'), nullable=False)
    
    job = relationship("Job", back_populates="job_media")
    media = relationship("Media", back_populates="job_media")
    
    __table_args__ = (UniqueConstraint('job_id', 'media_id', name='_job_media_uc'),)
    
    def __repr__(self):
        return f"<JobMedia(id={self.id}, job_id={self.job_id}, media_id={self.media_id})>"

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
