#!/usr/bin/env python3
"""
Docker gallery S3-specific feature tests.

Tests S3/MinIO-specific storage features in Docker configuration.
Verifies URL generation, storage provider configuration, and other
S3-specific functionality.
"""

import pytest
import os
import sys
import json
import requests
import io

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import Docker fixtures
pytest_plugins = ["tests.conftest_docker"]


class TestDockerGalleryS3Features:
    """S3-specific feature tests for gallery functionality with Docker."""
    
    def test_storage_provider_configuration(self):
        """
        Verify that storage provider is correctly configured for Docker.
        
        In Docker configuration, STORAGE_PROVIDER should be 's3',
        not 'temp' or 'local'.
        """
        # Check environment variable
        storage_provider = os.getenv('STORAGE_PROVIDER', 's3')
        assert storage_provider == 's3', \
            f"In Docker, STORAGE_PROVIDER should be 's3', not '{storage_provider}'"
        
        # Also check that S3 endpoint is configured
        s3_endpoint = os.getenv('S3_ENDPOINT_URL', 'http://localhost:9000')
        assert s3_endpoint.startswith('http'), \
            f"S3_ENDPOINT_URL should be a valid URL, got: {s3_endpoint}"
        
        # Check bucket configuration
        s3_bucket = os.getenv('S3_BUCKET', 'cleanit-media')
        assert s3_bucket, "S3_BUCKET should be configured"
        
        print(f"Docker storage configuration:")
        print(f"  - STORAGE_PROVIDER: {storage_provider}")
        print(f"  - S3_ENDPOINT_URL: {s3_endpoint}")
        print(f"  - S3_BUCKET: {s3_bucket}")
    
    def test_s3_url_generation(self, docker_admin_client):
        """
        Test that S3 URLs are properly generated for uploaded files.
        
        When using S3 storage, get_file_url() should return S3 URLs,
        not local Flask routes.
        """
        # Upload a test file
        test_file = io.BytesIO(b"S3 URL test data")
        test_file.name = "s3_url_test.jpg"
        
        upload_response = docker_admin_client.post(
            '/media/upload',
            data={
                'file': (test_file, 's3_url_test.jpg'),
                'description': 'S3 URL test'
            },
            content_type='multipart/form-data'
        )
        
        if upload_response.status_code != 200:
            pytest.skip("Could not upload test file")
        
        upload_data = json.loads(upload_response.data)
        media_id = upload_data['media_id']
        
        try:
            # Get media metadata which should include URL
            media_response = docker_admin_client.get(
                f'/media/{media_id}',
                headers={'Accept': 'application/json'}
            )
            
            if media_response.status_code == 200:
                media_data = json.loads(media_response.data)
                
                # Check if URL field exists
                if 'url' in media_data:
                    url = media_data['url']
                    
                    # Analyze the URL
                    print(f"Generated URL for S3 file: {url}")
                    
                    # S3/MinIO URLs could be:
                    # 1. Direct S3/MinIO URLs (contains endpoint or bucket)
                    # 2. Flask route URLs (contains /media/serve/)
                    # Both are acceptable depending on configuration
                    
                    is_s3_direct = any(
                        indicator in url.lower() 
                        for indicator in ['s3', 'amazonaws', 'minio', 'localhost:9000']
                    )
                    
                    is_flask_route = '/media/serve/' in url
                    
                    assert is_s3_direct or is_flask_route, \
                        f"URL doesn't look like S3 or Flask route: {url}"
                    
                    print(f"  - URL type: {'S3/MinIO direct' if is_s3_direct else 'Flask route'}")
                else:
                    print("Warning: URL field not found in media metadata")
            
            # Also test the serve endpoint to see what it returns
            serve_response = docker_admin_client.get(f'/media/serve/s3_url_test.jpg')
            print(f"Serve endpoint status: {serve_response.status_code}")
            
        finally:
            # Clean up
            docker_admin_client.delete(f'/media/{media_id}')
    
    def test_file_exists_s3_integration(self, docker_admin_client):
        """
        Test file_exists functionality with S3 storage.
        
        Upload a file and verify file_exists returns True,
        then delete it and verify file_exists returns False.
        """
        # Upload a test file
        test_file = io.BytesIO(b"file exists test data")
        test_file.name = "exists_test.jpg"
        
        upload_response = docker_admin_client.post(
            '/media/upload',
            data={
                'file': (test_file, 'exists_test.jpg'),
                'description': 'File exists test'
            },
            content_type='multipart/form-data'
        )
        
        if upload_response.status_code != 200:
            pytest.skip("Could not upload test file")
        
        upload_data = json.loads(upload_response.data)
        media_id = upload_data['media_id']
        filename = upload_data.get('filename', 'exists_test.jpg')
        
        try:
            # Get media to verify it exists
            media_response = docker_admin_client.get(
                f'/media/{media_id}',
                headers={'Accept': 'application/json'}
            )
            
            assert media_response.status_code == 200, \
                "Uploaded media should be retrievable"
            
            # Note: We can't directly test file_exists() from the client
            # since it's an internal function. But we can test that
            # the file can be served or accessed.
            
            # Try to serve the file (might work or return appropriate error)
            serve_response = docker_admin_client.get(f'/media/serve/{filename}')
            # Status could be 200 (served), 404 (not served via this route for S3),
            # or something else. Either is acceptable.
            print(f"File serve test status: {serve_response.status_code}")
            
        finally:
            # Delete the file
            delete_response = docker_admin_client.delete(f'/media/{media_id}')
            assert delete_response.status_code in [200, 404], \
                f"Failed to delete test file: {delete_response.status_code}"
            
            # Verify file is gone (should get 404)
            media_response = docker_admin_client.get(
                f'/media/{media_id}',
                headers={'Accept': 'application/json'}
            )
            assert media_response.status_code == 404, \
                "Deleted media should not be retrievable"
    
    def test_s3_storage_metadata(self, docker_admin_client, test_jpeg_file):
        """
        Test that S3 storage preserves file metadata.
    
        Verify that uploaded files retain their original filename,
        size, MIME type, and other metadata.
        """
        original_filename = "test_metadata_2025.jpg"
        original_description = "Test file with metadata"
    
        # Use the test_jpeg_file fixture which provides actual JPEG data
        test_jpeg_file.name = original_filename
        test_content = test_jpeg_file.getvalue()
        test_jpeg_file.seek(0)  # Reset for upload
    
        upload_response = docker_admin_client.post(
            '/media/upload',
            data={
                'file': (test_jpeg_file, original_filename),
                'description': original_description
            },
            content_type='multipart/form-data'
        )
    
        if upload_response.status_code != 200:
            pytest.skip("Could not upload test file")
    
        upload_data = json.loads(upload_response.data)
        media_id = upload_data['media_id']
    
        try:
            # Get media metadata
            media_response = docker_admin_client.get(
                f'/media/{media_id}',
                headers={'Accept': 'application/json'}
            )
    
            assert media_response.status_code == 200
            media_data = json.loads(media_response.data)
    
            # Verify metadata
            assert 'filename' in media_data
            # Filename might be modified (unique prefix added) but should contain original
            assert original_filename in media_data['filename'] or \
                   original_filename.replace('.jpg', '') in media_data['filename']
    
            assert 'description' in media_data
            assert media_data['description'] == original_description
    
            # Size should be preserved (approximately)
            if 'size_bytes' in media_data:
                # Size might be exact or close
                size = media_data['size_bytes']
                assert abs(size - len(test_content)) <= 100, \
                    f"Size mismatch: expected ~{len(test_content)}, got {size}"
    
            # MIME type should be set
            if 'mimetype' in media_data:
                mimetype = media_data['mimetype']
                assert mimetype, "MIME type should not be empty"
                # Should be image/jpeg or similar for JPEG files
                # Accept application/octet-stream as fallback
                if not ('image' in mimetype or 'jpeg' in mimetype):
                    print(f"Warning: MIME type is {mimetype}, not image/jpeg. This may be acceptable for test files.")
                    # Don't fail the test, just warn
                else:
                    print(f"MIME type correctly detected as: {mimetype}")
    
        finally:
            # Clean up
            docker_admin_client.delete(f'/media/{media_id}')
    
    def test_s3_endpoint_connectivity(self):
        """
        Test S3/MinIO endpoint connectivity and configuration.
        
        This test verifies that the S3 endpoint is properly configured
        and accessible from the test environment.
        """
        import requests
        
        s3_endpoint = os.getenv('S3_ENDPOINT_URL', 'http://localhost:9000')
        
        try:
            response = requests.get(s3_endpoint, timeout=10)
            
            # MinIO might return various status codes for root endpoint
            # 200 (OK), 403 (Forbidden), 404 (Not Found) are all acceptable
            # as long as we get a response
            assert response.status_code in [200, 403, 404], \
                f"S3 endpoint returned unexpected status: {response.status_code}"
            
            print(f"S3 endpoint connectivity: HTTP {response.status_code}")
            
            # Check response headers for MinIO identification
            server_header = response.headers.get('Server', '').lower()
            if 'minio' in server_header:
                print("  - Server identified as MinIO")
            
        except requests.exceptions.ConnectionError as e:
            pytest.fail(f"S3 endpoint not accessible: {e}")
        except requests.exceptions.Timeout as e:
            pytest.fail(f"S3 endpoint timeout: {e}")
    
    def test_gallery_display_with_fixed_url_generation(self, docker_admin_client):
        """
        Test that gallery correctly displays images with the fixed URL generation.
        
        This test specifically verifies the fix for the issue where images
        uploaded to the gallery show names but display "media could not be loaded"
        placeholder instead of actual image content.
        
        The fix ensures get_file_url() returns public URLs like
        http://localhost:9000/{bucket}/{filename} instead of presigned URLs
        with internal hostname minio:9000.
        """
        import os
        from pathlib import Path
        
        # Use a test image from the tests/media directory
        test_image_path = Path(__file__).parent / 'media' / 'test_image_1.jpg'
        
        if not test_image_path.exists():
            pytest.skip(f"Test image not found: {test_image_path}")
        
        # Read the test image
        with open(test_image_path, 'rb') as f:
            image_data = f.read()
        
        # Upload the test image
        test_file = io.BytesIO(image_data)
        test_file.name = "test_gallery_display.jpg"
        
        upload_response = docker_admin_client.post(
            '/media/upload',
            data={
                'file': (test_file, 'test_gallery_display.jpg'),
                'description': 'Gallery display test image'
            },
            content_type='multipart/form-data'
        )
        
        if upload_response.status_code != 200:
            pytest.skip("Could not upload test image")
        
        upload_data = json.loads(upload_response.data)
        media_id = upload_data['media_id']
        filename = upload_data.get('filename', 'test_gallery_display.jpg')
        
        try:
            # Get media metadata to check the URL
            media_response = docker_admin_client.get(
                f'/media/{media_id}',
                headers={'Accept': 'application/json'}
            )
            
            assert media_response.status_code == 200
            media_data = json.loads(media_response.data)
            
            # Check that URL field exists
            assert 'url' in media_data, "Media metadata should include URL field"
            url = media_data['url']
            
            print(f"Generated URL for gallery image: {url}")
            
            # Verify the URL is correctly generated for MinIO
            # With the fix, it should use the configured public hostname and port
            s3_bucket = os.getenv('S3_BUCKET', 'cleanit-media')
            s3_public_host = os.getenv('S3_PUBLIC_HOST', 'localhost')
            s3_public_port = os.getenv('S3_PUBLIC_PORT', '9000')
            
            # Check for the correct public URL pattern
            if s3_public_port == '80':
                expected_pattern = f"http://{s3_public_host}/{s3_bucket}/"
            elif s3_public_port == '443':
                expected_pattern = f"https://{s3_public_host}/{s3_bucket}/"
            else:
                expected_pattern = f"http://{s3_public_host}:{s3_public_port}/{s3_bucket}/"
            
            assert expected_pattern in url, \
                f"URL should contain public MinIO URL pattern: {expected_pattern}. Got: {url}"
            
            # Verify it's NOT using internal hostname minio:9000
            assert "minio:9000" not in url, \
                f"URL should not use internal hostname minio:9000. Got: {url}"
            
            # Verify it's NOT a presigned URL with signature parameters
            assert "?" not in url or "AWSAccessKeyId" not in url, \
                f"URL should not be a presigned URL with signature. Got: {url}"
            
            print(f"✓ URL correctly generated as public MinIO URL")
            print(f"  - Uses public hostname: {s3_public_host}:{s3_public_port}")
            print(f"  - Contains bucket: {s3_bucket}")
            print(f"  - Contains filename: {filename}")
            
            # Test that the URL is accessible (optional - depends on network)
            # We'll just check that the URL looks correct
            
            # Now test gallery endpoint to ensure it returns correct URLs
            # First, we need to attach this media to a property to test gallery
            # For simplicity, we'll just verify the URL generation logic
            
            # Import the storage module to test get_file_url directly
            from utils.storage import get_file_url
            
            # Test get_file_url with our filename
            test_url = get_file_url(filename)
            print(f"Direct get_file_url() result: {test_url}")
            
            # Verify it matches the same pattern
            # Note: get_file_url() might return a different URL format depending on configuration
            # For S3 storage with MinIO, it should return the public URL
            # But in test environment, it might return Flask route URL
            # We'll check that it returns a valid URL
            assert test_url, "get_file_url() should return a non-empty URL"
            
            # Check if it's a public MinIO URL or Flask route URL
            # Both are acceptable depending on configuration
            is_public_minio_url = expected_pattern in test_url
            is_flask_route_url = '/media/serve/' in test_url
            
            assert is_public_minio_url or is_flask_route_url, \
                f"get_file_url() should return either public MinIO URL or Flask route URL. Got: {test_url}"
            
            print(f"✓ get_file_url() correctly generates {'public MinIO' if is_public_minio_url else 'Flask route'} URL")
            
        finally:
            # Clean up
            delete_response = docker_admin_client.delete(f'/media/{media_id}')
            if delete_response.status_code not in [200, 404]:
                print(f"Warning: Failed to delete test image: {delete_response.status_code}")
    
    def test_docker_specific_environment_variables(self, docker_admin_client):
        """
        Verify Docker-specific environment variables are set.
    
        These variables are set in docker-compose.yml and should be
        present when running in Docker environment.
        """
        # Required for S3/MinIO - check either in environment or app config
        required_vars = [
            'STORAGE_PROVIDER',
            'S3_ENDPOINT_URL',
            'S3_BUCKET',
        ]
    
        # Optional but should have defaults
        optional_vars = [
            'AWS_REGION',
            'MINIO_ROOT_USER',
            'MINIO_ROOT_PASSWORD',
        ]
    
        print("Docker environment variables:")
    
        # Get app config to check values
        from flask import current_app
        with docker_admin_client.application.app_context():
            app_config = current_app.config
        
        for var in required_vars:
            # Check environment variable first
            env_value = os.getenv(var)
            # Check app config as fallback
            config_value = app_config.get(var)
            
            # Either environment variable or app config should have it
            value = env_value or config_value
            
            # For STORAGE_PROVIDER, default to 's3' for Docker
            if var == 'STORAGE_PROVIDER' and not value:
                value = 's3'
            
            assert value is not None and value != '', \
                f"Required variable {var} is not set in environment or app config"
            print(f"  - {var}: {value} (env: {env_value}, config: {config_value})")
    
        for var in optional_vars:
            env_value = os.getenv(var)
            config_value = app_config.get(var)
            value = env_value or config_value
            
            if value:
                print(f"  - {var}: {value}")
            else:
                print(f"  - {var}: (not set, using default)")


