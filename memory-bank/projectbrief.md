# Project Brief: CleanIt Job Management System

## Overview
CleanIt is a web-based job management system designed for cleaning businesses to efficiently manage cleaning jobs, teams, and users. The system provides role-based dashboards for admins, supervisors, and users with interactive job scheduling, assignment, and tracking capabilities.

## Core Purpose
To streamline cleaning business operations by providing a centralized platform for job management, team coordination, and real-time status tracking.

## Key Objectives
1. **Centralized Job Management**: Single source of truth for all cleaning jobs across multiple properties and teams
2. **Role-Based Access Control**: Different interfaces and permissions for owners, team leaders, and cleaners
3. **Interactive Scheduling**: Drag-and-drop job assignment and real-time timetable updates
4. **Media Management**: Upload and organize job-related photos and documents
5. **Mobile-First Design**: Responsive interface accessible on all devices
6. **Progressive Enhancement**: Server-rendered core with htmx for interactive features

## Target Users
- **Admins**: Business administrators with full system access and management capabilities
- **Supervisors**: Team supervisors who oversee job completion and have access to property access codes
- **Users**: Individual cleaners who complete assigned jobs with limited access to sensitive information

## Success Metrics
- Reduced time spent on job scheduling and assignment
- Improved team coordination and communication
- Increased job completion rates and customer satisfaction
- Reduced administrative overhead for business owners

## Project Scope
### In Scope
- User authentication and role management
- Job creation, assignment, and tracking
- Team management and member assignment
- Property management with job history
- Media uploads and gallery for job documentation
- Interactive timetable with drag-and-drop functionality
- Real-time job status updates
- Mobile-responsive web interface

### Out of Scope
- Mobile native applications (web-first approach)
- Complex accounting/invoicing systems
- GPS tracking of cleaners
- Customer-facing portals
- Advanced analytics and reporting (beyond basic job tracking)

## Technical Foundation
- **Backend**: Flask (Python) with SQLAlchemy ORM
- **Frontend**: Jinja2 templates with htmx for interactivity
- **Database**: SQLite (development), PostgreSQL/MySQL (production)
- **Storage**: Cloud-first approach with S3/local storage options
- **Styling**: Custom CSS with CSS variables for theming (no TailwindCSS)
- **Testing**: pytest with comprehensive test suite

## Project Status
Active development with core functionality implemented. The system is functional with ongoing feature enhancements and testing improvements.

## Key Decisions
1. **Framework Selection**: Flask chosen for Python web development
2. **Progressive Enhancement**: htmx used for interactive features while maintaining server-side rendering
3. **Storage Strategy**: Cloud-first with S3 as primary, temporary local storage for testing/development
4. **Role-based permissions**: Three-tier permission system (admin, supervisor, user)
5. **Mobile-first design**: Prioritizing mobile accessibility for field workers
6. **Testing Approach**: Combination of pytest for unit/integration tests and Playwright for end-to-end testing

## Next Phase Focus
- Enhancing media gallery functionality
- Improving test coverage
- Performance optimizations
- Documentation and deployment automation