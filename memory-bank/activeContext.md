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

## Error Handling Improvements: 404 Page and Global Error Handlers

### New 404 Page Implementation
- **Dedicated 404 Template**: Created `templates/not_found.html` with user-friendly design
- **Consistent Styling**: Uses application's CSS variables and design system
- **Helpful Navigation**: Includes links to timetable, back navigation, and admin-specific routes
- **Responsive Design**: Mobile-friendly layout with appropriate scaling
- **Debug Information**: Shows request details when in debug mode

### Global Error Handler Enhancements
- **Centralized Error Handling**: Added `register_general_error_handlers()` function in `utils/error_handlers.py`
- **404 Handler**: Custom handler that serves JSON for API requests and HTML for UI requests
- **Authentication Integration**: Unauthenticated users are redirected to login page via Flask-Login's unauthorized handler regardless of the existence of the route
- **500 Handler**: Basic internal server error handler with appropriate responses
- **Media-Specific Handling**: Existing `MediaNotFound` handler remains for specialized media error handling

### Technical Implementation Details
1. **Template Features**:
   - Large error code display (404) with visual emphasis
   - Clear error message explaining the issue
   - Action buttons for common navigation paths
   - SVG icons for visual reinforcement
   - Debug information section for development

2. **CSS Integration**:
   - Added error page styles to `static/css/style.css` (reusable `.error-*` classes)
   - Responsive breakpoints for mobile devices
   - Consistent use of CSS custom properties (variables)

3. **Handler Logic**:
   - **JSON API Requests**: Returns structured JSON error response
   - **HTML UI Requests**: Renders full `not_found.html` template
   - **Authentication Check**: Unauthenticated users invoke Flask-Login's unauthorized handler for redirect
   - **Logging**: All 404 errors are logged with request path
   - **Context**: Passes debug information and timestamps to template

### Integration Points
- **App Factory**: Registered via `register_general_error_handlers(app, login_manager)` in `app_factory.py`
- **Login Manager Integration**: 404 handler receives login_manager to invoke unauthorized handler
- **Existing Error System**: Complements existing `_form_response.html` for form errors
- **Media Error Handling**: Works alongside specialized `MediaNotFound` handler
- **HTMX Compatibility**: Returns proper HTML that can be swapped if needed

### Authentication Priority System
- **Authentication Dominance**: Unauthenticated requests to non-existent routes redirect to login page
- **Direct Invocation**: 404 handler calls `login_manager.unauthorized()` for unauthenticated users
- **Test Coverage**: Comprehensive test suite verifies authentication redirect behavior
- **Consistent UX**: Users always see login page first, then 404 page after authentication

### Benefits
1. **Improved User Experience**: Professional, helpful error pages instead of generic browser defaults
2. **Consistent Branding**: Maintains application's visual identity even in error states
3. **Better Debugging**: Development mode shows request details for troubleshooting
4. **API Compatibility**: Proper JSON responses for programmatic clients
5. **Maintainable Code**: Reusable CSS classes and template structure
6. **Security First**: Authentication takes precedence over 404 errors for unauthenticated users

### Testing Implementation
- **Comprehensive Test Suite**: Created `tests/test_error_handlers.py` with 6 tests
- **Authentication Tests**: Verify unauthorized users are redirected to login for non-existent routes
- **Authenticated Tests**: Verify authenticated users see proper 404 page
- **API Response Tests**: Verify JSON responses for API requests
- **Media Error Tests**: Verify MediaNotFound handler functionality
- **All Tests Passing**: 6/6 tests pass with the updated error handling implementation

### Environmental Configuration System Enhancement

### FLASK_ENV Configuration Implementation
- **Three Environment Modes**: Production, Debug, and Testing configurations now properly implemented
- **Configuration Classes**: Enhanced `config.py` with dedicated `DebugConfig` class for development
- **Runtime Selection**: Application factory selects configuration based on `FLASK_ENV` environment variable
- **Backward Compatibility**: Maintains support for `TESTING` flag in `config_override` parameter

