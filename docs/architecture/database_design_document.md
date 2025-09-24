# Relational Database Design for Cleaner Management Web Application

This document outlines the proposed relational database schema for the Cleaner Management Web Application, based on the `phase_one_requirements.md` document. The design focuses on a MySQL database, ensuring data integrity, efficient querying, and scalability for the described functionalities.

## 1. Core Entities and Their Justification

The following core entities have been identified from the requirements:

### 1.1. `Roles` Table
*   **Purpose**: To manage different access levels and permissions within the application (Cleaner, Team Leader, Owner). This centralizes role definitions and allows for easy modification and assignment.
*   **Attributes**:
    *   `role_id` (Primary Key, INT, AUTO_INCREMENT): Unique identifier for each role.
    *   `role_name` (VARCHAR(50), NOT NULL, UNIQUE): The name of the role (e.g., 'Cleaner', 'Team Leader', 'Owner'). Ensures role names are distinct.

### 1.2. `Users` Table
*   **Purpose**: To store information about all individuals who can log into and interact with the application.
*   **Attributes**:
    *   `user_id` (Primary Key, INT, AUTO_INCREMENT): Unique identifier for each user.
    *   `username` (VARCHAR(100), NOT NULL, UNIQUE): User's login name. Must be unique for authentication.
    *   `password_hash` (VARCHAR(255), NOT NULL): Stores a secure hash of the user's password.
    *   `role_id` (Foreign Key, INT, NOT NULL): Links a user to their assigned role in the `Roles` table. This enforces that every user must have a defined role.

### 1.3. `Teams` Table
*   **Purpose**: To organize cleaners into teams, which is crucial for the "Team leader: view/modify their team’s timetable" requirement and the Kanban-style view.
*   **Attributes**:
    *   `team_id` (Primary Key, INT, AUTO_INCREMENT): Unique identifier for each team.
    *   `team_name` (VARCHAR(100), NOT NULL, UNIQUE): The name of the team.
    *   `team_leader_id` (Foreign Key, INT, NULLABLE): Links a team to its designated team leader (a user with the 'Team Leader' role). It's nullable to allow for teams to be created before a leader is assigned.

### 1.4. `Jobs` Table (Phase 1 Implementation)
*   **Purpose**: To store details about each cleaning job that needs to be performed. In Phase 1, this table will directly contain location information.
*   **Attributes**:
    *   `job_id` (Primary Key, INT, AUTO_INCREMENT): Unique identifier for each job.
    *   `description` (TEXT, NOT NULL): Detailed description of the job.
    *   `location` (VARCHAR(255), NOT NULL): The physical location where the job is to be performed. This attribute will be used in Phase 1.
    *   `scheduled_date` (DATE, NOT NULL): The date on which the job is scheduled. Essential for the "Daily schedule filtered by date" requirement.
    *   `status` (VARCHAR(50), DEFAULT 'Pending'): Current status of the job (e.g., 'Pending', 'In Progress', 'Completed').

### 1.5. `Properties` Table (Future Phase 2 Integration)
*   **Purpose**: To store information about the physical locations (properties) that are cleaned. This table is introduced to allow for future expansion of property-specific details (e.g., address, contact person, specific cleaning instructions, recurring schedules). In Phase 2, the `location` attribute in the `Jobs` table will be replaced by a `property_id` foreign key linking to this table.
*   **Attributes**:
    *   `property_id` (Primary Key, INT, AUTO_INCREMENT): Unique identifier for each property.
    *   `address` (VARCHAR(255), NOT NULL): The physical address of the property.
    *   `name` (VARCHAR(255), NULLABLE): An optional name for the property (e.g., "Main Office", "Client X Residence").
    *   -- Additional attributes for Phase 2 development would go here (e.g., contact_person, special_instructions, recurring_schedule_id)

