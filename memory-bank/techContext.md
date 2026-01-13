# Technical Context: CleanIt Technology Stack and Development Setup

## Technology Stack

### Backend Framework
- **Flask 3.1.2**: Lightweight Python web framework
- **Flask Extensions**:
  - Flask-SQLAlchemy 3.1.1: ORM integration
  - Flask-Login 0.6.3: Authentication and session management
  - Flask-WTF 1.2.1: CSRF protection only
- **SQLAlchemy 2.0.30**: Database ORM and query builder
- **Werkzeug 3.1.0**: WSGI utilities and request/response handling
- **Python 3.12.3**
  
### Database
- **Primary Database**: PostgreSQL (production), MySQL (alternative production)
- **Development Database**: SQLite with file-based storage
- **ORM**: SQLAlchemy with declarative base models
- **Migration Strategy**: Alembic (planned) or manual schema updates

### Storage Layer
- **Cloud Storage**: Amazon S3 via boto3 library
- **Local Storage**: Filesystem storage for development (currently not in use)
- **Temporary Storage**: Auto-cleaning temp directories for testing (Use this over local storage)
- **Abstraction Layer**: Apache Libcloud 3.8.0+ for unified storage interface
- **File Processing**: Pillow 10.2.0 for image manipulation

### Frontend Technologies
- **Templating**: Jinja2 with template inheritance and fragments
- **Interactive Enhancements**: htmx for partial page updates and AJAX
- **JavaScript**: Vanilla ES6+ with modular patterns
- **CSS**: Custom CSS with CSS variables for theming (no frameworks)
- **Icons**: SVG icons with inline embedding and CSS styling
- **Drag-and-Drop**: DragulaJS for interactive job assignment

### Testing Stack
- **Unit/Integration Testing**: pytest 8.4.2 with pytest-flask 1.3.0
- **End-to-End Testing**: Playwright with pytest-playwright 0.7.2
- **Test Coverage**: pytest-cov (planned) for coverage reporting
- **Test Data**: Factory pattern for test data generation
- **Storage Testing**: Cross-provider testing for all storage backends

### Development Tools
- **Python Environment**: python-dotenv 1.0.1 for environment management
- **Dependency Management**: requirements.txt with pinned versions
- **Type Checking**: mypy (optional) for type hints

## Development Environment Setup


- **Python 3.9+**: Required for all Python dependencies
- **PostgreSQL/MySQL**: For production-like development (optional)
- **Node.js**: For Playwright end-to-end testing
- **Git**: Version control system

### Installation Steps
1. **Clone repository**: `git clone <repository-url>`
2. **Create virtual environment**: `python -m venv venv`
3. **Activate virtual environment**: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. **Install dependencies**: `pip install -r requirements.txt`
5. **Install Playwright browsers**: `playwright install`
6. **Set up environment variables**: Copy `.env.example` to `.env` and configure
7. **Initialize database**: Run database initialization script
8. **Run development server**: `python app.py`

### Environment Variables
```bash
# Required for production
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost/cleanit
FLASK_ENV=production

# Optional - S3 Storage Configuration
STORAGE_PROVIDER=s3
S3_BUCKET=your-bucket-name
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# Development overrides
FLASK_ENV=development
STORAGE_PROVIDER=local
UPLOAD_FOLDER=./uploads
```

### Database Setup
1. **Development (SQLite)**: Automatic creation in `instance/cleanit.db`
2. **Production (PostgreSQL)**:
   ```bash
   createdb cleanit
   psql -d cleanit -f schema.sql
   ```
3. **Test Database**: Automatically created and destroyed during tests

## Project Structure

### Directory Layout
```
cleanit/
├── app.py                    # Application entry point
├── app_factory.py           # Application factory with dependency injection
├── config.py                # Configuration classes
├── database.py              # Database initialization and session management
├── requirements.txt         # Python dependencies
├── README.md               # Project documentation
│
├── controllers/             # Request handlers and route controllers
│   ├── jobs_controller.py
│   ├── media_controller.py
│   ├── property_controller.py
│   ├── teams_controller.py
│   └── users_controller.py
│
├── routes/                  # Flask blueprints and route definitions
│   ├── jobs.py
│   ├── media.py
│   ├── properties.py
│   ├── teams.py
│   └── users.py
│
├── services/                # Business logic and service layer
│   ├── assignment_service.py
│   ├── job_service.py
│   ├── media_service.py
│   ├── property_service.py
│   ├── team_service.py
│   └── user_service.py
│
├── static/                  # Static assets
│   ├── css/                # Stylesheets
│   ├── js/                 # JavaScript files
│   ├── icons/              # SVG and PNG icons
│   └── images/             # Image assets and placeholders
│
├── templates/               # Jinja2 templates
│   ├── base.html           # Base template
│   ├── components/         # Reusable template components
│   ├── error.html          # Error pages
│   └── [feature].html      # Feature-specific templates
│
├── tests/                   # Test suite
│   ├── conftest.py         # Test configuration and fixtures
│   ├── helpers.py          # Test utilities
│   └── test_*.py           # Test modules
│
└── utils/                   # Utility modules
    ├── error_handlers.py   # Global error handling
    ├── storage.py          # Storage abstraction utilities
    ├── media_utils.py      # Media processing utilities
    └── [other utilities].py
```

