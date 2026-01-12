# Active Context: Current Development Focus

## Current Work Focus
**Media Gallery System Redesign** - Rethinking the architecture for media management to create a more robust, scalable, and maintainable system for handling job and property media collections.

## Immediate Goals
1. **Complete Media Gallery Implementation** with proper separation of concerns
2. **Redesign gallery access patterns** for better performance and usability
3. **Implement proper service layer architecture** for media management

## Architecture Redesign Plan

### Service Layer Responsibilities

#### Media Service
- **Primary Responsibility**: Handle storage operations for media files
- **Key Functions**:
  - Store media files to appropriate storage (disk, S3, temp based on configuration)
  - Resolve media URLs for frontend access
  - Delete media files from storage
  - Generate unique filenames and paths
  - Handle file validation and security checks

#### Gallery Service  
- **Primary Responsibility**: Manage media collections for entities (jobs, properties)
- **Key Functions**:
  - Collect and update media collections for specific entities
  - Maintain relationships between entities and their media
  - Handle collection metadata and organization
  - Coordinate with Media Service for storage operations
  - Provide query interfaces for retrieving entity media

### Controller Layer Updates

#### Job Controller Updates
- **New Endpoints**:
  - `POST /jobs/{job_id}/media` - Add/update job media collection
  - `GET /jobs/{job_id}/media` - Retrieve job media collection
  - `DELETE /jobs/{job_id}/media` - Remove media from job collection
- **Responsibilities**:
  - Receive job identifiers and raw media data
  - Handle incoming file uploads and existing media URLs
  - Leverage Media Service for storage operations
  - Use Gallery Service for collection management
  - Process deletion requests (IDs excluded from collection should be deleted)

#### Property Controller Updates
- **New Endpoints**:
  - `POST /properties/{property_id}/media` - Add/update property media collection
  - `GET /properties/{property_id}/media` - Retrieve property media collection
  - `DELETE /properties/{property_id}/media` - Remove media from property collection
- **Responsibilities**:
  - Similar to Job Controller but for properties
  - Handle property-specific media requirements
  - Maintain property-media relationships

### Data Flow Pattern
1. **Client Request** → Controller with entity ID and media data
2. **Controller** → Validates request, extracts entity context
3. **Gallery Service** → Manages collection logic, determines changes needed
4. **Media Service** → Handles actual storage operations (save/delete)
5. **Response** → Updated collection metadata returned to client

### Collection Update Logic
- **Inclusion-based updates**: Client sends complete list of media IDs to keep
- **Exclusion-based deletion**: Any media IDs not in the received list are deleted
- **New media handling**: Raw file data processed and added to collection
- **URL references**: Existing media URLs preserved in collection

## Technical Implementation Details

### Storage Configuration Support
- **S3 Storage**: Primary production storage with URL resolution
- **Local Disk**: Development and testing storage
- **Temporary Storage**: Test-specific storage that auto-cleans
- **Configuration-driven**: Storage provider selected via app config

### Media Metadata
- **Entity relationship**: Media linked to jobs or properties
- **File metadata**: Original filename, storage path, MIME type, size
- **Collection context**: Position in collection, tags, descriptions
- **Access control**: Role-based visibility (admin, supervisor, user)

### API Design Considerations
- **Batch operations**: Support multiple file uploads in single request
- **Progress tracking**: Handle large file uploads with progress indication
- **Error handling**: Graceful failure with partial success support
- **Validation**: File type, size, and security validation

## Current Status
- **Existing Code**: Basic media controller and service implementations exist
- **Gallery Components**: Frontend gallery modal and JavaScript components created
- **Testing**: Some test coverage exists but needs expansion
- **Integration**: Media functionality partially integrated with jobs/properties

## Next Steps
1. **Analyze current media service implementation** to identify gaps
2. **Design Gallery Service interface** and data models
3. **Update Job and Property controllers** to use new service architecture
4. **Implement collection update logic** with proper deletion handling
5. **Update frontend components** to work with new API patterns
6. **Expand test coverage** for new service layer

## Error Handling and Frontend Feedback

### Current Error Handling Approach
- **`_form_response.html` template**: Currently used for relaying errors and feedback to users in form contexts
- **Form-specific implementation**: Works well for form submissions but lacks global consistency
- **HTMX integration**: Partial support for dynamic error display via HTMX swaps

### Requirements for Global Error Handling
1. **Consistent Error Presentation**: Unified error display across all application interfaces
2. **HTMX Compatibility**: Errors must be swappable via HTMX `hx-swap` operations for dynamic content
3. **Strategic Positioning**: Global error container with fixed positioning for maximum visibility
4. **Error Type Support**: Accommodate validation errors, server errors, authorization errors, and success messages
5. **User Experience**: Temporary display with auto-dismissal or manual dismissal options
6. **Context Preservation**: Maintain user workflow context when errors occur

### Proposed Implementation
1. **Global Error Container Component**: Create reusable `_error_display.html` component
2. **Standardized Error Response Format**: Consistent HTML/JSON structure for error responses
3. **HTMX Target Integration**: Designate `id="global-error-container"` for error injection
4. **Error Severity Levels**: Visual differentiation (info, warning, error, success)
5. **Animation Support**: Smooth transitions for error appearance and dismissal
6. **Backward Compatibility**: Maintain `_form_response.html` support for existing forms

### Integration with Media Gallery Redesign
- **Gallery-specific error handling**: Media upload failures, storage errors, validation errors
- **Inline error feedback**: Contextual error display within gallery modals
- **Batch operation feedback**: Success/error reporting for multiple file operations
- **Recovery guidance**: Clear user instructions for error resolution

### Implementation Steps
1. **Design error component**: Create visually consistent error display template
2. **Update error handlers**: Modify global error handlers to use new component
3. **HTMX integration**: Configure HTMX to target global error container
4. **JavaScript enhancement**: Add optional auto-dismissal and interaction features
5. **Testing**: Verify error display across all user workflows and error types

## Dependencies and Constraints
- **Database Schema**: May require updates to media relationship models
- **Frontend Integration**: JavaScript gallery components need updating
- **Testing Infrastructure**: Ensure all storage configurations work in tests
- **Error Handling Consistency**: Need to maintain backward compatibility during transition

## Success Criteria
- **Complete separation** of storage and collection management concerns
- **All media operations** work across all storage configurations
- **Job and property media** can be managed through unified API patterns
- **Collection updates** properly handle additions and deletions
- **Frontend gallery** works seamlessly with new backend architecture