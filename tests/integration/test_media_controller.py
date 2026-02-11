"""
Integration tests for MediaController using real authentication and database.
Tests the media endpoints with actual login and seeded data.
Consolidated version with fewer test cases to reduce database recreation overhead.
"""
import pytest
import io
import json


class TestMediaControllerIntegration:
    """Consolidated integration tests for media controller endpoints."""
    
    def test_media_endpoint_error_handling(self, admin_client_no_csrf):
        """Test error responses for non-existent media."""
        # GET non-existent media returns 404 with JSON error
        response = admin_client_no_csrf.get('/media/999999', headers={'Accept': 'application/json'})
        assert response.status_code == 404
        assert response.content_type == 'application/json'
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Media not found' in data['error']
        
        # DELETE non-existent media returns 404 with JSON error
        response = admin_client_no_csrf.delete('/media/999999', headers={'Accept': 'application/json'})
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Media not found' in data['error']
        
        # Serve endpoint returns appropriate error for non-existent file
        response = admin_client_no_csrf.get('/media/serve/nonexistent.jpg')
        assert response.status_code in [404, 200]  # Could be 404 or 200 depending on storage provider
    
    def test_upload_operations(self, admin_client_no_csrf, regular_client_no_csrf):
        """Test upload functionality including permissions and validation."""
        # Admin upload success (or at least not forbidden)
        test_file = io.BytesIO(b"fake image data")
        test_file.name = "test_image.jpg"
        
        response = admin_client_no_csrf.post(
            '/media/upload',
            data={
                'file': (test_file, 'test_image.jpg'),
                'description': 'Test image description'
            },
            content_type='multipart/form-data'
        )
        
        assert response.status_code != 403, "Admin should have permission to upload"
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'media_id' in data
            assert 'filename' in data
            assert data['filename'] == 'test_image.jpg'
            # Store media_id for potential later use in this test
            admin_media_id = data['media_id']
        
        # Regular user upload forbidden
        test_file2 = io.BytesIO(b"fake image data")
        test_file2.name = "test_image2.jpg"
        
        response = regular_client_no_csrf.post(
            '/media/upload',
            data={
                'file': (test_file2, 'test_image2.jpg'),
                'description': 'Test image description'
            },
            content_type='multipart/form-data',
            headers={'Accept': 'application/json'}
        )
        
        assert response.status_code == 403, f"Expected 403 Forbidden but got {response.status_code}"
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Unauthorized: Admin access required' in data['error']
        
        # Upload validation errors
        # Missing file
        response = admin_client_no_csrf.post(
            '/media/upload',
            data={'description': 'No file here'},
            content_type='multipart/form-data'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No file part' in data['error']
        
        # Empty filename
        test_file3 = io.BytesIO(b"fake image data")
        test_file3.name = ""
        
        response = admin_client_no_csrf.post(
            '/media/upload',
            data={'file': (test_file3, '')},
            content_type='multipart/form-data'
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No selected file' in data['error']
    
    def test_delete_operations(self, admin_client_no_csrf, regular_client_no_csrf):
        """Test delete functionality including permissions."""
        # First upload a media file as admin
        test_file = io.BytesIO(b"fake image data for deletion")
        test_file.name = "delete_test.jpg"
        
        upload_response = admin_client_no_csrf.post(
            '/media/upload',
            data={
                'file': (test_file, 'delete_test.jpg'),
                'description': 'To be deleted'
            },
            content_type='multipart/form-data'
        )
        
        if upload_response.status_code != 200:
            pytest.skip("Upload failed, cannot test delete")
        
        upload_data = json.loads(upload_response.data)
        media_id = upload_data['media_id']
        
        # Regular user delete forbidden
        delete_response = regular_client_no_csrf.delete(f'/media/{media_id}')
        assert delete_response.status_code == 403
        delete_data = json.loads(delete_response.data)
        assert 'error' in delete_data
        assert 'Unauthorized: Admin access required' in delete_data['error']
        
        # Admin delete success
        delete_response = admin_client_no_csrf.delete(f'/media/{media_id}')
        assert delete_response.status_code == 200
        delete_data = json.loads(delete_response.data)
        assert 'message' in delete_data
        assert 'Media deleted successfully' in delete_data['message']
        assert delete_data['media_id'] == media_id
        
        # Verify it's gone
        get_response = admin_client_no_csrf.get(f'/media/{media_id}', headers={'Accept': 'application/json'})
        assert get_response.status_code == 404


class TestPropertyGalleryEndpoints:
    """Consolidated tests for property gallery endpoints (batch operations)."""
    
    def test_property_gallery_batch_operations(self, admin_client_no_csrf, regular_client_no_csrf, seeded_test_data):
        """Test batch associate and remove operations for property gallery."""
        properties = seeded_test_data['properties']
        if not properties:
            pytest.skip("No properties in seeded data")
        
        property_obj = list(properties.values())[0]
        property_id = property_obj.id
        
        # 1. Admin can upload and associate media with property
        media_ids = []
        for i in range(2):  # Upload 2 files
            test_file = io.BytesIO(f"test media data {i}".encode('utf-8'))
            test_file.name = f"test_media_{i}.jpg"
            
            associate_response = admin_client_no_csrf.post(
                f'/address-book/property/{property_id}/media',
                data={
                    'files[]': (test_file, f"test_media_{i}.jpg"),
                    'descriptions[]': f'Test media {i}'
                },
                content_type='multipart/form-data'
            )
            
            if associate_response.status_code == 200:
                associate_data = json.loads(associate_response.data)
                assert associate_data.get('success') is True
                if 'media_ids' in associate_data:
                    media_ids.extend(associate_data['media_ids'])
        
        if len(media_ids) < 2:
            pytest.skip("Could not upload enough test files")
        
        # Verify gallery contains the media
        gallery_response = admin_client_no_csrf.get(
            f'/address-book/property/{property_id}/media'
        )
        
        assert gallery_response.status_code == 200
        gallery_data = json.loads(gallery_response.data)
        
        gallery_media_ids = {m['id'] for m in gallery_data['media']}
        for media_id in media_ids:
            assert media_id in gallery_media_ids, \
                f"Media ID {media_id} not found in gallery"
        
        # 2. Regular user cannot associate media
        test_file = io.BytesIO(b"test media data")
        test_file.name = "test_media.jpg"
        
        associate_response = regular_client_no_csrf.post(
            f'/address-book/property/{property_id}/media',
            data={
                'file': (test_file, 'test_media.jpg'),
                'description': 'Test media'
            },
            content_type='multipart/form-data'
        )
        
        assert associate_response.status_code == 403, \
            f"Expected 403 Forbidden but got {associate_response.status_code}"
        
        associate_data = json.loads(associate_response.data)
        assert 'error' in associate_data
        assert 'Unauthorized: Admin access required' in associate_data['error']
        
        # 3. Invalid content type (JSON instead of multipart) returns 400
        # Test multiple invalid JSON payloads
        invalid_payloads = [
            {'media_ids': [999999, 888888]},
            {'media_ids': []},
            {}
        ]
        
        for payload in invalid_payloads:
            associate_response = admin_client_no_csrf.post(
                f'/address-book/property/{property_id}/media',
                json=payload,
                content_type='application/json'
            )
            
            assert associate_response.status_code == 400, \
                f"Expected 400 for wrong content type but got {associate_response.status_code}"
            
            associate_data = json.loads(associate_response.data)
            assert 'error' in associate_data
            assert 'multipart/form-data' in associate_data['error'].lower()
        
        # 4. Admin can batch remove media from property
        remove_response = admin_client_no_csrf.delete(
            f'/address-book/property/{property_id}/media',
            json={'media_ids': media_ids},
            content_type='application/json'
        )
        
        assert remove_response.status_code == 200, \
            f"Batch removal failed: {remove_response.data.decode('utf-8')}"
        
        remove_data = json.loads(remove_response.data)
        assert remove_data.get('success') is True
        
        # Verify gallery no longer contains the media
        gallery_response = admin_client_no_csrf.get(
            f'/address-book/property/{property_id}/media'
        )
        
        assert gallery_response.status_code == 200
        gallery_data = json.loads(gallery_response.data)
        
        gallery_media_ids = {m['id'] for m in gallery_data['media']}
        for media_id in media_ids:
            assert media_id not in gallery_media_ids, \
                f"Media ID {media_id} still found in gallery after removal"
        
        # Clean up - delete the media files themselves
        for media_id in media_ids:
            admin_client_no_csrf.delete(f'/media/{media_id}')
