# User Stories - CleanIt Job Management System

This document outlines user stories for the CleanIt job management system, focusing on user needs and functionalities without technical implementation details. The features are broken down into manageable components for easier understanding and development.

## Feature: Login and Permissions

### User Story: Role Based Permissions
**Priority: P0 (Urgent)**
As a user, I want to log in to the system with my credentials, so I can access my assigned functionalities and data.

**Acceptance Criteria:**
*   The system provides a login page with fields for username/email and password.
*   Upon successful authentication, the user is redirected to their role-specific dashboard.
*   Invalid credentials result in an error message without revealing specific details (e.g., "Invalid username or password").
*   The system securely handles password submission (e.g., hashing).

**Checklist:**
*   [x] Create a user's table in the database and a corresponding model
*   [x] Implement Flask route (`/login`) for displaying the login form (`templates/login.html`).
*   [x] Implement Flask route (`/login`, POST) to handle form submission and authentication.
*   [x] Integrate with a user management system (e.g., Flask-Login) for session management.
*   [x] Verify user credentials against the SQLite database.
*   [x] Redirect authenticated users to index.
*   [x] Display error messages for failed login attempts.


### User Story: Password Management
**Priority: P1 (High)**
As a user, I want to be able to change my password, so I can maintain the security of my account.

**Acceptance Criteria:**
*   Users can access a "change password" feature from their profile or settings.
*   The system requires the current password before allowing a new password to be set.
*   New passwords must meet defined complexity requirements (e.g., minimum length, special characters).
*   Upon successful password change, the user is notified.

**Checklist:**
*   [ ] Implement Flask route (`/change_password`) for displaying the password change form.
*   [ ] Implement Flask route (`/change_password`, POST) to handle form submission and password update.
*   [ ] Hash and salt new passwords before storing them in the database.
*   [ ] Validate new passwords against complexity requirements.
*   [ ] Implement authentication to ensure only the logged-in user can change their own password.
*   [ ] Provide user feedback on success or failure.

### User Story: User Registration (Owner Only)
**Priority: P2 (Medium)**
As the owner, I want to be able to register new users (cleaners and team leaders) and assign them roles, so I can manage my workforce within the system.

**Acceptance Criteria:**
*   Only users with the 'owner' role can access the user registration feature.
*   The owner can specify the new user's username/email, password, and role (cleaner or team leader).
*   Upon successful registration, the new user's account is created in the database with the assigned role.
*   The owner receives confirmation of the new user's creation.

**Checklist:**
*   [ ] Implement Flask route (`/register_user`) for displaying the user registration form.
*   [ ] Implement Flask route (`/register_user`, POST) to handle form submission and user creation.
*   [ ] Implement authorization to restrict access to this route to 'owner' role only.
*   [ ] Hash and salt the initial password for new users.
*   [ ] Store new user details and their assigned role in the SQLite database.
*   [ ] Provide feedback to the owner on successful registration or errors.



## Feature: Daily Job Timetable View

### User Story: Cleaner's Personalized Job List
**Priority: P1 (High)**
As a cleaner, I want to see only the jobs assigned to me for the current day, so I can focus on my specific tasks without distraction.

**Acceptance Criteria:**
*   The system displays a list of jobs specifically assigned to the logged-in cleaner for the current date.
*   No jobs assigned to other cleaners or teams are visible.
*   Sensitive job attributes (e.g., post-clean reports, pictures) are not displayed to the cleaner.
*   The job list is presented in a clear, easy-to-read format.

**Checklist:**
*   [ ] Implement Flask route (`/cleaner/jobs`) to fetch jobs for the authenticated cleaner.
*   [ ] Query SQLite database to retrieve jobs filtered by cleaner ID and current date.
*   [ ] Ensure only allowed job attributes are selected from the database for cleaners.
*   [ ] Render job list using Jinja2 template (`templates/job_cards.html`) with HTMX for dynamic updates.
*   [ ] Implement authentication and authorization to restrict access to cleaner-specific data.
*   [ ] Display a message if no jobs are assigned for the current day.
### User Story: Team Leader's Team Overview
**Priority: P2 (Medium)**
As a team leader, I want to view all jobs assigned to my team for the current day in a single list, so I can efficiently manage and monitor my team's progress.

**Acceptance Criteria:**
*   The system displays a list of all jobs assigned to the logged-in team leader's team for the current date.
*   The list includes essential job details (e.g., property address, time, assigned cleaner).
*   The team leader can quickly identify the status of each job (e.g., pending, in progress, completed).

**Checklist:**
*   [ ] Implement Flask route (`/team_leader/jobs`) to fetch jobs for the authenticated team leader's team.
*   [ ] Query SQLite database to retrieve jobs filtered by team ID and current date.
*   [ ] Render job list using Jinja2 template (`templates/job_cards.html`) with HTMX for dynamic updates.
*   [ ] Implement authentication and authorization to restrict access to team-specific data.
*   [ ] Display a message if no jobs are assigned to the team for the current day.