## Key Technical Decisions

### Custom CSS Over Frameworks
- **Decision**: Implement custom CSS with CSS variables
- **Rationale**:
  - Complete design control without framework constraints
  - Smaller CSS bundle size
  - Better performance with targeted styles
  - Consistent theming through CSS custom properties

### Cloud-First Storage Strategy
- **Decision**: S3 as primary storage with local fallback
- **Rationale**:
  - Production-ready scalability from day one
  - Simplified deployment to cloud environments
  - Development flexibility with local storage
  - Test isolation with temporary storage

### Multi-Layer Testing Strategy
- **Decision**: Combine pytest unit tests with Playwright E2E tests
- **Rationale**:
  - Comprehensive test coverage across all layers
  - Fast feedback with unit tests
  - Confidence with end-to-end workflow testing
  - Support for testing storage across all providers

## Development Workflows

```bash
# First activate the virtual environment
source .venv/bin/activate
```
### Running the Application
```bash

# Development mode with debug
python app.py

# Production mode (using gunicorn)
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Running Tests
```bash
# Run all tests
pytest

# Run specific test module
pytest tests/test_media_service.py

# Run tests with coverage
pytest --cov=.

# Run end-to-end tests
pytest tests/test_*.py -k "e2e" --headed
```

### Database Operations
```bash
# Initialize development database
python -c "from utils.populate_database import populate_database; populate_database('sqlite:///instance/cleanit.db')"

## Deployment Considerations

### Production Requirements
- **Web Server**: Gunicorn or uWSGI for WSGI serving
- **Reverse Proxy**: Nginx or Apache for static files and SSL termination
- **Database**: PostgreSQL with connection pooling
- **Storage**: S3 bucket with appropriate IAM permissions
- **Environment**: Linux server with Python 3.9+

### Containerization (Future)
- **Dockerfile**: Multi-stage build for production
- **Docker Compose**: Local development with all services
- **Orchestration**: Kubernetes or ECS for scaling

### Monitoring and Logging
- **Application Logs**: Structured logging with JSON format
- **Error Tracking**: Sentry or similar error monitoring
- **Performance Monitoring**: APM tools for request tracing
- **Health Checks**: `/health` endpoint for container orchestration

## Performance Considerations

### Database Optimization
- **Connection Pooling**: SQLAlchemy connection pool configuration
- **Query Optimization**: Eager loading for related data
- **Indexing**: Appropriate indexes for frequent query patterns
- **Caching**: Redis/memcached for frequently accessed data (future)

### Frontend Performance
- **Asset Optimization**: Minified CSS and JavaScript (future)
- **Image Optimization**: Responsive images with appropriate formats
- **Lazy Loading**: Deferred loading of non-critical resources
- **Caching Strategies**: Browser caching for static assets

### Scalability Patterns
- **Stateless Design**: Session data in secure cookies or database
- **Horizontal Scaling**: Multiple application instances behind load balancer
- **Database Scaling**: Read replicas for reporting queries
- **Async Processing**: Background tasks for long-running operations (future)

## Security Considerations

### Authentication and Authorization
- **Session Security**: Secure cookies with HttpOnly and SameSite flags
- **Password Storage**: bcrypt or similar hashing algorithm
- **Role-Based Access**: Three-tier permission system (admin, supervisor, user)
- **Route Protection**: Decorator-based access control

### Data Security
- **Input Validation**: Server-side validation for all user inputs
- **Output Encoding**: Jinja2 auto-escaping for XSS protection
- **SQL Injection Prevention**: SQLAlchemy parameterized queries
- **File Upload Security**: File type validation and virus scanning (future)

### Infrastructure Security
- **HTTPS Enforcement**: SSL/TLS for all production traffic
- **Security Headers**: CSP, HSTS, X-Frame-Options headers
- **Secret Management**: Environment variables for sensitive data
- **Regular Updates**: Dependency vulnerability scanning and updates