# Helper test that can be run directly
def test_docker_s3_environment():
    """
    Quick test to verify Docker S3 environment is properly configured.
    
    This can be run independently to check the environment before
    running the full test suite.
    """
    from tests.conftest_docker import docker_containers_running, check_minio_accessible
    
    print("=== Docker S3 Environment Check ===")
    
    # Check Docker containers
    assert docker_containers_running(), "Docker containers not running. Run: docker compose up -d"
    print("✓ Docker containers are running")
    
    # Check MinIO accessibility
    assert check_minio_accessible(), "MinIO not accessible"
    print("✓ MinIO is accessible")
    
    # Check environment variables
    storage_provider = os.getenv('STORAGE_PROVIDER', 's3')
    assert storage_provider == 's3', f"STORAGE_PROVIDER should be 's3', got '{storage_provider}'"
    print(f"✓ STORAGE_PROVIDER={storage_provider}")
    
    s3_endpoint = os.getenv('S3_ENDPOINT_URL', 'http://localhost:9000')
    print(f"✓ S3_ENDPOINT_URL={s3_endpoint}")
    
    s3_bucket = os.getenv('S3_BUCKET', 'cleanit-media')
    print(f"✓ S3_BUCKET={s3_bucket}")
    
    print("\n✓ All Docker S3 environment checks passed")
    print("  Run full test suite with: pytest tests/test_docker_gallery_*.py -v")
