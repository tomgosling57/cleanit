"""
Tests for the media_utils module.
"""

import pytest
from unittest.mock import Mock, patch
from utils.media_utils import resolve_image_url, get_placeholder_url, resolve_media_url, MEDIA_TYPE_IMAGE


class MockImage:
    """Mock Image object for testing."""
    def __init__(self, file_name):
        self.file_name = file_name


def test_get_placeholder_url(app):
    """Test that get_placeholder_url returns correct static URL."""
    with app.app_context():
        url = get_placeholder_url()
        assert url == '/static/images/placeholders/image-not-found.png'


@pytest.mark.parametrize("input_value,expected_placeholder", [
    (None, True),
    ("", True),
    (0, True),  # falsy but not None/empty string
])
def test_resolve_image_url_edge_cases(app, input_value, expected_placeholder):
    """Test resolve_image_url with edge cases that should return placeholder."""
    with app.app_context():
        url = resolve_image_url(input_value)
        assert url == '/static/images/placeholders/image-not-found.png'


@pytest.mark.parametrize("input_type,input_value,filename", [
    ("image_object", MockImage("test.jpg"), "test.jpg"),
    ("filename_string", "photo.png", "photo.png"),
])
def test_resolve_image_url_valid_inputs(app, input_type, input_value, filename):
    """Test resolve_image_url with valid inputs (Image object or filename string)."""
    with app.app_context():
        with patch('utils.media_utils.get_file_url') as mock_get_file_url:
            mock_get_file_url.return_value = f'/storage/files/{filename}'
            url = resolve_image_url(input_value)
            
            mock_get_file_url.assert_called_once_with(filename)
            assert url == f'/storage/files/{filename}'


@pytest.mark.parametrize("filename", [
    "",
    None,
])
def test_resolve_image_url_image_object_invalid_filename(app, filename):
    """Test resolve_image_url with Image object that has empty or None file_name."""
    with app.app_context():
        mock_image = MockImage(filename)
        url = resolve_image_url(mock_image)
        assert url == '/static/images/placeholders/image-not-found.png'


def test_resolve_image_url_integration_with_storage(app):
    """Test that resolve_image_url properly integrates with storage utility."""
    with app.app_context():
        mock_image = MockImage("integration_test.jpg")
        
        with patch('utils.media_utils.get_file_url') as mock_get_file_url:
            mock_get_file_url.return_value = 'https://example.com/files/integration_test.jpg'
            url = resolve_image_url(mock_image)
            
            assert url == 'https://example.com/files/integration_test.jpg'
            mock_get_file_url.assert_called_once_with("integration_test.jpg")


# Additional tests for new media_utils functions
def test_resolve_media_url_with_video_type(app):
    """Test resolve_media_url with video media type."""
    with app.app_context():
        mock_media = MockImage("video.mp4")
        with patch('utils.media_utils.get_file_url') as mock_get_file_url:
            mock_get_file_url.return_value = '/storage/files/video.mp4'
            url = resolve_media_url(mock_media, MEDIA_TYPE_IMAGE)  # default image type
            mock_get_file_url.assert_called_once_with("video.mp4")
            assert url == '/storage/files/video.mp4'


def test_get_placeholder_media_url_video(app):
    """Test get_placeholder_media_url for video type."""
    with app.app_context():
        # Assuming placeholder exists for video
        url = resolve_media_url(None, MEDIA_TYPE_IMAGE)
        assert url == '/static/images/placeholders/image-not-found.png'