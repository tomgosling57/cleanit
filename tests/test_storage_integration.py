#!/usr/bin/env python3
"""
Quick test to verify Apache Libcloud integration.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    try:
        from utils.storage import upload_flask_file, get_file_url, delete_file, validate_and_upload, file_exists
        print("✓ utils.storage imports succeeded")
    except Exception as e:
        print(f"✗ utils.storage imports failed: {e}")
        return False

    try:
        from routes.storage import storage_bp
        print("✓ routes.storage imports succeeded")
    except Exception as e:
        print(f"✗ routes.storage imports failed: {e}")
        return False

    try:
        from app_factory import create_app
        print("✓ app_factory import succeeded")
    except Exception as e:
        print(f"✗ app_factory import failed: {e}")
        return False

    return True

def test_config():
    """Check that config has storage settings."""
    from config import Config
    config = Config()
    required = ['STORAGE_PROVIDER', 'S3_BUCKET', 'AWS_REGION', 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'UPLOAD_FOLDER']
    for key in required:
        val = getattr(config, key, None)
        if val is None:
            print(f"✗ Config missing {key}")
            return False
        else:
            print(f"✓ Config {key} = {val}")
    return True

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
        if 'STORAGE_DRIVER' in app.config and 'STORAGE_CONTAINER' in app.config:
            print("✓ Storage driver and container configured")
        else:
            print("✗ Storage driver/container missing")
            return False
    except Exception as e:
        print(f"✗ App creation failed: {e}")
        return False
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    return True

if __name__ == '__main__':
    print("Testing Apache Libcloud integration...")
    success = True
    if not test_imports():
        success = False
    if not test_config():
        success = False
    if not test_app_factory():
        success = False

    if success:
        print("\nAll integration tests passed.")
        sys.exit(0)
    else:
        print("\nIntegration tests failed.")
        sys.exit(1)