### Configuration Details
1. **Production Configuration** (`FLASK_ENV=production`):
   - DEBUG: False
   - TESTING: False
   - Storage Provider: S3 (cloud storage)
   - Database: Production database (PostgreSQL/MySQL)
   - Security: Strict validation and error handling

2. **Debug Configuration** (`FLASK_ENV=debug`):
   - DEBUG: True (auto-reloading enabled)
   - TESTING: False
   - Storage Provider: Local filesystem (`./uploads`)
   - Database: Development database (SQLite)
   - Features: Enhanced logging, detailed error pages

3. **Testing Configuration** (`FLASK_ENV=testing`):
   - DEBUG: False
   - TESTING: True
   - Storage Provider: Temporary storage (auto-cleaned)
   - Database: Test database with seeded dummy data
   - Features: Deterministic test data, isolated test environment

### Implementation Changes
- **Updated `config.py`**: Added `DebugConfig` class with debug-specific settings
- **Enhanced `app_factory.py`**: Improved configuration selection logic with proper environment variable handling
- **Documentation Updates**: Added FLASK_ENV documentation to:
  - `Dockerfile` (with valid values explanation)
  - `docker-compose.yml` (environment variable documentation)
  - `set_environment_variables.py` (interactive setup guidance)
  - `memory-bank/techContext.md` (technical documentation)

### Validation and Testing
- **Configuration Tests**: Verified all three FLASK_ENV modes work correctly
- **Storage Provider Selection**: Confirmed each mode uses appropriate storage (S3, local, temp)
- **Backward Compatibility**: Verified `TESTING` flag in `config_override` still works
- **Application Startup**: Tested application creation with each configuration

### Usage Guidelines
- **Development**: Set `FLASK_ENV=debug` for auto-reloading and local storage
- **Testing**: Set `FLASK_ENV=testing` for isolated test environment with seeded data
- **Production**: Set `FLASK_ENV=production` (default) for S3 storage and production settings
- **Environment Variables**: Use `set_environment_variables.py` script for guided setup

## Error Handling and Frontend Feedback

### Current Error Handling Approach
- **`_form_response.html` template**: Currently used for relaying errors and feedback to users in form contexts
- **Form-specific implementation**: Works well for form submissions but lacks global consistency
- **HTMX integration**: Partial support for dynamic error display via HTMX swaps
- **New 404 Page**: Dedicated template for page not found errors with consistent styling

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

## Gallery Image Display Fix (NEW)

### Issue Identified
When running the application and uploading images to the gallery, images were uploaded successfully and filenames became visible, but the gallery displayed "media could not be loaded" placeholder instead of actual image content.

### Root Cause Analysis
1. **Docker Networking Issue**: The application uses MinIO (S3-compatible storage) in Docker development environment
2. **Internal vs. External Hostnames**: Images were uploaded to MinIO at internal Docker hostname `minio:9000`
3. **Presigned URL Problem**: `get_file_url()` returned presigned URLs with internal hostname `minio:9000`
4. **Signature Invalidation**: Changing hostname to `localhost:9000` for browser access invalidated AWS signature in presigned URLs

### Solution Implemented
1. **Updated `utils/storage.py`** - Modified `get_file_url()` function to:
   - Use configurable public hostname and port via `S3_PUBLIC_HOST` and `S3_PUBLIC_PORT` environment variables
   - Construct direct public URLs for MinIO (e.g., `http://localhost:9000/{bucket}/{filename}`) instead of presigned URLs
   - Fall back to intelligent defaults when environment variables aren't set

2. **Updated `docker-compose.yml`** - Added environment variables:
   ```yaml
   S3_PUBLIC_HOST: ${S3_PUBLIC_HOST:-localhost}
   S3_PUBLIC_PORT: ${S3_PUBLIC_PORT:-9000}
   ```
   This makes the public hostname configurable rather than hardcoded

