# SQLAlchemy Models Specification

## User Model
```python
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    role_id = Column(Integer, ForeignKey('roles.id'), nullable=False)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    role = relationship("Role", back_populates="users")
    team = relationship("Team", back_populates="members")
    created_jobs = relationship("Job", back_populates="created_by", 
                               foreign_keys="Job.created_by_id")
    assigned_jobs = relationship("Assignment", back_populates="cleaner")
```

## Role Model
```python
class Role(Base):
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)  # 'cleaner', 'team_leader', 'owner'
    description = Column(Text)
    permissions = Column(JSON)  # Store permission flags
    
    # Relationships
    users = relationship("User", back_populates="role")
```

## Team Model
```python
class Team(Base):
    __tablename__ = 'teams'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    team_leader_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    members = relationship("User", back_populates="team")
    team_leader = relationship("User", foreign_keys=[team_leader_id])
    jobs = relationship("Job", back_populates="team")
```

## Job Model
```python
class Job(Base):
    __tablename__ = 'jobs'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    location = Column(String(200))
    duration_minutes = Column(Integer, nullable=False)  # Estimated duration
    priority = Column(String(20), default='medium')  # 'low', 'medium', 'high', 'urgent'
    status = Column(String(20), default='pending')  # 'pending', 'assigned', 'in_progress', 'completed'
    scheduled_date = Column(Date, nullable=False)
    scheduled_time = Column(Time, nullable=False)
    team_id = Column(Integer, ForeignKey('teams.id'), nullable=True)
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    team = relationship("Team", back_populates="jobs")
    created_by = relationship("User", foreign_keys=[created_by_id])
    assignments = relationship("Assignment", back_populates="job")
```

## Assignment Model
```python
class Assignment(Base):
    __tablename__ = 'assignments'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('jobs.id'), nullable=False)
    cleaner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text)
    
    # Relationships
    job = relationship("Job", back_populates="assignments")
    cleaner = relationship("User", back_populates="assigned_jobs")
```

## Database Relationships

- **User ↔ Role**: Many-to-One (Many users can have the same role)
- **User ↔ Team**: Many-to-One (Many users can belong to one team)
- **Team ↔ Job**: One-to-Many (One team can have many jobs)
- **Job ↔ Assignment**: One-to-Many (One job can have multiple assignments for different cleaners)
- **User ↔ Assignment**: One-to-Many (One user can have multiple job assignments)

## Model Validation Rules

### User Model Validation
- Username must be unique and between 3-80 characters
- Email must be unique and valid format
- Password must be hashed before storage
- Role must be assigned (cleaner, team_leader, or owner)

### Job Model Validation
- Title must be between 1-200 characters
- Duration must be positive integer
- Priority must be one of: low, medium, high, urgent
- Status must be one of: pending, assigned, in_progress, completed
- Scheduled date must be in the future

### Assignment Model Validation
- Job must exist and be assigned
- Cleaner must exist and have appropriate role
- Completion time must be after assignment time