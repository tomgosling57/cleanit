# Cleaner Management Web Application - Architecture Overview

## Project Structure

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

## Architecture Pattern

The application follows a **Model-View-Template (MVT)** architectural pattern, which is a variation of MVC for web frameworks like Flask.

### Key Components

- **Model Layer**: SQLAlchemy ORM for database interactions
- **View Layer**: Jinja templates for HTML rendering
- **Controller Layer**: Flask routes for request handling
- **Hypermedia Enhancement**: htmx for dynamic updates

## Technology Stack

- **Backend**: Flask (Python web framework)
- **Database**: SQLAlchemy ORM with PostgreSQL/MySQL/SQLite
- **Templating**: Jinja2
- **Frontend Enhancement**: htmx + dragulajs
- **Styling**: TailwindCSS
- **Testing**: pytest, Flask-Testing, Selenium

## Security Considerations

- Session-based authentication
- Role-based access control (RBAC)
- CSRF protection
- Input validation and sanitization
- SQL injection prevention via SQLAlchemy

## Development Approach

- Server-side rendering with progressive enhancement
- Mobile-first responsive design
- Hypermedia-driven architecture
- Test-driven development (TDD)