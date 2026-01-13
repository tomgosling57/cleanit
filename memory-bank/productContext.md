# Product Context: CleanIt Job Management System

## Why This Project Exists

### Problem Statement
Cleaning businesses face significant operational challenges:
1. **Inefficient Job Scheduling**: Manual scheduling leads to conflicts, double-bookings, and missed appointments
2. **Poor Team Coordination**: Lack of real-time communication between admins, supervisors, and users
3. **Limited Visibility**: Admins struggle to track job progress and team performance
4. **Paper-Based Documentation**: Reliance on physical notes, photos, and reports leads to lost information
5. **Mobile Workforce Management**: Users in the field need access to job details without office visits
6. **Security Concerns**: Need to control access to sensitive information like property access codes

### Solution Vision
CleanIt provides a centralized digital platform that:
- **Streamlines Operations**: Automates scheduling, assignment, and tracking
- **Enhances Communication**: Real-time updates between all stakeholders
- **Improves Accountability**: Clear job status tracking and completion verification
- **Digitizes Documentation**: Centralized storage of job photos, notes, and reports
- **Supports Mobile Workforce**: Accessible on any device with internet connectivity

## How It Should Work

### Core User Workflows

#### Admin Workflow
1. **Dashboard Overview**: View all teams, jobs, and performance metrics at a glance
2. **Job Creation & Modification**: Create and modify cleaning jobs with property details, schedules, and requirements
3. **Team Management**: Create, modify, and manage teams and team assignments
4. **Property Management**: Create, modify, and manage properties including access codes
5. **User Management**: Create and manage users (admins, supervisors, users)
6. **Team Timetable**: View and manage the team timetable with drag-and-drop assignment
7. **Performance Monitoring**: Track job completion rates, team efficiency, and customer feedback
8. **Reporting**: Generate reports on business operations and team performance

#### Supervisor Workflow
1. **Daily Schedule**: View assigned daily schedule with job details and property information
2. **Access Codes**: View property access codes (not available to regular users)
3. **Job Completion**: Mark jobs as complete and upload completion images/reports
4. **Documentation**: Submit job completion reports with images for insurance and verification
5. **Address Book**: View the address book of properties
6. **Profile Management**: Update own profile information
7. **Job Details**: Access comprehensive job information including property details

#### User Workflow
1. **Daily Schedule**: View assigned daily schedule with job details
2. **Job Details**: Access job information (excluding property access codes)
3. **Profile Management**: Update own profile information
4. **Limited Property Access**: Cannot view address book or property access codes

### Key Interactions
1. **Interactive Timetable**: Visual drag-and-drop interface for job scheduling
2. **Job Cards**: Compact, information-rich cards showing job status and details
3. **Modal Interfaces**: Contextual modals for job creation, editing, and viewing details
4. **Media Gallery**: Organized storage and display of job-related photos
5. **Real-time Updates**: htmx-powered partial page updates without full reloads

## User Experience Goals

### Primary Goals
1. **Efficiency**: Reduce time spent on administrative tasks by 50%
2. **Accuracy**: Eliminate scheduling conflicts and missed appointments
3. **Transparency**: Provide real-time visibility into job status for all stakeholders
4. **Accessibility**: Ensure system works seamlessly on mobile devices for field workers
5. **Reliability**: Maintain system availability and data integrity

### Secondary Goals
1. **Scalability**: Support business growth from small teams to large operations
2. **Integration**: Potential for future integration with accounting and CRM systems
3. **Customization**: Allow configuration for different cleaning business models
4. **Analytics**: Provide insights for business optimization and decision-making

## Business Value Proposition

### For Admins (Business Administrators)
- **Full Control**: Complete management of jobs, teams, properties, and users
- **Increased Revenue**: More efficient scheduling allows more jobs per day
- **Reduced Costs**: Lower administrative overhead and fewer scheduling errors
- **Improved Customer Satisfaction**: Reliable service and professional documentation
- **Business Growth**: Scalable system supports expansion without proportional overhead increase
- **Security**: Granular control over sensitive information like property access codes

### For Supervisors
- **Enhanced Oversight**: Clear visibility into job completion and team performance
- **Documentation Control**: Ability to upload completion reports and images for insurance verification
- **Access to Sensitive Information**: View property access codes when needed
- **Reduced Administrative Burden**: Automated scheduling and communication reduces coordination stress
- **Professional Tools**: Digital platform enhances supervisory capabilities

### For Users (Cleaners)
- **Clear Instructions**: All necessary job details available in one place
- **Time Savings**: Reduced need for phone calls and office visits for information
- **Focused Interface**: Only see relevant information for assigned jobs
- **Security**: Protected from accessing sensitive property information
- **Professional Development**: Digital tools support career growth and accountability
