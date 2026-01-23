#!/usr/bin/env python3
"""
Quick test to verify Apache Libcloud integration.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import pytest

def test_imports():
    try:
        from utils.storage import upload_flask_file, get_file_url, delete_file, validate_and_upload, file_exists
        print("✓ utils.storage imports succeeded")
    except Exception as e:
        pytest.fail(f"utils.storage imports failed: {e}")

    try:
        from routes.media import media_bp
        print("✓ routes.media imports succeeded")
    except Exception as e:
        pytest.fail(f"routes.media imports failed: {e}")

    try:
        from app_factory import create_app
        print("✓ app_factory import succeeded")
    except Exception as e:
        pytest.fail(f"app_factory import failed: {e}")

def test_config():
    """Check that config has storage settings."""
    from config import Config
    config = Config()
    required = ['STORAGE_PROVIDER', 'S3_BUCKET', 'AWS_REGION', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'UPLOAD_FOLDER']
    for key in required:
        val = getattr(config, key, None)
        assert val is not None, f"Config missing {key}"
        print(f"✓ Config {key} = {val}")

def test_app_factory():
    """Test creating app with minimal config."""
    import tempfile
    import shutil
    from flask import Flask

    # Create a temporary upload directory
    tmpdir = tempfile.mkdtemp()
    try:
        os.environ['STORAGE_PROVIDER'] = 'local'
        os.environ['UPLOAD_FOLDER'] = os.path.join(tmpdir, 'uploads')
        os.environ['SECRET_KEY'] = 'testsecret'
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

        from app_factory import create_app
        app = create_app(config_override={'TESTING': True})
        print("✓ App creation succeeded")
        # Check that storage driver and container are set
        assert 'STORAGE_DRIVER' in app.config and 'STORAGE_CONTAINER' in app.config, "Storage driver/container missing"
        print("✓ Storage driver and container configured")
    except Exception as e:
        pytest.fail(f"App creation failed: {e}")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == '__main__':
    print("Testing Apache Libcloud integration...")
    try:
        test_imports()
        test_config()
        test_app_factory()
        print("\nAll integration tests passed.")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)