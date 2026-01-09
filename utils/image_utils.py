"""
Image utility module for handling image URI resolution and missing image fallback logic.

This module provides presentation-level URL resolution for images, returning placeholder
URLs when images are missing. It is intended for use by controllers and error handlers,
not the service layer.
"""

from flask import url_for
from utils.storage import get_file_url


def resolve_image_url(image):
    """
    Return a fully resolvable URL for the given image.
    
    If the image is missing (None, empty, or has no filename), return the placeholder URL.
    This function is for presentation-layer use by controllers and error handlers.
    
    Args:
        image: An Image object (with file_name attribute), a filename string, or None.
    
    Returns:
        str: URL to access the image or placeholder if image is missing.
    """
    # Handle missing image
    if not image:
        return get_placeholder_url()
    
    # Extract filename from Image object or use string directly
    filename = getattr(image, "file_name", str(image) if image else None)
    if not filename:
        return get_placeholder_url()
    
    # Use the storage utility to get the actual file URL
    return get_file_url(filename)


def get_placeholder_url():
    """
    Get the URL for the placeholder image.
    
    The placeholder image is part of the static collection, not storage or database.
    
    Returns:
        str: URL to the placeholder image.
    """
    return url_for(
        "static",
        filename="images/placeholders/image-not-found.png",
        _external=False
    )