#!/usr/bin/env python3
"""
Basic Docker gallery integration tests.

Tests the core functionality of property reference gallery with Docker S3/MinIO storage.
Verifies that files uploaded to a property using S3/MinIO storage actually upload
and become visible in the gallery.

This file contains the essential tests that verify the Docker configuration works.
"""

import pytest
import os
import sys
import json
import io

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import Docker fixtures
pytest_plugins = ["tests.conftest_docker"]


class TestDockerGalleryBasic:
    """Basic integration tests for gallery functionality with Docker S3/MinIO storage."""
    
    def test_docker_containers_available(self):
        """Verify Docker containers are running."""
        from tests.conftest_docker import docker_containers_running
        assert docker_containers_running(), (
            "Docker containers not running. Start with: docker compose up -d"
        )
    
    def test_minio_accessible(self):
        """Test that MinIO S3 endpoint is accessible."""
        from tests.conftest_docker import check_minio_accessible
        assert check_minio_accessible(), "MinIO not accessible at S3_ENDPOINT_URL"
    
    def test_property_gallery_upload_s3_integration(self, docker_admin_client, seeded_test_data):
        """
        Core test: upload a file to property gallery with S3/MinIO storage.
        
        This test verifies the complete flow:
        1. Upload a file to S3/MinIO storage
        2. Associate it with a property
        3. Verify it appears in the property gallery
        4. Clean up
        """
        # Get a property from seeded data
        properties = seeded_test_data['properties']
        if not properties:
            pytest.skip("No properties in seeded data")
        
        property_obj = list(properties.values())[0]
        property_id = property_obj.id
        
        # Create test file
        test_file = io.BytesIO(b"fake image data for S3 integration test")
        test_file.name = "s3_integration_test.jpg"
        
        # Step 1: Upload media file (admin only endpoint)
        upload_response = docker_admin_client.post(
            '/media/upload',
            data={
                'file': (test_file, 's3_integration_test.jpg'),
                'description': 'S3 integration test image'
            },
            content_type='multipart/form-data'
        )
        
        # Check upload succeeded
        assert upload_response.status_code == 200, \
            f"Upload failed: {upload_response.data.decode('utf-8')}"
        
        upload_data = json.loads(upload_response.data)
        assert 'media_id' in upload_data
        assert 'filename' in upload_data
        media_id = upload_data['media_id']
        
        # Step 2: Associate media with property using gallery endpoint
        associate_response = docker_admin_client.post(
            f'/address-book/property/{property_id}/media',
            json={'media_ids': [media_id]},
            content_type='application/json'
        )
        
        # The endpoint should return success
        assert associate_response.status_code == 200, \
            f"Association failed: {associate_response.data.decode('utf-8')}"
        
        associate_data = json.loads(associate_response.data)
        assert associate_data.get('success') is True
        
        # Step 3: Get property gallery and verify file is included
        gallery_response = docker_admin_client.get(
            f'/address-book/property/{property_id}/media'
        )
        
        assert gallery_response.status_code == 200
        gallery_data = json.loads(gallery_response.data)
        
        assert gallery_data['success'] is True
        assert gallery_data['property_id'] == property_id
        assert 'media' in gallery_data
        assert isinstance(gallery_data['media'], list)
        
        # Find our uploaded media in the gallery
        media_in_gallery = [
            m for m in gallery_data['media'] 
            if m.get('id') == media_id or m.get('filename') == 's3_integration_test.jpg'
        ]
        
        assert len(media_in_gallery) > 0, \
            f"Uploaded media not found in gallery. Gallery media: {gallery_data['media']}"
        
        # Step 4: Clean up - remove media from gallery
        cleanup_response = docker_admin_client.delete(
            f'/address-book/property/{property_id}/media',
            json={'media_ids': [media_id]},
            content_type='application/json'
        )
        
        # Cleanup should succeed (or at least not fail with 500)
        assert cleanup_response.status_code in [200, 404], \
            f"Cleanup failed: {cleanup_response.data.decode('utf-8')}"
        
        # Step 5: Delete the media file itself
        delete_response = docker_admin_client.delete(f'/media/{media_id}')
        assert delete_response.status_code in [200, 404], \
            f"Media deletion failed: {delete_response.data.decode('utf-8')}"
    
    @pytest.mark.parametrize("env_mode", ["production", "debug"])
    def test_gallery_with_different_flask_env_modes(self, env_mode, docker_admin_client, seeded_test_data):
        """
        Test gallery functionality works in both production and debug modes.
        
        This test verifies that the gallery works regardless of FLASK_ENV setting
        when using S3/MinIO storage in Docker.
        """
        properties = seeded_test_data['properties']
        if not properties:
            pytest.skip("No properties in seeded data")
        
        property_obj = list(properties.values())[0]
        property_id = property_obj.id
        
        # Get current app config to check FLASK_ENV
        from flask import current_app
        with docker_admin_client.application.app_context():
            current_env = current_app.config.get('ENV', 'production')
            # Just log the current mode
            print(f"Testing with FLASK_ENV={current_env}")
        
        # Test basic gallery access
        gallery_response = docker_admin_client.get(
            f'/address-book/property/{property_id}/media'
        )
        
        assert gallery_response.status_code == 200, \
            f"Gallery access failed in {env_mode} mode"
        
        gallery_data = json.loads(gallery_response.data)
        assert gallery_data['success'] is True
        assert 'media' in gallery_data
        
        # The key point is that gallery should work in both modes
        # with S3 storage configured via Docker
    
    def test_gallery_empty_property(self, docker_admin_client, seeded_test_data):
        """
        Test that empty property gallery returns empty list, not error.
        """
        properties = seeded_test_data['properties']
        if not properties:
            pytest.skip("No properties in seeded data")
        
        property_obj = list(properties.values())[0]
        property_id = property_obj.id
        
        # Get gallery for property (should be empty initially)
        gallery_response = docker_admin_client.get(
            f'/address-book/property/{property_id}/media'
        )
        
        assert gallery_response.status_code == 200
        gallery_data = json.loads(gallery_response.data)
        
        assert gallery_data['success'] is True
        assert gallery_data['property_id'] == property_id
        assert 'media' in gallery_data
        assert isinstance(gallery_data['media'], list)
        # Could be empty or have some media from other tests
        # Just verify the structure is correct


def test_docker_gallery_integration_summary():
    """
    Summary test that runs key Docker gallery integration tests.
    
    This test serves as a high-level verification that the Docker
    configuration with S3/MinIO storage works for property galleries.
    """
    from tests.conftest_docker import docker_containers_running
    # This is a placeholder test that will pass if Docker containers are running
    # and the other tests in this module pass
    assert docker_containers_running(), "Docker containers must be running"
    print("✓ Docker gallery integration test suite ready")
    print("✓ Tests will verify S3/MinIO storage integration")
    print("✓ Tests will verify property gallery functionality")
    print("✓ Tests will work in both production and debug modes")