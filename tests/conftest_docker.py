#!/usr/bin/env python3
"""
Docker-specific fixtures for integration tests.

This module provides fixtures for testing with Docker containers running
(MinIO, PostgreSQL, Flask app). These fixtures are separate from the main
conftest.py to keep it manageable and to isolate Docker-specific dependencies.
"""

import pytest
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app_factory import create_app
from flask_login import LoginManager
from utils.populate_database import populate_database


def docker_containers_running():
    """Check if required Docker containers are running."""
    try:
        result = subprocess.run(
            ['docker', 'compose', 'ps', '--services', '--filter', 'status=running'],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.dirname(__file__))
        )
        running_services = result.stdout.strip().split('\n')
        required_services = {'postgres', 'minio', 'web'}
        return all(service in running_services for service in required_services)
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


# Skip all Docker tests if containers are not running
pytestmark = pytest.mark.skipif(
    not docker_containers_running(),
    reason="Docker containers (postgres, minio, web) must be running. Run 'docker compose up -d' first."
)


@pytest.fixture(scope="session")
def docker_app_config():
    """
    Configuration for Docker-based app with S3/MinIO storage.
    
    This configuration matches the Docker Compose setup with:
    - S3 storage provider (MinIO)
    - PostgreSQL database
    - Docker network endpoints
    """
    return {
        'TESTING': True,
        'STORAGE_PROVIDER': 's3',
        'S3_BUCKET': os.getenv('S3_BUCKET', 'cleanit-media'),
        'AWS_REGION': os.getenv('AWS_REGION', 'us-east-1'),
        'AWS_ACCESS_KEY_ID': os.getenv('MINIO_ROOT_USER', 'minioadmin'),
        'AWS_SECRET_ACCESS_KEY': os.getenv('MINIO_ROOT_PASSWORD', 'minioadmin'),
        'S3_ENDPOINT_URL': os.getenv('S3_ENDPOINT_URL', 'http://localhost:9000'),
        'S3_USE_HTTPS': 'false',
        'S3_VERIFY_SSL': 'false',
        'DATABASE_URL': os.getenv('DATABASE_URL', 'postgresql://cleanit_user@localhost:5432/cleanit'),
        'SECRET_KEY': 'test-secret-key-for-docker-tests',
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for API testing
    }


@pytest.fixture(scope="session")
def docker_app_debug_config(docker_app_config):
    """Configuration for debug mode with Docker S3 storage."""
    config = docker_app_config.copy()
    config['FLASK_ENV'] = 'debug'
    config['DEBUG'] = True
    return config


@pytest.fixture(scope="session")
def docker_app_production_config(docker_app_config):
    """Configuration for production mode with Docker S3 storage."""
    config = docker_app_config.copy()
    config['FLASK_ENV'] = 'production'
    config['DEBUG'] = False
    return config


@pytest.fixture(scope="session")
def docker_app(docker_app_config):
    """
    Create a Flask app configured for Docker S3/MinIO storage.
    
    This app uses the same configuration as the running Docker containers,
    allowing tests to interact with the actual S3/MinIO storage and
    PostgreSQL database.
    """
    login_manager = LoginManager()
    
    app = create_app(login_manager=login_manager, config_override=docker_app_config)
    
    # Populate database with test data
    with app.app_context():
        populate_database(app.config['SQLALCHEMY_DATABASE_URI'])
    
    yield app
    
    # Cleanup if needed
    # Note: Database cleanup happens via rollback fixture in main conftest.py


@pytest.fixture(scope="session")
def docker_app_no_csrf(docker_app_config):
    """
    Create a Flask app configured for Docker with CSRF disabled.
    
    Useful for API testing where CSRF tokens are not needed.
    """
    login_manager = LoginManager()
    
    # Ensure CSRF is disabled
    config = docker_app_config.copy()
    config['WTF_CSRF_ENABLED'] = False
    
    app = create_app(login_manager=login_manager, config_override=config)
    
    # Populate database with test data
    with app.app_context():
        populate_database(app.config['SQLALCHEMY_DATABASE_URI'])
    
    yield app


