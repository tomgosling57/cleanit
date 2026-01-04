import pytest
import os
import random
from flask import Flask
from werkzeug.datastructures import FileStorage
from tests.helpers import login_admin, get_csrf_token
from io import BytesIO
from PIL import Image
import base64
from playwright.sync_api import Page

# Helper functions to generate images using Pillow
def generate_png_image(width, height, filename="test_image.png"):
    """
    Generates a PNG image of random noise using Pillow.
    Returns the filename and the byte content of the image.
    """
    img = Image.new('RGB', (width, height))
    pixels = img.load()
    for i in range(width):
        for j in range(height):
            pixels[i, j] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    
    byte_arr = BytesIO()
    img.save(byte_arr, format='PNG')
    return filename, byte_arr.getvalue()

def generate_jpeg_image(width, height, filename="test_image.jpeg"):
    """
    Generates a JPEG image of random noise using Pillow.
    Returns the filename and the byte content of the image.
    """
    img = Image.new('RGB', (width, height))
    pixels = img.load()
    for i in range(width):
        for j in range(height):
            pixels[i, j] = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
    
    byte_arr = BytesIO()
    img.save(byte_arr, format='JPEG')
    return filename, byte_arr.getvalue()

def test_e2e_png_upload_retrieval_and_deletion(local_storage_app: Flask, page: Page, goto, server_url):
    """
    End-to-end test for PNG file upload, retrieval, and deletion using local storage.
    """
    login_admin(page, goto)
    csrf_token = get_csrf_token(page)

    png_filename, original_png_content = generate_png_image(100, 100, "random_noise.png")
    
    # Encode the image content to base64 for transfer to JavaScript
    encoded_png_content = base64.b64encode(original_png_content).decode('utf-8')

    # Use page.evaluate to send a POST request with FormData
    with page.expect_response(f"**/upload") as response_info:
        page.evaluate(
            """
            async ([filename, contentType, encodedContent, csrfToken]) => {
                const blob = await (await fetch(`data:${contentType};base64,${encodedContent}`)).blob();
                const formData = new FormData();
                formData.append('file', blob, filename);

                const response = await fetch('/upload', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken
                    },
                    body: formData
                });
                return response.json();
            }
            """,
            [png_filename, "image/png", encoded_png_content, csrf_token]
        )
    
    upload_response_png_json = response_info.value.json()
    assert upload_response_png_json['message'] == 'File uploaded successfully'
    uploaded_png_filename = upload_response_png_json['filename']
    assert 'url' in upload_response_png_json

    # Retrieve the PNG file using page.request.get
    retrieval_response_png = page.request.get(f"{server_url}/uploads/{uploaded_png_filename}", headers={'X-CSRFToken': csrf_token})
    assert retrieval_response_png.status == 200
    retrieved_png_content = retrieval_response_png.body()
    assert retrieved_png_content == original_png_content

    # Deletion (still using os.remove for local storage cleanup)
    upload_folder = local_storage_app.config.get('UPLOAD_FOLDER')
    file_path = os.path.join(upload_folder, uploaded_png_filename)
    assert os.path.exists(file_path)
    os.remove(file_path)
    assert not os.path.exists(file_path)

def test_e2e_jpeg_upload_retrieval_and_deletion(local_storage_app: Flask, page: Page, goto, server_url):
    """
    End-to-end test for JPEG file upload, retrieval, and deletion using local storage.
    """
    login_admin(page, goto)
    csrf_token = get_csrf_token(page)

    jpeg_filename, original_jpeg_content = generate_jpeg_image(100, 100, "random_noise.jpeg")
 
    # Encode the image content to base64 for transfer to JavaScript
    encoded_jpeg_content = base64.b64encode(original_jpeg_content).decode('utf-8')

    # Use page.evaluate to send a POST request with FormData
    with page.expect_response(f"**/upload") as response_info:
        page.evaluate(
            """
            async ([filename, contentType, encodedContent, csrfToken]) => {
                const blob = await (await fetch(`data:${contentType};base64,${encodedContent}`)).blob();
                const formData = new FormData();
                formData.append('file', blob, filename);

                const response = await fetch('/upload', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken
                    },
                    body: formData
                });
                return response.json();
            }
            """,
            [jpeg_filename, "image/jpeg", encoded_jpeg_content, csrf_token]
        )
    
    upload_response_jpeg_json = response_info.value.json()
    assert upload_response_jpeg_json['message'] == 'File uploaded successfully'
    uploaded_jpeg_filename = upload_response_jpeg_json['filename']
    assert 'url' in upload_response_jpeg_json

    # Retrieve the JPEG file using page.request.get
    retrieval_response_jpeg = page.request.get(f"{server_url}/uploads/{uploaded_jpeg_filename}", headers={'X-CSRFToken': csrf_token})
    assert retrieval_response_jpeg.status == 200
    retrieved_jpeg_content = retrieval_response_jpeg.body()
    assert retrieved_jpeg_content == original_jpeg_content

    # Deletion (still using os.remove for local storage cleanup)
    upload_folder = local_storage_app.config.get('UPLOAD_FOLDER')
    file_path = os.path.join(upload_folder, uploaded_jpeg_filename)
    assert os.path.exists(file_path)
    os.remove(file_path)
    assert not os.path.exists(file_path)
