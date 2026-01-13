# Playwright Pytest Workflow for CleanIt Application

## Overview
This document outlines the patterns and best practices for writing end-to-end tests using Playwright and pytest for the CleanIt application. The patterns are derived from existing test implementations and helper functions.

## Test Database Configuration
The testing environment uses a **local seeded test database** that is wiped and reseeded after each test. This ensures consistent, deterministic test data for reliable test execution.

### Key Characteristics:
1. **Deterministic Data**: Test data is consistently seeded from `database.py` using the `insert_dummy_data()` function
2. **Isolated Tests**: Database is reset between tests to prevent state leakage
3. **Specific Object References**: Many test cases are tied to specific objects with known IDs:
   - Users: Admin (ID: 1), Supervisor (ID: 2), User (ID: 3)
   - Teams: Initial Team (ID: 1), Alpha Team (ID: 2), Beta Team (ID: 3), etc.
   - Properties: 123 Main St (ID: 1), 456 Oak Ave (ID: 2)
   - Jobs: Pre-defined jobs with specific IDs and attributes

### Database Seeding Functions:
- `create_initial_users()`: Creates admin, supervisor, and user accounts
- `create_initial_teams()`: Creates teams with specific memberships
- `create_initial_properties_and_jobs()`: Creates properties and associated jobs
- `insert_dummy_data()`: Main function that orchestrates all seeding

### Writing Tests with Deterministic Data:
When writing tests, you can rely on specific data being available:

```python
# Example: Testing with specific job ID
job_id = "1"  # Known from seeded data
with page.expect_response(f"**/jobs/job/{job_id}/details**"):
    # Test logic

# Example: Testing with specific user credentials
login_admin(page, goto)  # Uses admin@example.com / admin_password
login_supervisor(page, goto)  # Uses supervisor@example.com / supervisor_password
login_user(page, goto)  # Uses user@example.com / user_password
```

**Why:** Deterministic data enables precise test coverage and eliminates flakiness caused by random or inconsistent test data.

## Core Principles

### 1. Authentication First
All tests must begin with authentication using the appropriate login helper function:

```python
from tests.helpers import login_admin, login_supervisor, login_user

def test_example(page, goto) -> None:
    # Always start with authentication
    login_admin(page, goto)  # or login_supervisor, login_user
    # ... rest of test
```

**Why:** Ensures consistent test state and follows the application's authentication flow.

### 2. CSS Selectors Over Text/Role Locators
When identifying elements in Playwright, **always prefer CSS selectors** from the actual templates over `get_by_text()` or `get_by_role()` methods:

```python
# ✅ Preferred: Use CSS selectors from templates
page.locator("#job-modal")
page.locator(".job-card")
page.locator('div[data-job-id="123"]')

# ❌ Avoid when possible: Text/role based locators
page.get_by_text("View Details")
page.get_by_role("button", name="Save")
```

**Why:** CSS selectors are more stable, faster, and directly tied to the template structure. They're less likely to break due to text changes.

### 3. Template-Driven Selector Discovery
Before writing tests, examine the relevant template files to identify the correct CSS selectors:

- Check `templates/` directory for the relevant component
- Look for `id`, `class`, and `data-*` attributes
- Use the same selectors that are used in the HTML templates

**Example:** For job-related tests, examine:
- `templates/job_card.html`
- `templates/job_modal.html`
- `templates/job_details_modal.html`

### 4. Network Response Waiting
When buttons are clicked or API functionality is triggered, **always use `expect_response` blocks**:

```python
# ✅ Correct: Wait for specific network response
with page.expect_response("**/jobs/job/123/details**"):
    page.wait_for_load_state('networkidle')
    button.click()

# ✅ Also include network idle state
with page.expect_response("**/api/endpoint**"):
    page.wait_for_load_state('networkidle')
    # Perform action
```

**Why:** Ensures the test waits for the server response and any subsequent DOM updates before proceeding.

### 5. Helper Function Design
When creating helper functions, separate navigation/action helpers from assertion helpers:

#### Navigation/Action Helpers
- Perform actions like clicking, filling forms, opening modals
- May include sanity check expects but should not end with expects of the target element
- Focus on getting to a state, not validating the state

```python
# ✅ Good navigation helper
def open_job_details_modal(page: Page, job_card: Locator, url_pattern: str) -> None:
    """Opens the job details modal."""
    with page.expect_response(url_pattern):
        page.wait_for_load_state('networkidle')
        job_card.get_by_role("button", name="View Details").click()
        
    # Sanity check - modal container exists
    expect(page.locator("#job-modal")).to_be_visible()

# ❌ Avoid - navigation helper that asserts target element
def open_job_details_modal(page: Page, job_card: Locator, url_pattern: str) -> None:
    with page.expect_response(url_pattern):
        page.wait_for_load_state('networkidle')
        job_card.get_by_role("button", name="View Details").click()
    # Don't assert modal content here - that's for assertion helpers
    expect(page.locator("#job-modal h2")).to_have_text("Job Details")  # ❌ Too specific
```

#### Assertion Helpers
- Validate state, content, or behavior
- Focus on what should be true after navigation/actions
- Can be reused across multiple tests

