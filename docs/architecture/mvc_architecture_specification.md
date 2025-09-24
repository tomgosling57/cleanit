# Cleaner Management Web Application - MVC Architecture Specification

## 1. Overview

This document outlines the mid-tier architecture for the Cleaner Management Web Application using the Model-View-Controller (MVC) pattern with Flask, SQLAlchemy, and Jinja templates. The architecture follows a hypermedia-driven approach enhanced with htmx for dynamic updates.

## 2. Project Structure

```
cleaner_management/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── models/               # SQLAlchemy models
│   ├── __init__.py
│   ├── user.py
│   ├── role.py
│   ├── team.py
│   ├── job.py
│   └── assignment.py
├── templates/            # Jinja templates
│   ├── base.html
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   ├── timetable/
│   │   ├── timetable.html
│   │   └── partials/
│   │       ├── team_column.html
│   │       └── job_card.html
│   └── admin/
│       ├── users.html
│       └── teams.html
├── static/               # Static assets
│   ├── css/
│   ├── js/
│   └── images/
├── routes/               # Flask route handlers
│   ├── __init__.py
│   ├── auth.py
│   ├── timetable.py
│   └── admin.py
└── utils/                # Utility functions
    ├── __init__.py
    └── auth.py
```

## 3. Model Layer (SQLAlchemy)

### 3.1 Core Models

#### User Model
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

#### Role Model
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

#### Team Model
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

#### Job Model
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

#### Assignment Model
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

### 3.2 Database Relationships

- **User ↔ Role**: Many-to-One (Many users can have the same role)
- **User ↔ Team**: Many-to-One (Many users can belong to one team)
- **Team ↔ Job**: One-to-Many (One team can have many jobs)
- **Job ↔ Assignment**: One-to-Many (One job can have multiple assignments for different cleaners)
- **User ↔ Assignment**: One-to-Many (One user can have multiple job assignments)

## 4. View Layer (Jinja Templates)

### 4.1 Template Structure

#### Base Template (`base.html`)
- Common layout with navigation, header, and footer
- Includes TailwindCSS and htmx scripts
- Authentication state management
- Responsive design foundation

#### Authentication Templates
- `auth/login.html`: User login form
- `auth/register.html`: User registration (owner/admin only)

#### Timetable Templates
- `timetable/timetable.html`: Main timetable view with team columns
- `timetable/partials/team_column.html`: Reusable team column component
- `timetable/partials/job_card.html`: Individual job card component

#### Admin Templates
- `admin/users.html`: User management interface
- `admin/teams.html`: Team management interface
- `admin/jobs.html`: Job creation and management

### 4.2 Template Features

- **Role-based content**: Templates conditionally render content based on user roles
- **htmx integration**: Dynamic updates without full page reloads
- **Responsive design**: Mobile-first approach with TailwindCSS
- **Drag-and-drop**: Enhanced with dragulajs for job reassignment

## 5. Controller Layer (Flask Routes)

### 5.1 Authentication Routes

**GET /login**
- Renders login form
- Redirects authenticated users to appropriate dashboard

**POST /login**
- Authenticates user credentials
- Sets session and redirects based on user role

**GET /logout**
- Clears user session
- Redirects to login page

**GET /register** (Owner only)
- Renders user registration form

**POST /register** (Owner only)
- Creates new user accounts with role assignment

### 5.2 Timetable Routes

**GET /timetable**
- Renders main timetable view
- Filters jobs by selected date
- Organizes jobs by team columns
- Role-based access control

**GET /timetable/date/<date>**
- Returns timetable for specific date
- Used for date navigation via htmx

**POST /update-job-assignment**
- Updates job team assignment via drag-and-drop
- Returns updated team column HTML via htmx
- Validates user permissions

**GET /job/<job_id>**
- Renders job details modal
- Used for viewing/editing job information

**POST /job/<job_id>/update**
- Updates job details
- Returns updated job card HTML via htmx

**POST /job/create**
- Creates new job
- Returns new job card HTML via htmx

### 5.3 Admin Routes

**GET /admin/users**
- User management interface
- List, create, edit, delete users
- Role assignment functionality

**POST /admin/users/<user_id>/update-role**
- Updates user role
- Validates permission changes

**GET /admin/teams**
- Team management interface
- Create, edit teams
- Assign team leaders

**POST /admin/teams/create**
- Creates new team
- Returns team list update via htmx

### 5.4 Additional Justified Endpoints

**GET /api/jobs/date/<date>** (JSON endpoint)
- **Justification**: Needed for potential mobile app integration or external systems
- Returns job data in JSON format for specific date
- Enables future API consumption

**GET /dashboard**
- **Justification**: Role-specific landing pages improve UX
- Redirects users to appropriate views based on role
- Cleaner: Personal schedule view
- Team Leader: Team management dashboard
- Owner: Full admin dashboard

**POST /job/<job_id>/complete**
- **Justification**: Workflow completion tracking
- Marks job as completed
- Updates job status and records completion time
- Triggers notifications if needed

**GET /reports/team-performance**
- **Justification**: Business intelligence requirements
- Generates team performance metrics
- Completion rates, time tracking, etc.

## 6. Security Considerations

### 6.1 Authentication & Authorization
- Session-based authentication
- Role-based access control (RBAC)
- Route-level permission checks
- CSRF protection for all POST endpoints

### 6.2 Data Validation
- Input sanitization for all user inputs
- SQL injection prevention via SQLAlchemy
- XSS protection through template escaping

### 6.3 Business Logic Validation
- Team leaders can only manage their own team's jobs
- Cleaners can only view their assigned jobs
- Owners have full system access

## 7. htmx Integration Strategy

### 7.1 Dynamic Updates
- Job assignment updates via `POST /update-job-assignment`
- Date navigation via `GET /timetable/date/<date>`
- Job creation/editing via modal forms with htmx submissions
- Real-time status updates without page reloads

### 7.2 Progressive Enhancement
- Core functionality works without JavaScript
- htmx enhances user experience with AJAX updates
- Graceful degradation for older browsers

## 8. Database Schema Evolution

### 8.1 Initial Migration
- Create all tables with relationships
- Seed initial roles (cleaner, team_leader, owner)
- Create default admin user

### 8.2 Future Considerations
- Audit logging for job changes
- Notification system for assignments
- Time tracking for job completion
- Performance metrics and reporting

This architecture provides a solid foundation for the Cleaner Management Web Application, balancing simplicity with extensibility for future enhancements.