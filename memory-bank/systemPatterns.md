# System Patterns: CleanIt Architecture and Design Patterns

## System Architecture Overview

### Layered Architecture
CleanIt follows a **Model-View-Template (MVT)** pattern adapted for Flask applications:

1. **Model Layer** (SQLAlchemy ORM)
   - Database models and relationships
   - Data validation and business logic encapsulation
   - Database session management

2. **Controller Layer** (Flask Routes/Blueprints)
   - Request handling and routing
   - Input validation and sanitization
   - Response formatting
   - Authentication and authorization checks

3. **Service Layer** (Business Logic)
   - Core business operations
   - Complex transaction management
   - Cross-cutting concerns
   - Integration with external services

4. **Template Layer** (Jinja2 Templates)
   - Server-side rendering
   - Dynamic content generation
   - HTML structure and presentation

5. **Hypermedia Layer** (htmx)
   - Progressive enhancement
   - Partial page updates
   - Interactive UI components

## Key Design Patterns

### 1. Factory Pattern
**Application Factory** (`app_factory.py`)
- Centralized application creation with configurable options
- Dependency injection for services and components
- Environment-specific configuration management
- Test configuration support with temporary storage

### 2. Service Layer Pattern
**Separation of business logic from controllers**
- **Service Classes**: `*_service.py` files contain business logic
- **Controller Delegation**: Controllers delegate complex operations to services
- **Transaction Management**: Services handle database transactions
- **Reusability**: Services can be used by multiple controllers

### 3. Repository Pattern (via SQLAlchemy)
**Data access abstraction**
- SQLAlchemy models as data entities
- Service layer acts as repository interface
- Database-agnostic query construction
- Relationship management through ORM

### 4. Strategy Pattern
**Configurable storage providers**
- Storage strategy selection based on configuration
- Unified interface for different storage backends (S3, local, temp)
- Runtime switching between storage implementations
- Test isolation with temporary storage strategy

### 5. Role-Based Access Control (RBAC) Pattern
**Three-tier permission system**
- **Admin**: Full system access, user management, job/property/team modification
- **Supervisor**: Job completion, media upload, access code viewing, address book access
- **User**: Daily schedule viewing, job details (no access codes), profile management
- **Route-level enforcement**: Decorators and middleware for access control
- **Data-level filtering**: Queries filtered by user role and relationships

### 6. Progressive Enhancement Pattern
**htmx-driven interactivity**
- Server-rendered base content works without JavaScript
- htmx attributes add interactive capabilities
- Partial page updates without full reloads
- Graceful degradation for non-JavaScript clients

### 7. Component-Based Templates
**Reusable template fragments**
- Modular template components (`_form_response.html`, `card_actions.html`)
- Template inheritance with `base.html`
- Fragment rendering for htmx updates
- Consistent UI patterns across the application

## Database Design Patterns

### Entity Relationships
```
User (1) ──── (many) TeamMembership (many) ──── (1) Team
  │                                              │
  │                                              │
Job (many) ──── (1) Property                    │
  │                                              │
  └─── (many) JobAssignment (many) ─────────────┘
```

### Key Models
1. **User**: Authentication, roles, profile information
2. **Team**: Grouping of users for job assignment
3. **Property**: Location details, access codes, address information
4. **Job**: Cleaning tasks with schedules, status, requirements
5. **Media**: Files associated with jobs or properties
6. **JobAssignment**: Many-to-many relationship between jobs and teams/users

### Data Integrity Patterns
- **Foreign Key Constraints**: Enforce relational integrity
- **Cascade Operations**: Automatic cleanup of related records
- **Transaction Boundaries**: Atomic operations for complex updates
- **Validation Hooks**: SQLAlchemy validators for data quality

## Storage Architecture Patterns

### Cloud-First Storage Strategy
1. **Primary Storage**: S3 for production environments
2. **Fallback Storage**: Local filesystem for development
3. **Test Storage**: Temporary directories that auto-clean
4. **Unified Interface**: Libcloud abstraction layer

### Media Management Patterns
- **Single Service Responsibility**: Media Service handles both storage AND collection management
- **Entity-Scoped Operations**: Media operations scoped within Job/Property contexts (not separate Media Controller)
- **Batch Operations**: Efficient batch upload/delete for gallery management
- **Unique Filename Generation**: Prevent collisions and ensure security
- **Path Resolution**: Abstract storage location from application logic
- **URL Generation**: Dynamic URL construction for frontend access with Docker/MinIO support
- **Collection Management**: Entity-media relationship management within single service

### Docker/MinIO URL Generation Pattern
**Problem**: In Docker environments, MinIO runs at internal hostname `minio:9000` but browsers need public hostname `localhost:9000`

**Solution**: Configurable public hostname pattern
1. **Environment Variables**: `S3_PUBLIC_HOST` and `S3_PUBLIC_PORT` define public access point
2. **URL Construction**: `get_file_url()` builds URLs like `http://{S3_PUBLIC_HOST}:{S3_PUBLIC_PORT}/{bucket}/{filename}`
3. **Docker Compose Default**: `S3_PUBLIC_HOST=localhost`, `S3_PUBLIC_PORT=9000` (mapped port)
4. **Production Flexibility**: Can be configured for any public endpoint or CDN