@pytest.fixture
def docker_admin_client(docker_app_no_csrf):
    """
    Provides a Flask test client with admin user logged in for Docker tests.
    
    Uses the seeded database to find an admin user and logs in via the
    login endpoint. CSRF is disabled for easier API testing.
    """
    from tests.conftest import login_admin_for_test
    
    client = docker_app_no_csrf.test_client()
    login_admin_for_test(client)
    yield client


@pytest.fixture
def docker_regular_client(docker_app_no_csrf):
    """
    Provides a Flask test client with regular user logged in for Docker tests.
    
    Uses the seeded database to find a regular user and logs in via the
    login endpoint. CSRF is disabled for easier API testing.
    """
    from tests.conftest import login_regular_for_test
    
    client = docker_app_no_csrf.test_client()
    login_regular_for_test(client)
    yield client


@pytest.fixture
def docker_client(docker_app_no_csrf):
    """
    Provides a Flask test client without authentication for Docker tests.
    
    Useful for testing authentication flows and public endpoints.
    """
    client = docker_app_no_csrf.test_client()
    yield client


@pytest.fixture
def minio_endpoint():
    """Get the MinIO S3 endpoint URL."""
    return os.getenv('S3_ENDPOINT_URL', 'http://localhost:9000')


@pytest.fixture
def minio_bucket():
    """Get the MinIO S3 bucket name."""
    return os.getenv('S3_BUCKET', 'cleanit-media')


@pytest.fixture
def minio_credentials():
    """Get MinIO credentials."""
    return {
        'access_key': os.getenv('MINIO_ROOT_USER', 'minioadmin'),
        'secret_key': os.getenv('MINIO_ROOT_PASSWORD', 'minioadmin'),
    }


@pytest.fixture
def test_image_file():
    """Create a test image file for upload tests."""
    import io
    
    # Create a simple PNG file in memory
    png_data = (
        b'\x89PNG\r\n\x1a\n'  # PNG signature
        b'\x00\x00\x00\rIHDR'  # IHDR chunk start
        b'\x00\x00\x00\x01'    # width: 1
        b'\x00\x00\x00\x01'    # height: 1
        b'\x08\x02\x00\x00\x00'  # bit depth, color type, etc.
        b'\x91x\xda\x63'       # CRC
        b'\x00\x00\x00\x00IEND\xaeB`\x82'  # IEND chunk
    )
    file_obj = io.BytesIO(png_data)
    file_obj.name = 'test_image.png'
    return file_obj


@pytest.fixture
def test_jpeg_file():
    """Create a test JPEG file for upload tests."""
    import io
    
    # Minimal JPEG data (just enough to pass validation)
    jpeg_data = (
        b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
        b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n'
        b'\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f'
        b'\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00'
        b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01\x01'
        b'\x00\x00?\x00\xff\xd9'
    )
    file_obj = io.BytesIO(jpeg_data)
    file_obj.name = 'test_image.jpg'
    return file_obj


def check_minio_accessible():
    """Check if MinIO is accessible."""
    import requests
    try:
        response = requests.get(
            os.getenv('S3_ENDPOINT_URL', 'http://localhost:9000'),
            timeout=5
        )
        return response.status_code in [200, 403, 404]
    except requests.exceptions.ConnectionError:
        return False


@pytest.fixture(scope="session", autouse=True)
def verify_docker_environment():
    """
    Verify Docker environment before running tests.
    
    This fixture runs automatically before any Docker test and verifies
    that the required services are accessible.
    """
    if not docker_containers_running():
        pytest.skip("Docker containers not running")
    
    if not check_minio_accessible():
        pytest.skip("MinIO not accessible")
    
    print("✓ Docker environment verified:")
    print(f"  - STORAGE_PROVIDER: {os.getenv('STORAGE_PROVIDER', 's3')}")
    print(f"  - S3_ENDPOINT_URL: {os.getenv('S3_ENDPOINT_URL', 'http://localhost:9000')}")
    print(f"  - S3_BUCKET: {os.getenv('S3_BUCKET', 'cleanit-media')}")


# Import shared fixtures from main conftest.py
# These will be available to tests that use this fixture module
from tests.conftest import (
    seeded_test_data,
    admin_client_no_csrf,
    regular_client_no_csrf,
    admin_client,
    regular_client,
    # Add other shared fixtures as needed
)