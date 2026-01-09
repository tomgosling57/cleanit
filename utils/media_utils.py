"""
Media utility module for handling media file operations, validation, and URL resolution.

This module provides infrastructure-level utilities for media processing, including
file type identification, validation, thumbnail generation, metadata extraction,
transcoding, storage operations, and URL resolution for both images and videos.
"""

import os
import mimetypes
from typing import Optional, Dict, Any, Tuple
from flask import url_for, current_app
from PIL import Image, UnidentifiedImageError
import subprocess
import tempfile
import shutil

from utils.storage import (
    upload_flask_file,
    get_file_url,
    delete_file,
    validate_and_upload,
    file_exists,
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
)


# Media type constants
MEDIA_TYPE_IMAGE = 'image'
MEDIA_TYPE_VIDEO = 'video'
MEDIA_TYPE_DOCUMENT = 'document'
MEDIA_TYPE_AUDIO = 'audio'

# Supported MIME types for each media type
SUPPORTED_MIME_TYPES = {
    MEDIA_TYPE_IMAGE: {'image/jpeg', 'image/png', 'image/gif', 'image/webp'},
    MEDIA_TYPE_VIDEO: {'video/mp4', 'video/webm', 'video/ogg'},
    MEDIA_TYPE_DOCUMENT: {'application/pdf'},
    MEDIA_TYPE_AUDIO: {'audio/mpeg', 'audio/wav', 'audio/ogg'},
}

# Placeholder filenames per media type (assuming they exist in static/images/placeholders/)
PLACEHOLDER_FILENAMES = {
    MEDIA_TYPE_IMAGE: 'image-not-found.png',
    MEDIA_TYPE_VIDEO: 'video-not-found.png',
    MEDIA_TYPE_DOCUMENT: 'document-not-found.png',
    MEDIA_TYPE_AUDIO: 'audio-not-found.png',
}


def identify_file_type(file_stream) -> Tuple[str, str]:
    """
    Determine if a file is an image, video, or other type based on magic numbers or MIME type.
    
    Args:
        file_stream: A file-like object (with read() and seek() methods)
        
    Returns:
        Tuple[str, str]: (media_type, mime_type) e.g., ('image', 'image/jpeg')
        
    Raises:
        ValueError: If file type cannot be identified or is unsupported.
    """
    # Save current stream position to restore later
    original_position = file_stream.tell()
    
    # Save to temp file for magic number detection
    with tempfile.NamedTemporaryFile(delete=False, suffix='.tmp') as tmp:
        shutil.copyfileobj(file_stream, tmp)
        tmp_path = tmp.name
    
    try:
        # Use python-magic if available, fallback to mimetypes
        try:
            import magic
            mime_type = magic.from_file(tmp_path, mime=True)
        except ImportError:
            # Fallback to mimetypes based on extension (less reliable)
            # Since we don't have original filename, guess from content
            mime_type = mimetypes.guess_type(tmp_path)[0]
            if not mime_type:
                # Read first few bytes for simple detection
                with open(tmp_path, 'rb') as f:
                    header = f.read(12)
                if header.startswith(b'\xff\xd8\xff'):
                    mime_type = 'image/jpeg'
                elif header.startswith(b'\x89PNG\r\n\x1a\n'):
                    mime_type = 'image/png'
                elif header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):
                    mime_type = 'image/gif'
                elif header.startswith(b'\x1a\x45\xdf\xa3'):
                    mime_type = 'video/webm'
                elif header.startswith(b'\x00\x00\x00 ftyp'):
                    mime_type = 'video/mp4'
                else:
                    mime_type = 'application/octet-stream'
        
        # Map MIME type to media type
        for media_type, allowed_mimes in SUPPORTED_MIME_TYPES.items():
            if mime_type in allowed_mimes:
                # Restore stream position before returning
                file_stream.seek(original_position)
                return media_type, mime_type
        
        # If not in supported list, try to infer from MIME prefix
        if mime_type.startswith('image/'):
            file_stream.seek(original_position)
            return MEDIA_TYPE_IMAGE, mime_type
        elif mime_type.startswith('video/'):
            file_stream.seek(original_position)
            return MEDIA_TYPE_VIDEO, mime_type
        elif mime_type.startswith('audio/'):
            file_stream.seek(original_position)
            return MEDIA_TYPE_AUDIO, mime_type
        else:
            file_stream.seek(original_position)
            return MEDIA_TYPE_DOCUMENT, mime_type
            
    finally:
        os.unlink(tmp_path)
        # Ensure stream position is restored even if an exception occurs
        file_stream.seek(original_position)