**Benefits**:
- ✅ Images display correctly in gallery (not placeholders)
- ✅ No hardcoded hostnames - configurable via environment
- ✅ Works with Docker port mapping and networking
- ✅ Supports both development and production deployments

#### Media Architecture Pattern
```
Client → Job/Property Controller → Media Service → Storage
         (entity context)         (storage + collections)
         
Instead of:
Client → Media Controller → Media Service → Storage
         (wrong scope)     (storage only)
```

## Frontend Architecture Patterns

### CSS Architecture
- **CSS Variables**: Theme consistency through custom properties
- **Component-Based Styling**: Modular CSS files per feature area
- **Mobile-First Responsive Design**: Progressive enhancement for larger screens
- **Custom Styling**: No framework dependency (no TailwindCSS)

### JavaScript Patterns
- **Module Pattern**: Encapsulated functionality in gallery components
- **Event Delegation**: Efficient event handling for dynamic content
- **Progressive Enhancement**: JavaScript enhances but doesn't break core functionality
- **Drag-and-Drop**: Interactive job assignment with visual feedback

### htmx Integration Patterns
- **Attribute-Driven**: `hx-get`, `hx-post`, `hx-target` attributes
- **Partial Updates**: Replace specific DOM elements without full page reload
- **Form Handling**: Enhanced form submission with validation feedback
- **Modal Management**: Dynamic modal content loading

## Testing Patterns

### Multi-Layer Testing Strategy
1. **Unit Tests**: Isolated service and utility testing
2. **Integration Tests**: Controller and database interaction testing
3. **End-to-End Tests**: Playwright for full user workflow testing
4. **Storage Tests**: Cross-provider storage functionality verification
5. **Docker Integration Tests**: Comprehensive testing with actual Docker services (PostgreSQL, MinIO S3, Flask app)

### Test Isolation Patterns
- **Test Database**: Separate database instance for testing
- **Temporary Storage**: Auto-cleaning storage for file operations
- **Mock External Services**: Isolate tests from external dependencies
- **Fixture Management**: Reusable test data setup

### Docker Testing Patterns
**Comprehensive Docker-based integration testing**
- **Separate Configuration**: `pytest.docker.ini` for Docker-specific test configuration with environment variables for S3/MinIO and PostgreSQL
- **Dedicated Fixtures**: `tests/docker/conftest.py` provides Docker-specific fixtures for app configuration, test clients, and browser automation
- **Service Verification**: Automatic checks for running Docker containers (PostgreSQL, MinIO, web) before test execution
- **Test Markers**: `@pytest.mark.docker` marker required for all Docker tests to prevent accidental execution
- **Environment Isolation**: Docker tests run in separate directory (`tests/docker/`) with dedicated configuration
- **Real Service Testing**: Tests interact with actual S3/MinIO storage and PostgreSQL database instead of mocks
- **Browser Automation**: Playwright fixtures configured for Docker environment with proper networking and authentication
- **Database Cleanup**: Automatic rollback of database changes and media cleanup after each test
- **Configuration Profiles**: Different app configurations for Docker testing (production, debug, testing modes with S3 storage)

## Error Handling Patterns

### Structured Error Responses
- **HTTP Status Codes**: Appropriate status codes for different error types
- **JSON Error Format**: Consistent error response structure for API calls
- **User-Friendly Messages**: Contextual error messages for end users
- **Logging Integration**: Comprehensive error logging for debugging

### Exception Hierarchy
- **Application Exceptions**: Business logic errors with specific handling
- **Validation Errors**: Input validation failures with field-specific messages
- **Authorization Errors**: Access control violations
- **Storage Errors**: File operation failures with recovery strategies

## Configuration Patterns

### Environment-Based Configuration
- **Environment Variables**: Sensitive data and environment-specific settings
- **Configuration Classes**: Structured configuration with inheritance
- **Development/Production Profiles**: Different settings per environment
- **Test Configuration**: Isolated configuration for testing

### Service Configuration
- **Dependency Injection**: Services configured at application startup
- **Runtime Configuration**: Dynamic configuration based on environment
- **Feature Flags**: Conditional feature enabling/disabling
- **Storage Provider Selection**: Runtime storage strategy selection

## Deployment Patterns

### Container-Ready Architecture
- **Stateless Application**: Session data in secure cookies or database
- **Externalized Configuration**: Environment variables for all sensitive data
- **Health Checks**: Readiness and liveness endpoints
- **Logging Standards**: Structured logging for container environments

### Scalability Considerations
- **Database Connection Pooling**: Efficient database resource management
- **Stateless Services**: Horizontal scaling capability
- **Caching Strategy**: Potential for Redis/memcached integration
- **Background Processing**: Async task support for long-running operations