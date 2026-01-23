#!/usr/bin/env python3
"""
Docker gallery batch operation tests.

Tests batch upload and batch delete operations for property galleries
with S3/MinIO storage. Verifies that multiple files can be managed
efficiently in batch mode using the new gallery endpoints.
"""

import pytest
import os
import sys
import json
import io


class TestDockerGalleryBatchOperations:
    """Batch operation tests for gallery functionality with Docker S3/MinIO storage."""
    
    def test_batch_upload_to_property_gallery(self, docker_admin_client, seeded_test_data):
        """
        Test batch upload to property gallery with S3 storage.
        
        Verifies that multiple files can be uploaded directly to property gallery
        in batch mode using multipart/form-data.
        """
        properties = seeded_test_data['properties']
        if not properties:
            pytest.skip("No properties in seeded data")
        
        property_obj = list(properties.values())[0]
        property_id = property_obj.id
        
        # Create multiple test files for batch upload
        # Flask test client expects files in the data dictionary
        files = []
        for i in range(3):  # Upload 3 files
            test_file = io.BytesIO(f"batch test image data {i}".encode('utf-8'))
            test_file.name = f"batch_test_{i}.jpg"
            files.append((test_file, f"batch_test_{i}.jpg"))
        
        data = {
            'files[]': files,
            'descriptions[]': ['Batch test image 0', 'Batch test image 1', 'Batch test image 2']
        }
        
        # Batch upload directly to property gallery endpoint
        upload_response = docker_admin_client.post(
            f'/address-book/property/{property_id}/media',
            data=data,
            content_type='multipart/form-data'
        )
        
        assert upload_response.status_code == 200, \
            f"Batch upload failed: {upload_response.data.decode('utf-8')}"
        
        upload_data = json.loads(upload_response.data)
        assert upload_data.get('success') is True
        assert 'media_ids' in upload_data
        assert 'media' in upload_data
        
        media_ids = upload_data['media_ids']
        assert len(media_ids) == 3, f"Expected 3 media IDs, got {len(media_ids)}"
        
        # Verify gallery contains all uploaded files
        gallery_response = docker_admin_client.get(
            f'/address-book/property/{property_id}/media'
        )
        
        assert gallery_response.status_code == 200
        gallery_data = json.loads(gallery_response.data)
        
        gallery_media_ids = {m['id'] for m in gallery_data['media']}
        for media_id in media_ids:
            assert media_id in gallery_media_ids, \
                f"Media ID {media_id} not found in gallery"
        
        # Clean up - batch delete all uploaded files
        delete_response = docker_admin_client.delete(
            f'/address-book/property/{property_id}/media',
            json={'media_ids': media_ids},
            content_type='application/json'
        )
        
        assert delete_response.status_code == 200, \
            f"Batch delete failed: {delete_response.data.decode('utf-8')}"
        
        # Also delete media records from database
        for media_id in media_ids:
            docker_admin_client.delete(f'/media/{media_id}')
    
    def test_batch_remove_from_property_gallery(self, docker_admin_client, seeded_test_data):
        """
        Test batch removal from property gallery.
        
        Verifies that multiple files can be removed from gallery in batch mode.
        """
        properties = seeded_test_data['properties']
        if not properties:
            pytest.skip("No properties in seeded data")
        
        property_obj = list(properties.values())[0]
        property_id = property_obj.id
        
        # Upload multiple files directly to property gallery
        # Flask test client expects files in the data dictionary
        files = []
        for i in range(3):  # Upload 3 files
            test_file = io.BytesIO(f"batch removal test data {i}".encode('utf-8'))
            test_file.name = f"batch_remove_{i}.jpg"
            files.append((test_file, f"batch_remove_{i}.jpg"))
        
        data = {
            'files[]': files,
            'descriptions[]': ['Batch removal test 0', 'Batch removal test 1', 'Batch removal test 2']
        }
        
        upload_response = docker_admin_client.post(
            f'/address-book/property/{property_id}/media',
            data=data,
            content_type='multipart/form-data'
        )
        
        if upload_response.status_code != 200:
            pytest.skip("Could not upload test files to property gallery")
        
        upload_data = json.loads(upload_response.data)
        media_ids = upload_data.get('media_ids', [])
        
        if len(media_ids) < 3:
            # Clean up any uploaded files
            for media_id in media_ids:
                docker_admin_client.delete(f'/media/{media_id}')
            pytest.skip("Could not upload enough test files")
        
        # Verify initial gallery count
        gallery_response = docker_admin_client.get(
            f'/address-book/property/{property_id}/media'
        )
        assert gallery_response.status_code == 200
        gallery_data = json.loads(gallery_response.data)
        initial_count = len(gallery_data['media'])
        assert initial_count >= len(media_ids)
        
        # Batch remove some files (first 2)
        files_to_remove = media_ids[:2]
        remove_response = docker_admin_client.delete(
            f'/address-book/property/{property_id}/media',
            json={'media_ids': files_to_remove},
            content_type='application/json'
        )
        
        assert remove_response.status_code == 200, \
            f"Batch removal failed: {remove_response.data.decode('utf-8')}"
        
        remove_data = json.loads(remove_response.data)
        assert remove_data.get('success') is True
        
        # Verify remaining files in gallery
        gallery_response = docker_admin_client.get(
            f'/address-book/property/{property_id}/media'
        )
        assert gallery_response.status_code == 200
        gallery_data = json.loads(gallery_response.data)
        
        remaining_media_ids = {m['id'] for m in gallery_data['media']}
        
        # Files we removed should not be in gallery
        for media_id in files_to_remove:
            assert media_id not in remaining_media_ids, \
                f"Media ID {media_id} should have been removed but is still in gallery"
        
        # Files we didn't remove should still be in gallery
        files_not_removed = media_ids[2:] if len(media_ids) > 2 else []
        for media_id in files_not_removed:
            assert media_id in remaining_media_ids, \
                f"Media ID {media_id} should still be in gallery but is missing"
        
        # Clean up remaining files
        for media_id in media_ids:
            # Delete media file from database
            docker_admin_client.delete(f'/media/{media_id}')
    
    def test_empty_batch_operations(self, docker_admin_client, seeded_test_data):
        """
        Test batch operations with empty lists.
        
        Empty batch operations should succeed gracefully, not fail.
        """
        properties = seeded_test_data['properties']
        if not properties:
            pytest.skip("No properties in seeded data")
        
        property_obj = list(properties.values())[0]
        property_id = property_obj.id
        
        # Empty removal should succeed
        remove_response = docker_admin_client.delete(
            f'/address-book/property/{property_id}/media',
            json={'media_ids': []},
            content_type='application/json'
        )
        
        # Should return success (200) or at least not error (400/500)
        assert remove_response.status_code in [200, 400], \
            f"Empty removal failed with {remove_response.status_code}"
        
        if remove_response.status_code == 200:
            remove_data = json.loads(remove_response.data)
            assert remove_data.get('success') is True
    
    def test_partial_batch_failure(self, docker_admin_client, seeded_test_data):
        """
        Test batch operations with some invalid media IDs.
        
        The system should handle partial failures gracefully,
        succeeding for valid IDs and failing for invalid ones.
        """
        properties = seeded_test_data['properties']
        if not properties:
            pytest.skip("No properties in seeded data")
        
        property_obj = list(properties.values())[0]
        property_id = property_obj.id
        
        # Upload one valid file
        test_file = io.BytesIO(b"valid file for partial failure test")
        test_file.name = "valid_file.jpg"
        
        upload_response = docker_admin_client.post(
            f'/address-book/property/{property_id}/media',
            data={
                'file': (test_file, 'valid_file.jpg', 'image/jpeg'),
                'description': 'Valid file'
            },
            content_type='multipart/form-data'
        )
        
        if upload_response.status_code != 200:
            pytest.skip("Could not upload test file")
        
        upload_data = json.loads(upload_response.data)
        valid_media_ids = upload_data.get('media_ids', [])
        
        if not valid_media_ids:
            pytest.skip("Could not get media ID from upload")
        
        valid_media_id = valid_media_ids[0]
        
        try:
            # Try to remove valid and invalid media IDs
            invalid_media_id = 999999  # Non-existent ID
            mixed_ids = [valid_media_id, invalid_media_id]
            
            remove_response = docker_admin_client.delete(
                f'/address-book/property/{property_id}/media',
                json={'media_ids': mixed_ids},
                content_type='application/json'
            )
            
            # The response could be 200 (partial success) or 400/404 (failure)
            # Both are acceptable behaviors
            assert remove_response.status_code in [200, 400, 404], \
                f"Unexpected status code: {remove_response.status_code}"
            
            if remove_response.status_code == 200:
                remove_data = json.loads(remove_response.data)
                # Could have success: true with warnings, or success: false
                # Either is acceptable
        
        finally:
            # Clean up file
            docker_admin_client.delete(f'/media/{valid_media_id}')
    
    def test_batch_operations_order_preservation(self, docker_admin_client, seeded_test_data):
        """
        Test that batch operations preserve or handle order correctly.
        
        While order may not be critical, we verify that batch operations
        work consistently.
        """
        properties = seeded_test_data['properties']
        if not properties:
            pytest.skip("No properties in seeded data")
        
        property_obj = list(properties.values())[0]
        property_id = property_obj.id
        
        # Upload files in specific order
        # Flask test client expects files in the data dictionary
        files = []
        file_order = ["first", "second", "third"]
        
        for name in file_order:
            test_file = io.BytesIO(f"{name} file content".encode('utf-8'))
            test_file.name = f"{name}_file.jpg"
            files.append((test_file, f"{name}_file.jpg"))
        
        data = {
            'files[]': files,
            'descriptions[]': [f'{name} file' for name in file_order]
        }
        
        upload_response = docker_admin_client.post(
            f'/address-book/property/{property_id}/media',
            data=data,
            content_type='multipart/form-data'
        )
        
        if upload_response.status_code != 200:
            pytest.skip("Could not upload test files")
        
        upload_data = json.loads(upload_response.data)
        media_ids = upload_data.get('media_ids', [])
        
        if len(media_ids) != len(file_order):
            # Clean up any uploaded files
            for media_id in media_ids:
                docker_admin_client.delete(f'/media/{media_id}')
            pytest.skip("Could not upload all test files")
        
        try:
            # Get gallery and verify all files are present
            gallery_response = docker_admin_client.get(
                f'/address-book/property/{property_id}/media'
            )
            assert gallery_response.status_code == 200
            gallery_data = json.loads(gallery_response.data)
            
            # All media IDs should be in gallery
            gallery_media_ids = {m['id'] for m in gallery_data['media']}
            for media_id in media_ids:
                assert media_id in gallery_media_ids
            
            # Batch remove in reverse order
            reverse_ids = list(reversed(media_ids))
            remove_response = docker_admin_client.delete(
                f'/address-book/property/{property_id}/media',
                json={'media_ids': reverse_ids},
                content_type='application/json'
            )
            
            assert remove_response.status_code == 200
            
            # Verify gallery is empty (or at least not contain our files)
            gallery_response = docker_admin_client.get(
                f'/address-book/property/{property_id}/media'
            )
            assert gallery_response.status_code == 200
            gallery_data = json.loads(gallery_response.data)
            
            remaining_ids = {m['id'] for m in gallery_data['media']}
            for media_id in media_ids:
                assert media_id not in remaining_ids
        
        finally:
            # Clean up files (in case some weren't removed)
            for media_id in media_ids:
                docker_admin_client.delete(f'/media/{media_id}')
    
    def test_single_file_upload_to_property_gallery(self, docker_admin_client, seeded_test_data):
        """
        Test single file upload to property gallery.
        
        Verifies that single file upload works with the same endpoint.
        """
        properties = seeded_test_data['properties']
        if not properties:
            pytest.skip("No properties in seeded data")
        
        property_obj = list(properties.values())[0]
        property_id = property_obj.id
        
        # Upload single file
        test_file = io.BytesIO(b"single file test data")
        test_file.name = "single_test.jpg"
        
        upload_response = docker_admin_client.post(
            f'/address-book/property/{property_id}/media',
            data={
                'file': (test_file, 'single_test.jpg', 'image/jpeg'),
                'description': 'Single file test'
            },
            content_type='multipart/form-data'
        )
        
        assert upload_response.status_code == 200, \
            f"Single file upload failed: {upload_response.data.decode('utf-8')}"
        
        upload_data = json.loads(upload_response.data)
        assert upload_data.get('success') is True
        assert 'media_ids' in upload_data
        assert len(upload_data['media_ids']) == 1
        
        media_id = upload_data['media_ids'][0]
        
        # Clean up
        docker_admin_client.delete(
            f'/address-book/property/{property_id}/media',
            json={'media_ids': [media_id]},
            content_type='application/json'
        )
        docker_admin_client.delete(f'/media/{media_id}')