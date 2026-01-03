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