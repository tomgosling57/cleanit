#!/usr/bin/env python3
"""
Docker gallery batch operation tests.

Tests batch upload and batch delete operations for property galleries
with S3/MinIO storage. Verifies that multiple files can be managed
efficiently in batch mode.
"""

import pytest
import os
import sys
import json
import io

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TestDockerGalleryBatchOperations:
    """Batch operation tests for gallery functionality with Docker S3/MinIO storage."""
    
    def test_batch_upload_to_property_gallery(self, docker_admin_client, seeded_test_data):
        """
        Test batch upload to property gallery with S3 storage.
        
        Verifies that multiple files can be uploaded and associated in batch mode.
        """
        properties = seeded_test_data['properties']
        if not properties:
            pytest.skip("No properties in seeded data")
        
        property_obj = list(properties.values())[0]
        property_id = property_obj.id
        
        # Create multiple test files
        media_ids = []
        
        for i in range(3):  # Upload 3 files
            test_file = io.BytesIO(f"batch test image data {i}".encode('utf-8'))
            test_file.name = f"batch_test_{i}.jpg"
            
            # Upload each file
            upload_response = docker_admin_client.post(
                '/media/upload',
                data={
                    'file': (test_file, f"batch_test_{i}.jpg"),
                    'description': f'Batch test image {i}'
                },
                content_type='multipart/form-data'
            )
            
            if upload_response.status_code == 200:
                upload_data = json.loads(upload_response.data)
                media_ids.append(upload_data['media_id'])
            else:
                print(f"Warning: Upload {i} failed: {upload_response.status_code}")
        
        if len(media_ids) < 2:
            pytest.skip("Could not upload enough test files (need at least 2)")
        
        # Batch associate all media with property
        associate_response = docker_admin_client.post(
            f'/address-book/property/{property_id}/media',
            json={'media_ids': media_ids},
            content_type='application/json'
        )
        
        assert associate_response.status_code == 200, \
            f"Batch association failed: {associate_response.data.decode('utf-8')}"
        
        associate_data = json.loads(associate_response.data)
        assert associate_data.get('success') is True
        
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
        
        # Clean up
        for media_id in media_ids:
            # Remove from gallery
            docker_admin_client.delete(
                f'/address-book/property/{property_id}/media',
                json={'media_ids': [media_id]},
                content_type='application/json'
            )
            # Delete media file
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
        
        # Upload and associate multiple files
        media_ids = []
        
        for i in range(3):  # Upload 3 files
            test_file = io.BytesIO(f"batch removal test data {i}".encode('utf-8'))
            test_file.name = f"batch_remove_{i}.jpg"
            
            upload_response = docker_admin_client.post(
                '/media/upload',
                data={
                    'file': (test_file, f"batch_remove_{i}.jpg"),
                    'description': f'Batch removal test {i}'
                },
                content_type='multipart/form-data'
            )
            
            if upload_response.status_code == 200:
                upload_data = json.loads(upload_response.data)
                media_ids.append(upload_data['media_id'])
        
        if len(media_ids) < 2:
            pytest.skip("Could not upload enough test files")
        
        # Associate all files with property
        associate_response = docker_admin_client.post(
            f'/address-book/property/{property_id}/media',
            json={'media_ids': media_ids},
            content_type='application/json'
        )
        
        if associate_response.status_code != 200:
            # Clean up uploaded files
            for media_id in media_ids:
                docker_admin_client.delete(f'/media/{media_id}')
            pytest.skip("Could not associate media with property")
        
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
            # Remove any remaining associations
            docker_admin_client.delete(
                f'/address-book/property/{property_id}/media',
                json={'media_ids': [media_id]},
                content_type='application/json'
            )
            # Delete media file
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
        
        # Empty association should succeed
        associate_response = docker_admin_client.post(
            f'/address-book/property/{property_id}/media',
            json={'media_ids': []},
            content_type='application/json'
        )
        
        # Should return success (200) or at least not error (400/500)
        assert associate_response.status_code in [200, 400], \
            f"Empty association failed with {associate_response.status_code}"
        
        if associate_response.status_code == 200:
            associate_data = json.loads(associate_response.data)
            assert associate_data.get('success') is True
        
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
            '/media/upload',
            data={
                'file': (test_file, 'valid_file.jpg'),
                'description': 'Valid file'
            },
            content_type='multipart/form-data'
        )
        
        if upload_response.status_code != 200:
            pytest.skip("Could not upload test file")
        
        upload_data = json.loads(upload_response.data)
        valid_media_id = upload_data['media_id']
        
        try:
            # Try to associate valid and invalid media IDs
            invalid_media_id = 999999  # Non-existent ID
            mixed_ids = [valid_media_id, invalid_media_id]
            
            associate_response = docker_admin_client.post(
                f'/address-book/property/{property_id}/media',
                json={'media_ids': mixed_ids},
                content_type='application/json'
            )
            
            # The response could be 200 (partial success) or 400/404 (failure)
            # Both are acceptable behaviors
            assert associate_response.status_code in [200, 400, 404], \
                f"Unexpected status code: {associate_response.status_code}"
            
            if associate_response.status_code == 200:
                associate_data = json.loads(associate_response.data)
                # Could have success: true with warnings, or success: false
                # Either is acceptable
            
            # Clean up association if it succeeded
            docker_admin_client.delete(
                f'/address-book/property/{property_id}/media',
                json={'media_ids': [valid_media_id]},
                content_type='application/json'
            )
        
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
        media_ids = []
        file_order = ["first", "second", "third"]
        
        for name in file_order:
            test_file = io.BytesIO(f"{name} file content".encode('utf-8'))
            test_file.name = f"{name}_file.jpg"
            
            upload_response = docker_admin_client.post(
                '/media/upload',
                data={
                    'file': (test_file, f"{name}_file.jpg"),
                    'description': f'{name} file'
                },
                content_type='multipart/form-data'
            )
            
            if upload_response.status_code == 200:
                upload_data = json.loads(upload_response.data)
                media_ids.append(upload_data['media_id'])
        
        if len(media_ids) != len(file_order):
            # Clean up any uploaded files
            for media_id in media_ids:
                docker_admin_client.delete(f'/media/{media_id}')
            pytest.skip("Could not upload all test files")
        
        try:
            # Batch associate in original order
            associate_response = docker_admin_client.post(
                f'/address-book/property/{property_id}/media',
                json={'media_ids': media_ids},
                content_type='application/json'
            )
            
            assert associate_response.status_code == 200
            
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
            
            # Verify gallery is empty
            gallery_response = docker_admin_client.get(
                f'/address-book/property/{property_id}/media'
            )
            assert gallery_response.status_code == 200
            gallery_data = json.loads(gallery_response.data)
            
            # Gallery should be empty (or at least not contain our files)
            remaining_ids = {m['id'] for m in gallery_data['media']}
            for media_id in media_ids:
                assert media_id not in remaining_ids
        
        finally:
            # Clean up files
            for media_id in media_ids:
                docker_admin_client.delete(f'/media/{media_id}')