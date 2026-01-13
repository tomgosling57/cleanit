
# Unit tests for MediaController with mocked dependencies
class TestMediaControllerUnit:
    """Unit tests for MediaController with mocked dependencies."""
    
    def test_upload_media_regular_user_returns_403(self, app):
        """Test that regular user gets 403 Forbidden, not 401 Unauthorized."""
        from controllers.media_controller import MediaController
        from services.media_service import MediaService
        from unittest.mock import Mock, patch, MagicMock
        
        # Mock media service
        mock_media_service = Mock(spec=MediaService)
        
        # Create controller
        controller = MediaController(media_service=mock_media_service)
        
        # Mock current_user as regular user
        regular_user = Mock()
        regular_user.role = 'user'
        regular_user.is_authenticated = True
        
        # Mock request with file
        mock_request = Mock()
        mock_request.method = 'POST'
        mock_file = Mock()
        mock_file.filename = 'test.jpg'
        mock_file.seek = Mock()
        mock_file.tell = Mock(return_value=100)
        # Mock request.files as a dict that supports 'in' operator and .get() method
        mock_files = {'file': mock_file}
        mock_request.files = mock_files
        mock_request.form = {'description': 'Test'}
        
        # Mock media utils functions
        with patch('controllers.media_controller.request', mock_request), \
             patch('controllers.media_controller.current_user', regular_user), \
             patch('controllers.media_controller.identify_file_type') as mock_identify, \
             patch('controllers.media_controller.validate_media') as mock_validate, \
             patch('controllers.media_controller.upload_media_to_storage') as mock_upload, \
             patch('controllers.media_controller.extract_metadata') as mock_extract, \
             patch('controllers.media_controller.get_media_url') as mock_url:
            
            mock_identify.return_value = ('image', 'image/jpeg')
            mock_upload.return_value = 'test.jpg'
            mock_url.return_value = 'http://example.com/test.jpg'
            
            # Call the controller method
            response, status_code = controller.upload_media()
            
            # Should return 403 because regular user is not admin
            assert status_code == 403
            assert 'error' in response.json
            assert 'Unauthorized: Admin access required' in response.json['error']
    
    def test_upload_media_admin_succeeds(self, app):
        """Test that admin user can upload successfully."""
        from controllers.media_controller import MediaController
        from services.media_service import MediaService
        from unittest.mock import Mock, patch, MagicMock
        from database import Media
        
        # Mock media service
        mock_media_service = Mock(spec=MediaService)
        mock_media = Mock(spec=Media)
        mock_media.id = 1
        mock_media.filename = 'test.jpg'
        mock_media.file_path = 'test.jpg'
        mock_media.media_type = 'image'
        mock_media.mimetype = 'image/jpeg'
        mock_media.size_bytes = 100
        mock_media.description = 'Test'
        mock_media_service.add_media.return_value = mock_media
        
        # Create controller
        controller = MediaController(media_service=mock_media_service)
        
        # Mock current_user as admin
        admin_user = Mock()
        admin_user.role = 'admin'
        admin_user.is_authenticated = True
        
        # Mock request with file
        mock_request = Mock()
        mock_request.method = 'POST'
        mock_file = Mock()
        mock_file.filename = 'test.jpg'
        mock_file.seek = Mock()
        mock_file.tell = Mock(return_value=100)
        # Mock request.files as a dict that supports 'in' operator and .get() method
        mock_files = {'file': mock_file}
        mock_request.files = mock_files
        mock_request.form = {'description': 'Test'}
        
        # Mock media utils functions
        with patch('controllers.media_controller.request', mock_request), \
             patch('controllers.media_controller.current_user', admin_user), \
             patch('controllers.media_controller.identify_file_type') as mock_identify, \
             patch('controllers.media_controller.validate_media') as mock_validate, \
             patch('controllers.media_controller.upload_media_to_storage') as mock_upload, \
             patch('controllers.media_controller.extract_metadata') as mock_extract, \
             patch('controllers.media_controller.get_media_url') as mock_url:
            
            mock_identify.return_value = ('image', 'image/jpeg')
            mock_upload.return_value = 'test.jpg'
            mock_url.return_value = 'http://example.com/test.jpg'
            mock_extract.return_value = {}
            
            # Call the controller method
            response, status_code = controller.upload_media()
            
            # Should return 200
            assert status_code == 200
            assert 'media_id' in response.json
            assert response.json['media_id'] == 1
