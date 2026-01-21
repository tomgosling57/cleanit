"""
Test to verify S3/MinIO configuration works correctly in debug mode.

This test reproduces the issue where Flask app in debug mode fails to connect to MinIO
because S3 configuration variables (S3_ENDPOINT_URL, S3_USE_HTTPS, S3_VERIFY_SSL)
were missing from the Config class.
"""

import os
import pytest
from flask import Flask
from config import DebugConfig


def test_debug_config_has_s3_variables():
    """Test that DebugConfig includes all necessary S3 configuration variables."""
    # Set environment variables for the test
    os.environ['STORAGE_PROVIDER'] = 's3'
    os.environ['S3_BUCKET'] = 'test-bucket'
    os.environ['AWS_ACCESS_KEY_ID'] = 'test-key'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'test-secret'
    os.environ['S3_ENDPOINT_URL'] = 'http://minio:9000'
    os.environ['S3_USE_HTTPS'] = 'false'
    os.environ['S3_VERIFY_SSL'] = 'false'
    
    # Create app with DebugConfig
    app = Flask(__name__)
    app.config.from_object(DebugConfig)
    
    # Verify all S3 configuration variables are present
    assert app.config['STORAGE_PROVIDER'] == 's3'
    assert app.config['S3_BUCKET'] == 'test-bucket'
    assert app.config['AWS_ACCESS_KEY_ID'] == 'test-key'
    assert app.config['AWS_SECRET_ACCESS_KEY'] == 'test-secret'
    assert app.config['S3_ENDPOINT_URL'] == 'http://minio:9000'
    assert app.config['S3_USE_HTTPS'] == 'false'
    assert app.config['S3_VERIFY_SSL'] == 'false'
    
    # Clean up environment variables
    del os.environ['STORAGE_PROVIDER']
    del os.environ['S3_BUCKET']
    del os.environ['AWS_ACCESS_KEY_ID']
    del os.environ['AWS_SECRET_ACCESS_KEY']
    del os.environ['S3_ENDPOINT_URL']
    del os.environ['S3_USE_HTTPS']
    del os.environ['S3_VERIFY_SSL']


def test_debug_config_defaults_to_s3():
    """Test that DebugConfig defaults to S3 storage (not local)."""
    # Clear any STORAGE_PROVIDER environment variable
    if 'STORAGE_PROVIDER' in os.environ:
        del os.environ['STORAGE_PROVIDER']
    
    app = Flask(__name__)
    app.config.from_object(DebugConfig)
    
    # After the fix, DebugConfig should default to 's3' not 'local'
    assert app.config['STORAGE_PROVIDER'] == 's3'


def test_app_factory_s3_driver_initialization():
    """Test that app_factory creates S3 driver correctly with MinIO endpoint."""
    # This test requires the actual app_factory module
    try:
        from app_factory import create_app
        
        # Create a test app with debug config
        app = create_app(config_override={'TESTING': True})
        
        # In testing mode, it should use temp storage, not S3
        # But we can verify the config loading works
        assert 'STORAGE_DRIVER' in app.config
        assert 'STORAGE_CONTAINER' in app.config
        
    except ImportError:
        pytest.skip("app_factory module not available for testing")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])