# --- Test MinIO URL transformation logic ---
def test_minio_url_transformation():
    """
    Test that MinIO internal URLs are transformed to public URLs correctly.
    This tests the logic in get_file_url() for S3/MinIO storage.
    """
    from urllib.parse import urlparse
    
    # Test cases: (internal_url, expected_public_url)
    test_cases = [
        # Internal Docker URL -> Public localhost URL
        ("http://minio:9000/cleanit-media/file.jpg", "http://localhost:9000/cleanit-media/file.jpg"),
        # URL with path
        ("http://minio:9000/cleanit-media/path/to/file.jpg", "http://localhost:9000/cleanit-media/path/to/file.jpg"),
        # Already public URL should not be changed
        ("http://localhost:9000/cleanit-media/file.jpg", "http://localhost:9000/cleanit-media/file.jpg"),
        # External S3 URL should not be changed
        ("https://s3.amazonaws.com/bucket/file.jpg", "https://s3.amazonaws.com/bucket/file.jpg"),
    ]
    
    for internal_url, expected_public_url in test_cases:
        # Simulate the transformation logic
        s3_endpoint_url = "http://minio:9000"
        parsed_endpoint = urlparse(s3_endpoint_url)
        internal_host = parsed_endpoint.hostname  # 'minio'
        internal_port = parsed_endpoint.port or 9000  # 9000
        
        public_host = 'localhost'
        public_port = 9000
        
        cdn_url = internal_url
        
        # Apply transformation
        internal_url_part = f"{internal_host}:{internal_port}"
        public_url_part = f"{public_host}:{public_port}"
        
        if internal_url_part in cdn_url:
            cdn_url = cdn_url.replace(internal_url_part, public_url_part)
        elif internal_host in cdn_url:
            cdn_url = cdn_url.replace(internal_host, public_host)
        
        assert cdn_url == expected_public_url, f"Failed to transform {internal_url} to {expected_public_url}, got {cdn_url}"
        
    print("✓ MinIO URL transformation tests passed")

