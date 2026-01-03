import os
from flask import url_for
from libcloud.common.types import ObjectDoesNotExistError
from libcloud.storage.base import StorageDriver

CHUNK_SIZE = 8192

def upload_flask_file(file_storage_object, container, object_name):
    """
    Uploads a file from a werkzeug.FileStorage object to a Libcloud container.

    :param file_storage_object: werkzeug.FileStorage object
    :param container: Libcloud container object
    :param object_name: Desired object name
    :return: Uploaded object
    """
    def file_iterator(file_storage):
        while True:
            chunk = file_storage.read(CHUNK_SIZE)
            if not chunk:
                break
            yield chunk

    uploaded_object = container.upload_object_via_stream(
        iterator=file_iterator(file_storage_object),
        object_name=object_name
    )
    return uploaded_object

def get_file_url(app, container, object_name):
    """
    Generates a URL for the given object.

    :param app: Flask app instance
    :param container: Libcloud container object
    :param object_name: Object name
    :return: URL for the object or None if the object does not exist
    """
    storage_provider = app.config.get('STORAGE_PROVIDER')
    if storage_provider == 'local':
        return url_for('uploads', filename=object_name)
    elif storage_provider == 's3':
        try:
            obj = container.get_object(object_name)
            return obj.get_cdn_url()
        except ObjectDoesNotExistError:
            return None
    return None

def delete_file(container, object_name):
    """
    Deletes a file from the container.

    :param container: Libcloud container object
    :param object_name: Object name
    :return: True if the object was deleted, False if it did not exist
    """
    try:
        container.delete_object(object_name)
        return True
    except ObjectDoesNotExistError:
        return False

def file_exists(container, object_name):
    """
    Checks if a file exists in the container.

    :param container: Libcloud container object
    :param object_name: Object name
    :return: True if the object exists, False otherwise
    """
    try:
        container.get_object(object_name)
        return True
    except ObjectDoesNotExistError:
        return False