```python
# ✅ Good assertion helper
def assert_job_details_modal_content(
    page: Page,
    modal_id: str,
    title: str,
    start_time: str,
    # ... other parameters
) -> None:
    """Asserts the content of a job details modal."""
    modal = page.locator(modal_id)
    expect(modal.locator("h2")).to_have_text(title)
    expect(modal.get_by_text(f"Start: {start_time}")).to_be_visible()
    # ... other assertions
```

**Why:** Separation of concerns makes helpers more reusable and tests more maintainable.

### 7. Deterministic Test Data
Tests should leverage the seeded database data for consistent coverage:

```python
# ✅ Good: Use known IDs from seeded data
job_card = page.locator('div.job-card[data-job-id="1"]')  # Job ID 1 exists in seeded data
property_card = page.locator('.property-card[data-id="2"]')  # Property ID 2 exists

# ✅ Good: Test specific scenarios tied to seeded data
def test_admin_can_edit_job_1(page, goto):
    login_admin(page, goto)
    # Job 1 has specific attributes in seeded data
    job_card = page.locator('div.job-card[data-job-id="1"]')
    # ... test logic

# ❌ Avoid: Assuming random or non-existent data unless testing failure or negative cases
job_card = page.locator('div.job-card[data-job-id="999"]')  # ID 999 doesn't exist
```

**Key Data Points:**
- **Admin User**: ID 1, email: admin@example.com
- **Supervisor User**: ID 2, email: supervisor@example.com  
- **Regular User**: ID 3, email: user@example.com
- **Initial Team**: ID 1, contains admin and regular user
- **Property 1**: ID 1, address: "123 Main St, Anytown"
- **Property 2**: ID 2, address: "456 Oak Ave, Teamville"
- **Job 1**: ID 1, assigned to Initial Team, specific time and description

**Why:** Using deterministic data ensures tests are reliable and cover specific business logic tied to known data relationships.

### 8. Data Attributes for Dynamic Elements
Use `data-*` attributes for locating dynamic elements:

```python
# Get job ID from data attribute
job_id = job_card.get_attribute('data-job-id')

# Use data attribute in selectors
page.locator(f'div.job-card[data-job-id="{job_id}"]')
```

**Why:** Data attributes provide stable, semantic hooks for test automation that are less likely to change than classes or IDs.

## Test Structure Template

```python
from flask import url_for
from playwright.sync_api import expect
from tests.helpers import login_admin, relevant_helpers

def test_feature_name(page, goto) -> None:
    # 1. Authentication
    login_admin(page, goto)
    
    # 2. Navigate to relevant section (if needed)
    # 3. Locate elements using CSS selectors from templates
    element = page.locator("#css-selector-from-template")
    
    # 4. Perform actions with network response waiting
    with page.expect_response("**/api/endpoint**"):
        page.wait_for_load_state('networkidle')
        element.click()
    
    # 5. Assert expected state
    expect(element).to_be_visible()
    expect(element).to_have_text("Expected text")
    
    # 6. Use helper functions for complex operations
    # 7. Clean up if necessary
```

## Common Patterns

### Modal Operations
```python
# Open modal with response waiting
with page.expect_response("**/modal/endpoint**"):
    page.wait_for_load_state('networkidle')
    open_modal_button.click()

# Wait for modal to be visible
modal = page.locator("#modal-id")
expect(modal).to_be_visible()

# Close modal
modal.get_by_text("×").click()
expect(modal).to_be_hidden()
```

### Form Interactions
```python
# Fill form using CSS selectors
page.locator("#input-field").fill("value")
page.locator("#select-field").select_option("option-value")

# Submit with response waiting
with page.expect_response("**/form/submit**"):
    page.wait_for_load_state('networkidle')
    page.locator("#submit-button").click()
```

### Card/List Operations
```python
# Get first card
card = page.locator(".card-class").first

# Extract data attribute
item_id = card.get_attribute('data-id')

# Assert card content
expect(card.get_by_text("Expected content")).to_be_visible()
```

## Best Practices Checklist

- [ ] Start test with appropriate login helper
- [ ] Use CSS selectors from templates instead of text/role locators
- [ ] Check relevant template files for correct selectors
- [ ] Wrap interactions with `expect_response` blocks
- [ ] Include `page.wait_for_load_state('networkidle')` in response blocks
- [ ] Separate navigation helpers from assertion helpers
- [ ] Navigation helpers may include sanity checks but not target element assertions
- [ ] Use assertion helpers for state validation
- [ ] Leverage deterministic test data from seeded database
- [ ] Reference specific object IDs from seeded data in tests
- [ ] Leverage `data-*` attributes for dynamic elements
- [ ] Use `page.locator()` with CSS selectors
- [ ] Follow the test structure template
- [ ] Assert expected states after actions

## File Organization

- Place new test files in `tests/` directory
- Name test files with `test_` prefix (e.g., `test_feature_views.py`)
- Import helpers from `tests.helpers`
- Follow existing test patterns in `test_job_views.py` and `test_property_views.py`

## Troubleshooting

If tests fail:
1. Verify CSS selectors match the current template
2. Check network responses are correctly awaited
3. Ensure authentication is working
4. Confirm helper functions are up-to-date
5. Check for modal visibility states

## References

- Existing tests: `tests/test_job_views.py`, `tests/test_property_views.py`
- Helper functions: `tests/helpers.py`
- Templates: `templates/` directory
- Playwright documentation: https://playwright.dev/python/