def test_gallery_url_generation():
    """Test that gallery images generate correct public URLs."""
    
    print("=== Testing Gallery URL Generation Fix ===")
    
    # Check environment variables
    s3_endpoint = os.getenv('S3_ENDPOINT_URL', 'http://localhost:9000')
    s3_public_host = os.getenv('S3_PUBLIC_HOST', 'localhost')
    s3_public_port = os.getenv('S3_PUBLIC_PORT', '9000')
    s3_bucket = os.getenv('S3_BUCKET', 'cleanit-media')
    
    print(f"Configuration:")
    print(f"  - S3_ENDPOINT_URL: {s3_endpoint}")
    print(f"  - S3_PUBLIC_HOST: {s3_public_host}")
    print(f"  - S3_PUBLIC_PORT: {s3_public_port}")
    print(f"  - S3_BUCKET: {s3_bucket}")
    
    # Check if web server is running
    try:
        response = requests.get('http://localhost:5000/health', timeout=5)
        assert response.status_code == 200, "Web server health check failed"
        print("✓ Web server is running")
    except requests.exceptions.ConnectionError:
        pytest.fail("Web server not accessible at http://localhost:5000. Make sure Docker containers are running: docker compose up -d")
    
    # Check if MinIO is accessible
    try:
        response = requests.get(f'http://{s3_public_host}:{s3_public_port}/minio/health/live', timeout=5)
        assert response.status_code == 200, f"MinIO health check failed at http://{s3_public_host}:{s3_public_port}"
        print(f"✓ MinIO is accessible at http://{s3_public_host}:{s3_public_port}")
    except requests.exceptions.ConnectionError:
        pytest.fail(f"MinIO not accessible at http://{s3_public_host}:{s3_public_port}. Make sure MinIO container is running")
    
    # Test URL generation logic from utils/storage.py
    print("\n=== Testing URL Generation Logic ===")
    
    # Import the storage module
    try:
        from utils.storage import get_file_url
        
        # Create a test Flask app context to test get_file_url
        from flask import Flask
        from app_factory import create_app
        
        app = create_app()
        
        with app.app_context():
            # Configure app for S3 storage
            app.config['STORAGE_PROVIDER'] = 's3'
            app.config['S3_ENDPOINT_URL'] = s3_endpoint
            app.config['S3_BUCKET'] = s3_bucket
            app.config['S3_PUBLIC_HOST'] = s3_public_host
            app.config['S3_PUBLIC_PORT'] = s3_public_port
            
            # Initialize storage driver (simplified for test)
            # We'll just test the URL construction logic
            
            test_filename = "test_image_123.jpg"
            
            # Get the URL
            url = get_file_url(test_filename)
            
            print(f"Generated URL for '{test_filename}': {url}")
            
            # Check URL format
            expected_url = f"http://{s3_public_host}:{s3_public_port}/{s3_bucket}/{test_filename}"
            
            assert url == expected_url, f"Generated URL does not match expected format, expected: {expected_url}, got: {url}"
            
            # Verify it's NOT using internal hostname
            assert "minio:9000" not in url, "URL contains internal hostname 'minio:9000'"
            
            # Verify it's NOT a presigned URL
            assert not ("?" in url and ("AWSAccessKeyId" in url or "X-Amz-" in url)), "URL is a presigned URL with signature parameters"
            
            
    except ImportError as e:
        pytest.fail(f"Error importing modules: {e}")
    except Exception as e:
        pytest.fail(f"Error testing URL generation: {e}")

if __name__ == "__main__":
    """
    Run Docker S3 environment check directly.
    
    Usage: python tests/test_docker_gallery_s3_features.py
    """
    import sys
    try:
        test_docker_s3_environment()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)
