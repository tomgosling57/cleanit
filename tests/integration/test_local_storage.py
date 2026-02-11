import pytest
import os
from io import BytesIO
from flask import url_for
from werkzeug.datastructures import FileStorage
from unittest.mock import patch, MagicMock

# Assuming utils.storage and routes.storage are in the path
from utils.storage import (
    allowed_file, upload_flask_file, get_file_url,
    delete_file, file_exists, validate_and_upload,
    MAX_FILE_SIZE, ALLOWED_EXTENSIONS
)

# Fixture for a Flask client with local storage configured
@pytest.fixture
def client_local(local_storage_app):
    with local_storage_app.test_client() as client:
        yield client


# --- Test allowed_file function ---
def test_allowed_file():
    assert allowed_file("image.png") is True
    assert allowed_file("document.pdf") is True
    assert allowed_file("video.mp4") is True
    assert allowed_file("photo.JPG") is True
    assert allowed_file("script.exe") is False
    assert allowed_file("archive.zip") is False
    assert allowed_file("noextension") is False
    assert allowed_file(".bashrc") is False


# --- Combined upload tests ---
def test_upload_functions(client_local, local_storage_app):
    """Test upload_flask_file and validate_and_upload functions."""
    with local_storage_app.app_context():
        # Test upload_flask_file
        data = b"test file content"
        filename = "test_upload.png"
        flask_file = FileStorage(
            stream=BytesIO(data),
            filename=filename,
            content_type="image/png"
        )

        uploaded_filename = upload_flask_file(flask_file)
        assert uploaded_filename is not None
        name, ext = os.path.splitext(filename)
        assert name in uploaded_filename
        assert ext in uploaded_filename

        # Verify file exists in the upload folder
        upload_folder = local_storage_app.config['UPLOAD_FOLDER']
        expected_path = os.path.join(upload_folder, uploaded_filename)
        assert os.path.exists(expected_path)

        with open(expected_path, 'rb') as f:
            assert f.read() == data

        # Test validate_and_upload with valid file
        valid_data = b"valid content"
        valid_filename = "valid.png"
        valid_file = FileStorage(stream=BytesIO(valid_data), filename=valid_filename, content_type="image/png")
        validated_filename = validate_and_upload(valid_file)
        assert validated_filename is not None
        assert file_exists(validated_filename)

        # Test validate_and_upload with no file
        with pytest.raises(ValueError, match='No file provided'):
            validate_and_upload(None)

        # Test validate_and_upload with invalid file type
        invalid_filename = "invalid.exe"
        invalid_file = FileStorage(stream=BytesIO(b"exe content"), filename=invalid_filename, content_type="application/octet-stream")
        with pytest.raises(ValueError, match='File type not allowed'):
            validate_and_upload(invalid_file)

        # Test validate_and_upload with file too large
        large_data = b"a" * (MAX_FILE_SIZE + 1)
        large_file = FileStorage(stream=BytesIO(large_data), filename="large.png", content_type="image/png")
        with pytest.raises(ValueError, match='File too large'):
            validate_and_upload(large_file)


# --- Test get_file_url function (local storage) ---
def test_get_file_url_local(client_local, local_storage_app):
    with local_storage_app.app_context():
        with local_storage_app.test_request_context():
            filename = "some_file.jpg"
            url = get_file_url(filename)
            assert url == url_for('media.serve_media', filename=filename, _external=True)
            assert 'http://localhost' in url # Ensure it's an external URL for testing


# --- Combined file existence and deletion tests ---
def test_file_operations(client_local, local_storage_app):
    """Test file_exists and delete_file functions."""
    with local_storage_app.app_context():
        upload_folder = local_storage_app.config['UPLOAD_FOLDER']
        
        # Test file_exists with existing file
        test_filename = "existing_file.txt"
        test_filepath = os.path.join(upload_folder, test_filename)
        with open(test_filepath, 'w') as f:
            f.write("hello world")

        assert file_exists(test_filename) is True
        assert file_exists("non_existent_file.txt") is False

        # Test delete_file
        delete_filename = "file_to_delete.pdf"
        delete_filepath = os.path.join(upload_folder, delete_filename)
        with open(delete_filepath, 'w') as f:
            f.write("delete me")

        assert os.path.exists(delete_filepath)
        delete_file(delete_filename)
        assert not os.path.exists(delete_filepath)
        
        # Assert that the upload folder is empty or doesn't exist (libcloud may delete empty container)
        if os.path.exists(upload_folder):
            # There might be other test files, so we can't assert it's empty
            pass
            
        # Deleting non-existent file should return False
        assert delete_file("non_existent_file_to_delete.txt") is False


# --- Test serve_file route (local storage) ---
def test_serve_file_route_local(client_local, local_storage_app):
    with local_storage_app.app_context():
        with local_storage_app.test_request_context():
            # Create a dummy file in the upload folder
            upload_folder = local_storage_app.config['UPLOAD_FOLDER']
            test_filename = "served_file.txt"
            test_filepath = os.path.join(upload_folder, test_filename)
            file_content = b"This is the content of the served file."
            with open(test_filepath, 'wb') as f:
                f.write(file_content)

        response = client_local.get(f'/media/serve/{test_filename}')
        assert response.status_code == 200
        assert response.data == file_content
        assert response.headers['Content-Type'] == 'text/plain; charset=utf-8'

        # Test file not found
        response = client_local.get('/media/serve/non_existent_file.txt')
        assert response.status_code == 404
        assert b"File not found" in response.data

        # Test with STORAGE_PROVIDER set to s3 (should return 404 with error message)
        # Patch the app config instead of os.environ since routes/storage.py now uses current_app.config
        original_provider = local_storage_app.config.get('STORAGE_PROVIDER')
        local_storage_app.config['STORAGE_PROVIDER'] = 's3'
        try:
            response = client_local.get(f'/media/serve/{test_filename}')
            assert response.status_code == 404
            assert b"File serving not available when STORAGE_PROVIDER is 's3'" in response.data
        finally:
            local_storage_app.config['STORAGE_PROVIDER'] = original_provider