### User Story: Owner's Comprehensive Team Timetable
**Priority: P2 (Medium)**
As the owner, I want to see all jobs organized by team, with each team's jobs in a separate column for the current day, so I can get a complete overview of all operations and manage resources effectively.

**Acceptance Criteria:**
*   The system displays all jobs for the current day, grouped by team.
*   Each team's jobs are presented in a distinct column or section.
*   The owner can easily identify which jobs are assigned to which team.
*   The display provides a high-level overview of all ongoing operations.

**Checklist:**
*   [ ] Implement Flask route (`/owner/jobs`) to fetch all jobs for the current date.
*   [ ] Query SQLite database to retrieve all jobs for the current date, including team assignments.
*   [ ] Process job data to group jobs by team in the Flask application.
*   [ ] Render the grouped job data using a Jinja2 template (`templates/index.html` or similar) with HTMX for dynamic updates.
*   [ ] Implement authentication and authorization to restrict access to owner-specific data.
*   [ ] Ensure the UI clearly separates jobs by team (e.g., using distinct columns or sections).

## Feature: Interactive Job Cards

### User Story: Access Job Details
**Priority: P1 (High)**
As a user, I want to click on a job card to view its detailed information in a pop-up, so I can quickly access all necessary specifics about a clean.

**Acceptance Criteria:**
*   Clicking a job card triggers a pop-up or modal displaying detailed job information.
*   The pop-up content is dynamically loaded based on the selected job.
*   The pop-up can be closed easily by the user.
*   The displayed information is relevant to the user's role (read-only for cleaners, editable for team leaders/owners).

**Checklist:**
*   [ ] Implement HTMX `hx-get` attribute on job cards to fetch job details.
*   [ ] Create a Flask route (`/job/<job_id>/details`) to return a Jinja2 template fragment for the pop-up.
*   [ ] Query SQLite database for specific job details based on `job_id`.
*   [ ] Render job details within a Jinja2 template (`templates/job_details_modal.html` or similar).
*   [ ] Implement HTMX `hx-target` and `hx-swap` to display the pop-up content.
*   [ ] Ensure appropriate styling for the pop-up (CSS).

### User Story: Assign Jobs to Teams (Owner)
**Priority: P3 (Low)**
As the owner, I want to be able to drag and drop job cards between team columns, so I can easily assign and reassign jobs to different teams as needed.

**Acceptance Criteria:**
*   Job cards are draggable and can be dropped into different team columns.
*   Dropping a job card into a new team column updates its assigned team in the database.
*   The UI reflects the change immediately without a full page reload.
*   Only users with the 'owner' role can perform this action.

**Checklist:**
*   [ ] Implement HTMX `hx-trigger="drop"` and `hx-post` on team columns to handle job assignment.
*   [ ] Implement HTMX `hx-swap` to update the UI after a successful drag-and-drop.
*   [ ] Create a Flask route (`/job/<job_id>/assign_team`) to handle the team assignment update.
*   [ ] Update the `team_id` for the specified job in the SQLite database.
*   [ ] Implement JavaScript for drag-and-drop functionality (if HTMX alone is insufficient).
*   [ ] Ensure proper authorization checks for the 'owner' role on the Flask route.

## Feature: Critical Job Highlighting

### User Story: Identify Back-to-Back Cleans
**Priority: P3 (Low)**
As a user, I want critical jobs that are scheduled back-to-back (small window between guest departure and arrival) to be clearly highlighted, so I can prioritize and ensure timely completion.

**Acceptance Criteria:**
*   Jobs with a short turnaround time between guest departure and arrival are automatically identified.
*   These critical jobs are visually highlighted on the job cards (e.g., distinct color, icon).
*   The highlighting is consistent across all timetable views (cleaner, team leader, owner).

**Checklist:**
*   [ ] Implement logic in Flask to calculate the time difference between consecutive bookings for a property.
*   [ ] Define a threshold for "small window" (e.g., less than 3 hours).
*   [ ] Add a `is_back_to_back` flag to job data if the condition is met.
*   [ ] Modify Jinja2 templates (`templates/job_cards.html`) to apply CSS classes or display icons based on `is_back_to_back` flag.
*   [ ] Ensure CSS (`static/css/style.css`) defines distinct styling for highlighted job cards.

### User Story: Identify Next-Day Arrival Cleans
**Priority: P3 (Low)**
As a user, I want jobs for properties with a guest arriving the next day to be clearly highlighted, so I know these cleans must be completed today.

**Acceptance Criteria:**
*   Jobs for properties with a guest arrival scheduled for the *next day* are automatically identified.
*   These jobs are visually highlighted on the job cards (e.g., distinct color, icon).
*   The highlighting is consistent across all timetable views.

**Checklist:**
*   [ ] Implement logic in Flask to check for guest arrivals on the day following the current job.
*   [ ] Add an `is_next_day_arrival` flag to job data if the condition is met.
*   [ ] Modify Jinja2 templates (`templates/job_cards.html`) to apply CSS classes or display icons based on `is_next_day_arrival` flag.
*   [ ] Ensure CSS (`static/css/style.css`) defines distinct styling for highlighted job cards.

