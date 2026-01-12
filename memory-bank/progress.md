# Progress: Current Status and What's Left to Build

## Current Status

### ✅ Completed and Working
- **User Management**: Authentication, role-based access (admin, supervisor, user), profiles
- **Job Management**: Creation, assignment, status tracking, timetable views
- **Team Management**: Team creation, membership, team-specific views
- **Property Management**: Property database with details and access codes
- **Basic Media Functionality**: Initial media controller and service implementations
- **Frontend Interface**: Responsive design, htmx interactions, drag-and-drop
- **Testing Foundation**: pytest unit tests, some integration tests

### 🚧 In Progress / Needs Completion
- **Media Gallery System**: Service layer redesign in progress
- **Gallery Service**: Not yet implemented - needed for collection management
- **Global Error Handling**: Need consistent HTMX-compatible error display
- **Test Coverage**: Needs expansion for controllers and storage providers

## Immediate Development Priorities

### 1. Media Gallery Redesign
**Current Focus**: Rethinking gallery access and service architecture

#### Tasks Required:
- **Media Service**: Update to handle storage paths, URL resolution, and saving media to disk based on configuration
- **Gallery Service**: Implement to manage media collections for properties and jobs
- **Controller Updates**: 
  - Update job and property controllers to handle media collection updates
  - Create endpoints for media collection management
  - Implement deletion logic (IDs excluded from collection should be deleted)
- **Frontend Integration**: Update gallery components to work with new API patterns

#### Service Responsibilities:
- **Media Service**: Storage operations, URL resolution, file handling
- **Gallery Service**: Collection management, entity-media relationships
- **Controllers**: Receive identifiers and raw data, delegate to services

### 2. Global Error Handling
**Requirement**: Consistent error display that works with HTMX

#### Current State:
- Using `_form_response.html` template for form errors
- Need global positioning for errors caught by error handlers
- Errors must be swappable via HTMX

#### Needed:
- Global error container component
- HTMX-compatible error response format
- Consistent error display across all interfaces

## What's Left to Build

### Media Gallery System
1. **Design and implement Gallery Service**
   - Collection management interface
   - Entity-media relationship handling
   - Update coordination with Media Service

2. **Update Media Service**
   - Proper storage abstraction
   - URL resolution for different storage providers
   - Configuration-based storage selection

3. **Update Controllers**
   - New media collection endpoints for jobs and properties
   - Batch update handling with inclusion/exclusion logic
   - Error handling and validation

4. **Update Frontend**
   - Gallery components to use new API
   - Error display integration
   - User feedback for media operations

### Error Handling System
1. **Design error display component**
   - Global positioning (top of viewport)
   - HTMX swap compatibility
   - Multiple error type support

2. **Update error handlers**
   - Consistent error response format
   - Integration with global error container
   - Backward compatibility for existing forms

### Testing
1. **Expand test coverage**
   - Media service tests for all storage providers
   - Gallery service unit tests
   - Controller integration tests
   - End-to-end media workflow tests

## Known Issues
- Media service needs proper storage abstraction
- No unified collection management service
- Inconsistent error handling across endpoints
- Test gaps for storage provider compatibility

## Success Criteria for Current Phase
- Media gallery system complete with proper service separation
- Global error handling working with HTMX
- All media operations work across storage configurations
- Comprehensive test coverage for new functionality