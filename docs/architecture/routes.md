# Flask Routes Specification

## Authentication Routes

### GET /login
- **Purpose**: Render login form
- **Access**: Public
- **Behavior**: Redirects authenticated users to appropriate dashboard
- **Response**: Renders `auth/login.html`

### POST /login
- **Purpose**: Authenticate user credentials
- **Access**: Public
- **Parameters**: username, password
- **Behavior**: Sets session and redirects based on user role
- **Response**: Redirect to dashboard or error message

### GET /logout
- **Purpose**: Clear user session
- **Access**: Authenticated users only
- **Behavior**: Clears session data
- **Response**: Redirect to login page

### GET /register
- **Purpose**: Render user registration form
- **Access**: Owner only
- **Behavior**: Validates owner permissions
- **Response**: Renders `auth/register.html`

### POST /register
- **Purpose**: Create new user accounts
- **Access**: Owner only
- **Parameters**: username, email, password, first_name, last_name, role_id, team_id
- **Behavior**: Creates user with role assignment
- **Response**: Redirect to user management or error message

## Timetable Routes

### GET /timetable
- **Purpose**: Render main timetable view
- **Access**: Authenticated users (role-based filtering)
- **Behavior**: Filters jobs by selected date, organizes by team columns
- **Response**: Renders `timetable/timetable.html`

### GET /timetable/date/<date>
- **Purpose**: Return timetable for specific date
- **Access**: Authenticated users
- **Parameters**: date (YYYY-MM-DD format)
- **Behavior**: Used for date navigation via htmx
- **Response**: Renders timetable partial or full page

### POST /update-job-assignment
- **Purpose**: Update job team assignment via drag-and-drop
- **Access**: Team leaders and owners only
- **Parameters**: job_id, new_team_id
- **Behavior**: Validates permissions, updates database
- **Response**: Returns updated team column HTML via htmx

### GET /job/<job_id>
- **Purpose**: Render job details modal
- **Access**: Authenticated users (role-based access)
- **Behavior**: Used for viewing/editing job information
- **Response**: Renders job details partial

### POST /job/<job_id>/update
- **Purpose**: Update job details
- **Access**: Team leaders and owners only
- **Parameters**: Various job attributes
- **Behavior**: Updates job in database
- **Response**: Returns updated job card HTML via htmx

### POST /job/create
- **Purpose**: Create new job
- **Access**: Team leaders and owners only
- **Parameters**: Job creation data
- **Behavior**: Creates new job in database
- **Response**: Returns new job card HTML via htmx

## Admin Routes

### GET /admin/users
- **Purpose**: User management interface
- **Access**: Owner only
- **Behavior**: List, create, edit, delete users
- **Response**: Renders `admin/users.html`

### POST /admin/users/<user_id>/update-role
- **Purpose**: Update user role
- **Access**: Owner only
- **Parameters**: user_id, new_role_id
- **Behavior**: Validates permission changes
- **Response**: Returns updated user list via htmx

### GET /admin/teams
- **Purpose**: Team management interface
- **Access**: Owner only
- **Behavior**: Create, edit teams, assign team leaders
- **Response**: Renders `admin/teams.html`

### POST /admin/teams/create
- **Purpose**: Create new team
- **Access**: Owner only
- **Parameters**: team_name, description, team_leader_id
- **Behavior**: Creates team in database
- **Response**: Returns team list update via htmx

## Additional Justified Endpoints

### GET /api/jobs/date/<date>
- **Purpose**: JSON endpoint for job data
- **Access**: Authenticated users
- **Justification**: Mobile app integration and external systems
- **Response**: JSON array of job data

### GET /dashboard
- **Purpose**: Role-specific landing pages
- **Access**: Authenticated users
- **Justification**: Improved UX with role-specific views
- **Behavior**: Redirects based on user role
- **Response**: Appropriate dashboard view

### POST /job/<job_id>/complete
- **Purpose**: Mark job as completed
- **Access**: Assigned cleaners and team leaders
- **Justification**: Workflow completion tracking
- **Behavior**: Updates job status and records completion time
- **Response**: Updated job status via htmx

### GET /reports/team-performance
- **Purpose**: Team performance metrics
- **Access**: Owners and team leaders
- **Justification**: Business intelligence requirements
- **Behavior**: Generates performance reports
- **Response**: Renders performance dashboard

## Route Security

### Authentication Middleware
- All routes except `/login` require authentication
- Session-based authentication with secure cookies
- Automatic redirect to login for unauthenticated users

### Authorization Checks
- Role-based access control for all routes
- Team leaders can only access their team's data
- Cleaners can only view their assigned jobs
- Owners have full system access

### Input Validation
- All POST parameters validated and sanitized
- CSRF protection for form submissions
- SQL injection prevention via SQLAlchemy