3. **Created comprehensive test** - Added `test_gallery_display_with_fixed_url_generation()` to `tests/test_docker_gallery_s3_features.py` that:
   - Uploads test images from `tests/media/` directory
   - Verifies URLs are correctly generated using configured public hostname
   - Ensures URLs don't contain internal hostnames or signature parameters

### Key Improvements
- ✅ Images now display correctly in the gallery (not placeholders)
- ✅ Public hostname is configurable via environment variables
- ✅ No hardcoded `localhost` or `minio` hostnames
- ✅ Works with Docker networking (internal vs. external hostnames)
- ✅ Comprehensive test coverage for the fix
- ✅ Backward compatible with existing configuration

### Configuration Options
- **Default**: `S3_PUBLIC_HOST=localhost`, `S3_PUBLIC_PORT=9000` (Docker Compose default mapping)
- **Custom**: Set `S3_PUBLIC_HOST` and `S3_PUBLIC_PORT` to match your deployment environment
- **Production**: For real S3, use appropriate public endpoint or CDN URL

## Docker-Specific Playwright Fixtures (NEW)

### Comprehensive Docker Testing Infrastructure
A complete set of Playwright fixtures has been implemented in [`tests/conftest_docker.py`](tests/conftest_docker.py) for testing the application in Docker environments with S3/MinIO storage and PostgreSQL database.

### Key Fixtures Implemented

#### Core Browser Fixtures
- `docker_playwright_browser`: Session-scoped Playwright browser with Docker-appropriate arguments (`--no-sandbox`) and `--headed` flag support
- `docker_browser_context`: Function-scoped browser context for test isolation
- `docker_page`: Function-scoped page with 5-second navigation timeout
- `docker_server_url`: Base URL from pytest-flask's `live_server` using `docker_app`

#### Authentication Fixtures
- `_create_docker_auth_state`: Helper function for creating authentication state with Docker-specific browser and server
- `docker_admin_auth_state`, `docker_supervisor_auth_state`, `docker_user_auth_state`: Session-scoped authentication state fixtures for different user roles
- `docker_admin_context`, `docker_supervisor_context`, `docker_user_context`: Authenticated browser contexts
- `docker_admin_page`, `docker_supervisor_page`, `docker_user_page`: Pre-authenticated pages that navigate to `/jobs/`

#### Utility Fixtures
- `docker_goto`: Helper for navigating to paths within the Docker-based application
- `docker_rollback_db_after_test`: Database isolation fixture that cleans up media and re-seeds data after each test

### Design Decisions
1. **Separate naming convention**: All fixtures use `docker_` prefix to avoid conflicts with existing fixtures in [`tests/conftest.py`](tests/conftest.py)
2. **Docker-specific configuration**: Uses `docker_app` and `docker_app_no_csrf` for proper Docker environment setup with S3 storage
3. **Proper test isolation**: Each test gets fresh browser contexts and pages
4. **Database cleanup**: Media tables are cleaned and database is re-seeded after each test
5. **Compatibility**: Works with pytest-flask's `live_server` fixture which automatically picks up `docker_app`
6. **Headed browser support**: Respects pytest's `--headed` flag for visible browser windows during debugging

### Usage
Tests can use Docker fixtures by declaring:
```python
# Import Docker fixtures
pytest_plugins = ["tests.conftest_docker"]

def test_example(docker_admin_page):
    # Test using Docker-specific fixtures
    docker_admin_page.goto("/jobs/")
```

### Benefits
- **Isolated Docker testing**: Tests run against actual S3/MinIO storage and PostgreSQL database
- **Consistent authentication**: Pre-authenticated pages reduce test setup complexity
- **Debugging support**: `--headed` flag works for visual debugging of Docker tests
- **Database isolation**: Clean database state between tests ensures test reliability

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
- **✅ Frontend gallery** works seamlessly with new backend architecture (COMPLETED)
- **✅ Gallery image display** fixed with configurable public hostnames (NEW)
- **✅ Docker-specific Playwright fixtures** implemented for comprehensive Docker environment testing (NEW)