## Feature: Job Editor Popup

### User Story: View Job Details (Cleaner)
**Priority: P1 (High)**
As a cleaner, when I click on a job card, I want to see a read-only pop-up with all job attributes, so I have all the information I need to perform the clean.

**Acceptance Criteria:**
*   Clicking a job card displays a read-only pop-up with relevant job details.
*   The pop-up includes all necessary information for a cleaner to perform their task (e.g., property address, access codes, specific instructions).
*   Sensitive information (e.g., post-clean reports, pictures) is not displayed.
*   The pop-up is easily dismissible.

**Checklist:**
*   [ ] Implement a Flask route (`/cleaner/job/<job_id>`) to fetch read-only job details.
*   [ ] Query SQLite database for job details, ensuring sensitive data is excluded for cleaners.
*   [ ] Render job details in a read-only Jinja2 template fragment (`templates/cleaner_job_modal.html`).
*   [ ] Integrate with HTMX to display the modal when a job card is clicked.
*   [ ] Ensure the modal has a clear close button or mechanism.

### User Story: Edit Job Details (Team Leader & Owner)
**Priority: P2 (Medium)**
As a team leader or owner, when I click on a job card, I want to see an editable pop-up with all job attributes, so I can update job details as necessary.

**Acceptance Criteria:**
*   Clicking a job card displays an editable pop-up with all job attributes.
*   Users with 'team leader' or 'owner' roles can modify job details within the pop-up.
*   Changes made are saved to the database upon submission.
*   The UI updates to reflect the saved changes without a full page reload.

**Checklist:**
*   [ ] Implement a Flask route (`/job/<job_id>/edit`) to fetch editable job details.
*   [ ] Query SQLite database for all job attributes based on `job_id`.
*   [ ] Render job details in an editable Jinja2 template fragment (`templates/job_editor_modal.html`).
*   [ ] Integrate with HTMX to display the modal and handle form submission (`hx-post`).
*   [ ] Implement a Flask route (`/job/<job_id>/update`) to handle form submission and update the SQLite database.
*   [ ] Ensure proper authorization checks for 'team leader' and 'owner' roles.
*   [ ] Provide clear feedback to the user on successful save or errors.

### User Story: Access Post-Clean Information (Team Leader & Owner)
**Priority: P2 (Medium)**
As a team leader or owner, I want to view the post-clean report and pictures within the job editor pop-up, so I can verify the quality of the clean and address any issues.

**Acceptance Criteria:**
*   The job editor pop-up includes a section to display the post-clean report.
*   Pictures uploaded by cleaners after a job are visible within this section.
*   Team leaders and owners can access and review this information.

**Checklist:**
*   [ ] Modify the Flask route (`/job/<job_id>/edit`) to fetch post-clean report and picture data.
*   [ ] Query SQLite database for post-clean details and associated image paths.
*   [ ] Update the Jinja2 template (`templates/job_editor_modal.html`) to display the report text and images.
*   [ ] Ensure proper authorization checks for 'team leader' and 'owner' roles.
*   [ ] Implement image display (e.g., `<img>` tags) and potentially a gallery/viewer if multiple images exist.

### User Story: Create New Job (Owner)
**Priority: P1 (High)**
As the owner, I want to be able to create a new job directly from the timetable view by clicking a "Create Job" or a plus button, which brings up a blank, editable job modal pop-up, so I can efficiently add new jobs to the database and see them immediately reflected on the timetable.

**Acceptance Criteria:**
*   A "Create Job" button or a prominent plus icon is visible on the owner's timetable view.
*   Clicking this button/icon displays a blank, editable job modal pop-up.
*   The pop-up contains all necessary fields for creating a new job (e.g., property address, date, time, assigned team/cleaner, job type, notes).
*   Upon submission, the new job is saved to the database.
*   The newly created job is immediately visible on the timetable view without a full page reload.
*   Only users with the 'owner' role can access this feature.

**Checklist:**
*   [ ] Add a "Create Job" button or plus icon to the owner's timetable template (`templates/index.html` or similar).
*   [ ] Implement HTMX `hx-get` on the button to fetch a blank job creation form.
*   [ ] Create a Flask route (`/job/create`) to return a blank Jinja2 template fragment for the job creation modal.
*   [ ] Render an empty job form within a Jinja2 template (`templates/job_editor_modal.html` or a dedicated `templates/job_create_modal.html`).
*   [ ] Implement HTMX `hx-post` on the form within the modal to handle submission.
*   [ ] Create a Flask route (`/job/save`) to handle form submission and save the new job to the SQLite database.
*   [ ] Ensure proper authorization checks for the 'owner' role on the Flask routes.
*   [ ] Implement HTMX `hx-trigger` and `hx-swap` to refresh the timetable view after successful job creation.
*   [ ] Provide clear feedback to the user on successful creation or errors.