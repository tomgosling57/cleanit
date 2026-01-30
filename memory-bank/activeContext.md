# Active Context: Current Development Focus

## Current Work Focus
**Media Service Refactoring and Gallery Implementation** - Comprehensive redesign to fix scope violations and implement proper media management with batch operations.

**Docker Testing Configuration Enhancement** - Implementation of comprehensive Docker-based testing infrastructure with dedicated configuration files and fixtures for testing with PostgreSQL and S3/MinIO services.

## Key Decisions Made
1. **Media Controller and Services use Storage Utilities**: Separated the storage abstraction into utilities that are utilized by the media controller and services
2. **Reusable Media gallery component**: The media gallery component will be used in both the property reference galleries (available from the job details/address book views) as well as the job report (available to team leaders and admins who are marking a job as complete - not implemented yet)
3. **External Environment For E2E tests**: The end to end tests that are run using playwright (found in tests/e2e) will be executed outside of the docker application environment. They also have their own contest file and fixtures. 
4. **Universal timezone handler**: Timezone handling has been implemented as a utility and is configured as part of the environment variables. For enter end testing and development or production they should be set using the set_env.py script.


## Implementation Status

### 1. Media Controller and Services use Storage Utilities
- **Storage abstraction**: Implemented in [`utils/storage.py`](utils/storage.py) with support for S3, local disk, and temporary storage
- **Media utilities**: [`utils/media_utils.py`](utils/media_utils.py) provides file validation and processing
- **Controller usage**: [`controllers/media_controller.py`](controllers/media_controller.py) uses storage utilities for file operations
- **Service integration**: [`services/media_service.py`](services/media_service.py) leverages storage utilities for entity-media relationships

### 2. Reusable Media Gallery Component
- **Frontend component**: JavaScript gallery components in [`static/js/gallery*.js`](static/js/gallery.js)
- **Templates**: [`templates/components/media_gallery_modal.html`](templates/components/media_gallery_modal.html) provides reusable modal
- **API endpoints**: Job and property controllers have dedicated media endpoints for gallery operations
- **CSS styling**: [`static/css/gallery_styles.css`](static/css/gallery_styles.css) provides consistent styling

### 3. External Environment for E2E Tests
- **Test configuration**: [`pytest.e2e.ini`](pytest.e2e.ini) for external E2E test execution
- **Fixtures**: [`tests/e2e/conftest.py`](tests/e2e/conftest.py) provides test fixtures for Playwright
- **Test isolation**: E2E tests run outside Docker environment with dedicated configuration
- **Playwright integration**: Browser automation tests in [`tests/e2e/`](tests/e2e/) directory

### 4. Universal Timezone Handler
- **Timezone utilities**: [`utils/timezone.py`](utils/timezone.py) provides centralized timezone handling
- **Configuration**: `APP_TIMEZONE` environment variable configures application timezone
- **UTC-first approach**: All internal operations use UTC, conversion at presentation layer
- **Testing**: Timezone validation endpoints in [`routes/testing.py`](routes/testing.py)

## Current Status
- **✅ Storage utilities** implemented and integrated with media controller and services
- **✅ Media gallery component** available for reuse across job and property contexts
- **✅ E2E test environment** configured with external execution and dedicated fixtures
- **✅ Timezone handling** implemented with UTC-first architecture and environment configuration

## Next Steps
1. **Complete frontend integration** of reusable gallery component across all views
2. **Expand E2E test coverage** for all critical user workflows
3. **Validate timezone handling** in production deployment scenarios
4. **Document storage utility usage** patterns for future development
