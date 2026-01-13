# Active Context: Current Development Focus

## Current Work Focus
**Media Service Refactoring and Gallery Implementation** - Comprehensive redesign to fix scope violations and implement proper media management with batch operations.

## Key Decisions Made
1. **Single Media Service Approach**: Keep existing Media Service (enhanced) rather than creating separate Gallery Service
2. **Controller Scope Fix**: Move media operations from Media Controller to Job/Property controllers
3. **Batch Operations**: Add batch upload and delete methods for efficient gallery management
4. **Simplified Architecture**: Avoid over-engineering with two services when one can handle both storage and collections

## Architecture Redesign Plan

### Service Layer Responsibilities

#### Enhanced Media Service (Single Service)
- **Primary Responsibility**: Handle both storage operations AND collection management
- **Key Functions**:
  - Store media files to appropriate storage (disk, S3, temp based on configuration)
  - Resolve media URLs for frontend access
  - Manage entity-media relationships (property/job associations)
  - Handle batch operations for efficient gallery management
  - Generate unique filenames and paths
  - Handle file validation and security checks

**New Batch Methods Added**:
- `associate_media_batch_with_property/job()` - Batch association
- `disassociate_media_batch_from_property/job()` - Batch disassociation
- `upload_and_associate_with_property/job()` - Upload and associate in one operation

### Controller Layer Updates

#### Media Controller Refactoring
- **Methods to Remove** (move to Job/Property controllers):
  - `associate_media_with_property()`
  - `disassociate_media_from_property()`
  - `associate_media_with_job()`
  - `disassociate_media_from_job()`
- **Methods to Keep** (for direct file access):
  - `upload_media()` - Generic upload (not entity-specific)
  - `get_media()` - Get media metadata
  - `serve_media()` - Serve files
  - `delete_media()` - Delete media (admin only)

#### Job Controller Additions
- **New Endpoints**:
  - `GET /jobs/{job_id}/media` - Get job gallery
  - `POST /jobs/{job_id}/media` - Add media to job (single or batch)
  - `DELETE /jobs/{job_id}/media` - Remove media from job (batch)
  - `DELETE /jobs/{job_id}/media/{media_id}` - Remove single media

#### Property Controller Additions
- **New Endpoints** (mirroring Job controller):
  - `GET /properties/{property_id}/media` - Get property gallery
  - `POST /properties/{property_id}/media` - Add media to property (single/batch)
  - `DELETE /properties/{property_id}/media` - Remove media from property (batch)
  - `DELETE /properties/{property_id}/media/{media_id}` - Remove single media

### API Design

#### Batch Upload Request
```http
POST /jobs/123/media
Content-Type: multipart/form-data

files[]: [binary file 1]
files[]: [binary file 2]
descriptions[]: "First image"
descriptions[]: "Second image"
```

#### Batch Delete Request
```http
DELETE /jobs/123/media
Content-Type: application/json

{
  "media_ids": [1, 2, 3]
}
```

### Why This Approach is Better
1. **Less code duplication**: Media Service already has collection logic
2. **Simpler architecture**: Fewer services to maintain
3. **Easier migration**: Just move controller logic, don't rewrite service layer
4. **Solves actual problem**: Controller scope violations, not service responsibilities

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
- **✅ Phase 1: Media Service Enhancement**: COMPLETED
  - Enhanced Media Service with batch operations
  - Added `associate_media_batch_with_property/job()` methods
  - Added `disassociate_media_batch_from_property/job()` methods
  - Added `upload_and_associate_with_property/job()` methods
  - All media service tests passing (20/20)

- **✅ Phase 2: Controller Updates**: COMPLETED
  - Updated Job Controller with gallery methods (`get_job_gallery`, `add_job_media`, `remove_job_media`, `remove_single_job_media`)
  - Updated Property Controller with gallery methods (`get_property_gallery`, `add_property_media`, `remove_property_media`, `remove_single_property_media`)
  - Refactored Media Controller to remove association methods
  - All controller changes implemented

- **✅ Phase 3: Route Updates**: COMPLETED
  - Updated Job Routes with gallery endpoints (`/jobs/{job_id}/media`)
  - Updated Property Routes with gallery endpoints (`/address-book/property/{property_id}/media`)
  - Updated Media Routes to remove deprecated association endpoints
  - All route changes implemented

- **✅ Testing Implementation**: COMPLETED
  - Created comprehensive test suite for gallery endpoints (`tests/test_gallery_endpoints.py`)
  - All gallery endpoint tests passing (16/16)
  - Existing media controller tests passing for non-association functionality

- **🚧 Phase 4: Frontend Integration**: IN PROGRESS
  - Gallery JavaScript components need updates for new API
  - Batch upload functionality to be implemented
  - Batch delete functionality to be implemented
  - Error handling updates needed

- **🚧 Phase 5: Testing & Polish**: IN PROGRESS
  - Need to update old association tests or mark them as deprecated
  - Performance testing with large galleries needed
  - Documentation updates required

## Next Steps
1. **Update Gallery JavaScript** (`static/js/gallery*.js`) for new API endpoints
2. **Implement batch upload UI** with drag-and-drop integration
3. **Implement batch delete UI** with multi-select functionality
4. **Update templates** to use new gallery endpoints
5. **Update old association tests** in `tests/test_media_controller.py`
6. **Performance testing** with large galleries (50+ files)

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

### Implementation Steps for Frontend Integration
1. **Update Gallery JavaScript** to use new job/property gallery endpoints
2. **Implement batch upload UI** with drag-and-drop for multiple files
3. **Implement batch delete UI** with checkbox selection for multiple media items
4. **Update error handling** to use global error container for gallery operations
5. **Update templates** to trigger gallery with correct entity IDs and endpoints

## Dependencies and Constraints
- **Database Schema**: No schema changes needed - existing media relationship models work
- **Frontend Integration**: JavaScript gallery components need updating for new API
- **Testing Infrastructure**: All storage configurations work in tests
- **Error Handling Consistency**: Need to implement global error container for gallery operations

## Success Criteria
- **✅ Complete separation** of storage and collection management concerns
- **✅ All media operations** work across all storage configurations
- **✅ Job and property media** can be managed through unified API patterns
- **✅ Collection updates** properly handle additions and deletions
- **🚧 Frontend gallery** works seamlessly with new backend architecture (in progress)
