# Testing Configuration for User Service

This directory contains unit tests for the `UserService` using `pytest`.

## Testing Library

*   **Pytest**: The primary testing framework used for writing and running tests.
*   **unittest.mock**: Used for mocking dependencies, such as the database session and external functions like `check_password_hash`, to isolate the unit under test.

## How to Run Tests

To run the tests, follow these steps:

1.  **Activate the Virtual Environment**:
    Ensure your Python virtual environment is activated. If you are in the project root directory, you can activate it using:
    ```bash
    source venv/bin/activate
    ```

2.  **Install Dependencies (if not already installed)**:
    If `pytest` or other dependencies are not installed in your virtual environment, install them:
    ```bash
    pip install pytest
    ```

3.  **Run All Tests**:
    To run all tests in the `tests/` directory:
    ```bash
    pytest tests/
    ```

4.  **Run Specific Test File**:
    To run tests from a specific file, for example, `test_user_service.py`:
    ```bash
    pytest tests/test_user_service.py
    ```

5.  **Run Tests with Verbose Output**:
    To see more detailed output during test execution:
    ```bash
    pytest -v tests/
    ```

This setup ensures that tests are run in an isolated environment and provides clear instructions for execution.

## Shared Fixtures

Common fixtures like `app_context` and `client` are defined in `tests/conftest.py` to be shared across multiple test files, promoting reusability and reducing code duplication.