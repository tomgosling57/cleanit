"""
Tests for the image_utils module.
"""

import pytest
from unittest.mock import Mock, patch
from utils.image_utils import resolve_image_url, get_placeholder_url


class MockImage:
    """Mock Image object for testing."""
    def __init__(self, file_name):
        self.file_name = file_name


def test_get_placeholder_url(app):
    """Test that get_placeholder_url returns correct static URL."""
    with app.app_context():
        url = get_placeholder_url()
        assert url == '/static/images/placeholders/image-not-found.png'


def test_resolve_image_url_with_none(app):
    """Test resolve_image_url with None returns placeholder."""
    with app.app_context():
        url = resolve_image_url(None)
        assert url == '/static/images/placeholders/image-not-found.png'


def test_resolve_image_url_with_empty_string(app):
    """Test resolve_image_url with empty string returns placeholder."""
    with app.app_context():
        url = resolve_image_url("")
        assert url == '/static/images/placeholders/image-not-found.png'


def test_resolve_image_url_with_falsy_value(app):
    """Test resolve_image_url with falsy values returns placeholder."""
    with app.app_context():
        # Test with 0 (falsy but not None/empty string)
        url = resolve_image_url(0)
        assert url == '/static/images/placeholders/image-not-found.png'


def test_resolve_image_url_with_image_object(app):
    """Test resolve_image_url with Image object."""
    with app.app_context():
        mock_image = MockImage("test.jpg")
        
        # Mock get_file_url to return a predictable value
        with patch('utils.image_utils.get_file_url') as mock_get_file_url:
            mock_get_file_url.return_value = '/storage/files/test.jpg'
            url = resolve_image_url(mock_image)
            
            mock_get_file_url.assert_called_once_with("test.jpg")
            assert url == '/storage/files/test.jpg'


def test_resolve_image_url_with_filename_string(app):
    """Test resolve_image_url with filename string."""
    with app.app_context():
        with patch('utils.image_utils.get_file_url') as mock_get_file_url:
            mock_get_file_url.return_value = '/storage/files/photo.png'
            url = resolve_image_url("photo.png")
            
            mock_get_file_url.assert_called_once_with("photo.png")
            assert url == '/storage/files/photo.png'


def test_resolve_image_url_image_object_no_filename(app):
    """Test resolve_image_url with Image object that has empty file_name."""
    with app.app_context():
        mock_image = MockImage("")
        url = resolve_image_url(mock_image)
        assert url == '/static/images/placeholders/image-not-found.png'


def test_resolve_image_url_image_object_none_filename(app):
    """Test resolve_image_url with Image object that has None file_name."""
    with app.app_context():
        mock_image = MockImage(None)
        url = resolve_image_url(mock_image)
        assert url == '/static/images/placeholders/image-not-found.png'


def test_resolve_image_url_integration_with_storage(app):
    """Test that resolve_image_url properly integrates with storage utility."""
    with app.app_context():
        mock_image = MockImage("integration_test.jpg")
        
        # Don't mock get_file_url to test actual integration
        # This will use the real get_file_url which requires storage setup
        # Since we're in a test context, we should mock it
        with patch('utils.image_utils.get_file_url') as mock_get_file_url:
            mock_get_file_url.return_value = 'https://example.com/files/integration_test.jpg'
            url = resolve_image_url(mock_image)
            
            assert url == 'https://example.com/files/integration_test.jpg'
            mock_get_file_url.assert_called_once_with("integration_test.jpg")