### 1.6. `Assignments` Table (Junction Table)
*   **Purpose**: To manage the many-to-many relationship between `Jobs` and `Teams`, and optionally to specific `Cleaners` within those teams. This table is critical for assigning jobs to teams and individual cleaners, and for enabling the drag-and-drop functionality.
*   **Attributes**:
    *   `assignment_id` (Primary Key, INT, AUTO_INCREMENT): Unique identifier for each assignment record.
    *   `job_id` (Foreign Key, INT, NOT NULL): Links to the `Jobs` table, indicating which job is being assigned.
    *   `team_id` (Foreign Key, INT, NOT NULL): Links to the `Teams` table, indicating which team is responsible for the job.
    *   `cleaner_id` (Foreign Key, INT, NULLABLE): Links to the `Users` table (specifically, users with the 'Cleaner' role). This allows for assigning a job to a specific cleaner within a team, or leaving it team-level if not specified.
    *   `UNIQUE (job_id, team_id, cleaner_id)`: Ensures that a specific job is assigned to a particular team and cleaner only once.

## 2. Relationships and Justification

The relationships between these tables are designed to reflect the business logic and security requirements, and to accommodate future expansion:

*   **`Users` to `Roles` (Many-to-One)**:
    *   **Justification**: Each user has exactly one role, but a single role can be assigned to multiple users. This is a standard way to implement role-based access control.
    *   **Implementation**: `Users.role_id` is a foreign key referencing `Roles.role_id`.

*   **`Teams` to `Users` (Many-to-One for Team Leader)**:
    *   **Justification**: Each team can have one designated team leader, who is a user. A user can be a leader of multiple teams (though typically one in practice, the schema allows for flexibility).
    *   **Implementation**: `Teams.team_leader_id` is a foreign key referencing `Users.user_id`.

*   **`Jobs` to `Properties` (Future Many-to-One)**:
    *   **Justification**: In Phase 1, `Jobs` will directly store `location`. In Phase 2, this will evolve to a many-to-one relationship where each job is performed at a specific property, but a single property can have many jobs scheduled for it over time. This relationship is key for future "persistent properties" requirements, allowing property details to be managed independently of individual jobs.
    *   **Implementation**: In Phase 1, `Jobs` will have a `location` column. In Phase 2, `Jobs.location` will be replaced by `Jobs.property_id` as a foreign key referencing `Properties.property_id`.

*   **`Assignments` to `Jobs` (Many-to-One)**:
    *   **Justification**: A single job can be part of multiple assignments (e.g., if a job is reassigned, or if it's a complex job with multiple phases assigned to different teams/cleaners over time, though the current requirements imply a single active assignment). An assignment record pertains to one specific job.
    *   **Implementation**: `Assignments.job_id` is a foreign key referencing `Jobs.job_id`.

*   **`Assignments` to `Teams` (Many-to-One)**:
    *   **Justification**: A team can have many assignments, and each assignment record is for one specific team. This supports the "Team leader: view/modify their team’s timetable" and Kanban view.
    *   **Implementation**: `Assignments.team_id` is a foreign key referencing `Teams.team_id`.

*   **`Assignments` to `Users` (Many-to-One for Cleaner)**:
    *   **Justification**: A cleaner can be assigned to many jobs, and each assignment record can optionally specify a particular cleaner. This supports the "Cleaner: view own schedule only" requirement.
    *   **Implementation**: `Assignments.cleaner_id` is a foreign key referencing `Users.user_id`.

## 3. Security Considerations

*   **Password Hashing**: The `password_hash` attribute in the `Users` table is crucial for security. Passwords should never be stored in plain text.
*   **Role-Based Access Control**: The `Roles` table and its relationship to `Users` forms the foundation for implementing the specified security clearances (Cleaner, Team Leader, Owner). Application logic will use the `role_id` to determine what actions a user can perform and what data they can view.

## 4. Data Integrity and Constraints

*   **Primary Keys**: Ensure unique identification for each record in a table.
*   **Foreign Keys**: Maintain referential integrity between related tables, preventing orphaned records.
*   **NOT NULL Constraints**: Enforce that critical data fields are always populated.
*   **UNIQUE Constraints**: Ensure uniqueness for fields like `username`, `role_name`, and `team_name`, and for the combination of `job_id`, `team_id`, and `cleaner_id` in `Assignments` to prevent duplicate assignments.

This database design provides a solid foundation for the Cleaner Management Web Application, addressing the core requirements for user management, role-based security, team organization, job scheduling, and assignment tracking, while also supporting the planned frontend functionalities like the Kanban view and drag-and-drop job reassignment.