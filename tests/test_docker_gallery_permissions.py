#!/usr/bin/env python3
"""
Docker gallery permission tests.

Tests role-based permissions for gallery endpoints with S3/MinIO storage.
Verifies that regular users cannot upload or modify property galleries,
while admins have full access.
"""

import pytest
import os
import sys
import json
import io

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TestDockerGalleryPermissions:
    """Permission tests for gallery functionality with Docker S3/MinIO storage."""
    
    def test_regular_user_cannot_upload_media(self, docker_regular_client):
        """
        Regular users should NOT be able to upload media.
        
        Only admins should have permission to upload files to the system.
        """
        test_file = io.BytesIO(b"permission test data")
        test_file.name = "permission_test.jpg"
        
        upload_response = docker_regular_client.post(
            '/media/upload',
            data={
                'file': (test_file, 'permission_test.jpg'),
                'description': 'Permission test'
            },
            content_type='multipart/form-data'
        )
        
        assert upload_response.status_code == 403, \
            "Regular user should not be able to upload media"
        
        # Verify error message
        if upload_response.status_code == 403:
            data = json.loads(upload_response.data)
            assert 'error' in data
            assert 'Unauthorized' in data['error']
    
    def test_regular_user_cannot_access_property_gallery(self, docker_regular_client, seeded_test_data):
        """
        Regular users should NOT have access to property gallery.
        
        Property gallery requires supervisor or admin role.
        Regular users only have access to job galleries for their assigned jobs.
        """
        properties = seeded_test_data['properties']
        if not properties:
            pytest.skip("No properties in seeded data")
        
        property_obj = list(properties.values())[0]
        property_id = property_obj.id
        
        gallery_response = docker_regular_client.get(
            f'/address-book/property/{property_id}/media'
        )
        
        # Should be 403 Forbidden for regular users
        assert gallery_response.status_code == 403, \
            "Regular user should not have access to property gallery"
        
        # Verify error message
        if gallery_response.status_code == 403:
            data = json.loads(gallery_response.data)
            assert 'error' in data
            assert 'Unauthorized' in data['error']
    
    def test_admin_can_access_property_gallery(self, docker_admin_client, seeded_test_data):
        """
        Admin users SHOULD have access to property gallery.
        
        This is a positive test to contrast with the regular user test.
        """
        properties = seeded_test_data['properties']
        if not properties:
            pytest.skip("No properties in seeded data")
        
        property_obj = list(properties.values())[0]
        property_id = property_obj.id
        
        gallery_response = docker_admin_client.get(
            f'/address-book/property/{property_id}/media'
        )
        
        assert gallery_response.status_code == 200, \
            "Admin should have access to property gallery"
        
        # Verify structure of response
        gallery_data = json.loads(gallery_response.data)
        assert gallery_data['success'] is True
        assert gallery_data['property_id'] == property_id
        assert 'media' in gallery_data
    
    def test_regular_user_cannot_associate_media_with_property(self, docker_regular_client, docker_admin_client, seeded_test_data):
        """
        Regular users should NOT be able to associate media with properties.
        
        This test requires first uploading a file as admin, then trying to
        associate it as a regular user.
        """
        properties = seeded_test_data['properties']
        if not properties:
            pytest.skip("No properties in seeded data")
        
        property_obj = list(properties.values())[0]
        property_id = property_obj.id
        
        # First, admin uploads a file
        test_file = io.BytesIO(b"admin uploaded file for permission test")
        test_file.name = "admin_uploaded.jpg"
        
        upload_response = docker_admin_client.post(
            '/media/upload',
            data={
                'file': (test_file, 'admin_uploaded.jpg'),
                'description': 'Admin uploaded for permission test'
            },
            content_type='multipart/form-data'
        )
        
        if upload_response.status_code != 200:
            pytest.skip("Could not upload test file as admin")
        
        upload_data = json.loads(upload_response.data)
        media_id = upload_data['media_id']
        
        try:
            # Regular user tries to associate media with property
            associate_response = docker_regular_client.post(
                f'/address-book/property/{property_id}/media',
                json={'media_ids': [media_id]},
                content_type='application/json'
            )
            
            # Should be 403 Forbidden
            assert associate_response.status_code == 403, \
                "Regular user should not be able to associate media with property"
            
            # Verify error message
            if associate_response.status_code == 403:
                data = json.loads(associate_response.data)
                assert 'error' in data
                assert 'Unauthorized' in data['error']
        
        finally:
            # Clean up - admin deletes the file
            docker_admin_client.delete(f'/media/{media_id}')
    
    def test_regular_user_cannot_remove_media_from_gallery(self, docker_regular_client, docker_admin_client, seeded_test_data):
        """
        Regular users should NOT be able to remove media from property gallery.
        
        This test requires setting up a gallery with media first (as admin),
        then trying to remove it as a regular user.
        """
        properties = seeded_test_data['properties']
        if not properties:
            pytest.skip("No properties in seeded data")
        
        property_obj = list(properties.values())[0]
        property_id = property_obj.id
        
        # Admin uploads and associates a file
        test_file = io.BytesIO(b"file for removal permission test")
        test_file.name = "removal_test.jpg"
        
        upload_response = docker_admin_client.post(
            '/media/upload',
            data={
                'file': (test_file, 'removal_test.jpg'),
                'description': 'For removal permission test'
            },
            content_type='multipart/form-data'
        )
        
        if upload_response.status_code != 200:
            pytest.skip("Could not upload test file as admin")
        
        upload_data = json.loads(upload_response.data)
        media_id = upload_data['media_id']
        
        try:
            # Admin associates media with property
            associate_response = docker_admin_client.post(
                f'/address-book/property/{property_id}/media',
                json={'media_ids': [media_id]},
                content_type='application/json'
            )
            
            if associate_response.status_code != 200:
                pytest.skip("Could not associate media with property")
            
            # Regular user tries to remove media from gallery
            remove_response = docker_regular_client.delete(
                f'/address-book/property/{property_id}/media',
                json={'media_ids': [media_id]},
                content_type='application/json'
            )
            
            # Should be 403 Forbidden
            assert remove_response.status_code == 403, \
                "Regular user should not be able to remove media from gallery"
            
            # Verify error message
            if remove_response.status_code == 403:
                data = json.loads(remove_response.data)
                assert 'error' in data
                assert 'Unauthorized' in data['error']
        
        finally:
            # Clean up - admin removes association and deletes file
            docker_admin_client.delete(
                f'/address-book/property/{property_id}/media',
                json={'media_ids': [media_id]},
                content_type='application/json'
            )
            docker_admin_client.delete(f'/media/{media_id}')
    
    def test_unauthenticated_user_cannot_access_gallery(self, docker_client, seeded_test_data):
        """
        Unauthenticated users should be redirected to login.
        
        This tests the authentication layer, not just authorization.
        """
        properties = seeded_test_data['properties']
        if not properties:
            pytest.skip("No properties in seeded data")
        
        property_obj = list(properties.values())[0]
        property_id = property_obj.id
        
        gallery_response = docker_client.get(
            f'/address-book/property/{property_id}/media'
        )
        
        # Unauthenticated users should be redirected to login (302)
        # or get 401/403 depending on configuration
        assert gallery_response.status_code in [302, 401, 403], \
            f"Unauthenticated user should not have access (got {gallery_response.status_code})"
        
        # If it's a redirect, check it goes to login
        if gallery_response.status_code == 302:
            assert '/login' in gallery_response.location or 'login' in gallery_response.location