def validate_media(file_stream, media_type: str) -> bool:
    """
    Validate file integrity and security based on its identified media_type.
    
    Args:
        file_stream: A file-like object
        media_type: One of MEDIA_TYPE_* constants
        
    Returns:
        bool: True if valid, False otherwise
        
    Raises:
        ValueError: If validation fails with specific reason.
    """
    # Check file size
    file_stream.seek(0, 2)  # Seek to end
    size = file_stream.tell()
    file_stream.seek(0)  # Reset
    
    if size > MAX_FILE_SIZE:
        raise ValueError(f'File too large (max {MAX_FILE_SIZE} bytes)')
    
    # Basic format validation per media type
    if media_type == MEDIA_TYPE_IMAGE:
        try:
            img = Image.open(file_stream)
            img.verify()  # Verify integrity
            file_stream.seek(0)
        except (UnidentifiedImageError, IOError) as e:
            raise ValueError(f'Invalid image file: {e}')
    
    elif media_type == MEDIA_TYPE_VIDEO:
        # Simple validation: check if file has video extension
        # In production, use ffprobe or similar
        pass  # Stub for now
    
    # Additional security checks could be added (e.g., virus scanning)
    
    return True


def generate_thumbnail(file_path: str, media_type: str, output_path: str, size: Tuple[int, int] = (200, 200)) -> str:
    """
    Generate a thumbnail for the given media file.
    
    Args:
        file_path: Path to the source media file
        media_type: One of MEDIA_TYPE_* constants
        output_path: Path where thumbnail should be saved
        size: Desired thumbnail dimensions (width, height)
        
    Returns:
        str: Path to the generated thumbnail
        
    Raises:
        NotImplementedError: For unsupported media types
        ValueError: If generation fails
    """
    if media_type == MEDIA_TYPE_IMAGE:
        try:
            img = Image.open(file_path)
            img.thumbnail(size, Image.Resampling.LANCZOS)
            img.save(output_path)
            return output_path
        except Exception as e:
            raise ValueError(f'Failed to generate image thumbnail: {e}')
    
    elif media_type == MEDIA_TYPE_VIDEO:
        # Use ffmpeg to extract a frame at 1 second
        try:
            cmd = [
                'ffmpeg', '-i', file_path,
                '-ss', '00:00:01',
                '-vframes', '1',
                '-vf', f'scale={size[0]}:{size[1]}',
                '-y', output_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return output_path
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            raise ValueError(f'Failed to generate video thumbnail: {e}. Ensure ffmpeg is installed.')
    
    else:
        raise NotImplementedError(f'Thumbnail generation not implemented for {media_type}')


def extract_metadata(file_path: str, media_type: str) -> Dict[str, Any]:
    """
    Extract metadata from media file.
    
    Args:
        file_path: Path to the media file
        media_type: One of MEDIA_TYPE_* constants
        
    Returns:
        Dict[str, Any]: Metadata dictionary with keys specific to media type
    """
    metadata = {}
    
    if media_type == MEDIA_TYPE_IMAGE:
        try:
            with Image.open(file_path) as img:
                metadata['width'], metadata['height'] = img.size
                metadata['format'] = img.format
                metadata['mode'] = img.mode
                # EXIF data if available
                if hasattr(img, '_getexif') and img._getexif():
                    metadata['exif'] = dict(img._getexif())
        except Exception as e:
            current_app.logger.warning(f'Failed to extract image metadata: {e}')
    
    elif media_type == MEDIA_TYPE_VIDEO:
        # Use ffprobe to extract video metadata
        try:
            cmd = [
                'ffprobe', '-v', 'quiet',
                '-print_format', 'json',
                '-show_format', '-show_streams',
                file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            import json
            probe_data = json.loads(result.stdout)
            
            # Extract relevant info
            video_stream = next((s for s in probe_data['streams'] if s['codec_type'] == 'video'), None)
            if video_stream:
                metadata['width'] = int(video_stream.get('width', 0))
                metadata['height'] = int(video_stream.get('height', 0))
                metadata['codec'] = video_stream.get('codec_name')
                metadata['duration'] = float(probe_data['format'].get('duration', 0))
                metadata['bit_rate'] = int(probe_data['format'].get('bit_rate', 0))
                metadata['resolution'] = f"{metadata['width']}x{metadata['height']}"
                metadata['aspect_ratio'] = video_stream.get('display_aspect_ratio', '16:9')
        except (subprocess.CalledProcessError, FileNotFoundError, KeyError) as e:
            current_app.logger.warning(f'Failed to extract video metadata: {e}')
    
    return metadata


def transcode_video(input_path: str, output_path: str, format: str = 'mp4') -> str:
    """
    Convert videos to different formats.
    
    Args:
        input_path: Path to source video
        output_path: Path for transcoded video
        format: Target format ('mp4', 'webm', 'ogg')
        
    Returns:
        str: Path to transcoded video
        
    Raises:
        ValueError: If transcoding fails
    """
    # Map format to codec and container
    codec_map = {
        'mp4': 'libx264',
        'webm': 'libvpx-vp9',
        'ogg': 'libtheora',
    }
    
    if format not in codec_map:
        raise ValueError(f'Unsupported format: {format}')
    
    try:
        cmd = [
            'ffmpeg', '-i', input_path,
            '-c:v', codec_map[format],
            '-c:a', 'copy' if format == 'mp4' else 'libvorbis',
            '-y', output_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return output_path
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise ValueError(f'Video transcoding failed: {e}. Ensure ffmpeg is installed.')


def upload_media_to_storage(file_stream, filename: str, media_type: str) -> str:
    """
    Handles storage upload, potentially calling utils.storage for the actual storage mechanism.
    
    Args:
        file_stream: A file-like object
        filename: Original filename
        media_type: One of MEDIA_TYPE_* constants
        
    Returns:
        str: The unique filename that was uploaded
    """
    # Use existing storage utility for upload
    return upload_flask_file(file_stream, filename)


def delete_media_from_storage(file_path: str) -> bool:
    """
    Deletes the file from the configured storage.
    
    Args:
        file_path: The file path (or filename) to delete
        
    Returns:
        bool: True if deleted, False if not found
    """
    # Extract filename from path if needed
    filename = os.path.basename(file_path)
    return delete_file(filename)


def get_media_url(file_path: str) -> str:
    """
    Provides a URL to access the stored media, adapting for different storage providers.
    
    Args:
        file_path: The file path (or filename) to get URL for
        
    Returns:
        str: URL to access the file
    """
    filename = os.path.basename(file_path)
    return get_file_url(filename)


def get_placeholder_media_url(media_type: str = MEDIA_TYPE_IMAGE) -> str:
    """
    Returns a placeholder URL based on the media_type.
    
    Args:
        media_type: One of MEDIA_TYPE_* constants
        
    Returns:
        str: URL to the placeholder media
    """
    placeholder_filename = PLACEHOLDER_FILENAMES.get(media_type, PLACEHOLDER_FILENAMES[MEDIA_TYPE_IMAGE])
    
    return url_for(
        "static",
        filename=f"images/placeholders/{placeholder_filename}",
        _external=False
    )


# Adapted functions from image_utils.py for generalized media
def resolve_media_url(media, media_type: str = MEDIA_TYPE_IMAGE) -> str:
    """
    Return a fully resolvable URL for the given media.
    
    If the media is missing (None, empty, or has no filename), return the placeholder URL.
    This function is for presentation-layer use by controllers and error handlers.
    
    Args:
        media: A Media object (with file_name attribute), a filename string, or None.
        media_type: The type of media (defaults to 'image')
        
    Returns:
        str: URL to access the media or placeholder if media is missing.
    """
    # Handle missing media
    if not media:
        return get_placeholder_media_url(media_type)
    
    # Extract filename from Media object or use string directly
    filename = getattr(media, "file_name", str(media) if media else None)
    if not filename:
        return get_placeholder_media_url(media_type)
    
    # Use the storage utility to get the actual file URL
    return get_media_url(filename)


# Backward compatibility aliases
def resolve_image_url(image):
    """Alias for resolve_media_url with media_type='image' for backward compatibility."""
    return resolve_media_url(image, MEDIA_TYPE_IMAGE)


def get_placeholder_url():
    """Alias for get_placeholder_media_url with media_type='image' for backward compatibility."""
    return get_placeholder_media_url(MEDIA_TYPE_IMAGE)