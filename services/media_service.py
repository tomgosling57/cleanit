from database import Media, PropertyMedia, JobMedia
import os
from werkzeug.utils import secure_filename
from typing import List, Dict, Any, Optional


class MediaNotFound(Exception):
    """Exception raised when a media item is not found."""
    pass


class MediaService:
    """
    Service layer for media-related operations.
    Handles CRUD for media and their associations with properties and jobs.
    Supports images, videos, and other media types.
    """

    def __init__(self, db_session):
        self.db_session = db_session

    def _clean_filename(self, filename):
        """
        Ensure the filename stored does not contain any CDN or temporary directory content.
        Extracts the basename, strips query parameters, and applies secure filename cleaning.
        """
        if not filename:
            return filename
        # Remove any URL query parameters (e.g., ?token=abc)
        filename = filename.split('?')[0]
        # Extract basename to remove any directory paths (including CDN paths)
        basename = os.path.basename(filename)
        # Apply secure_filename to ensure safe characters
        cleaned = secure_filename(basename)
        return cleaned

    def add_media(self, file_name, file_path, media_type, mimetype, size_bytes, description=None, metadata=None):
        """
        Create a new media record in the database.

        Args:
            file_name (str): The filename (will be cleaned of CDN/temp paths)
            file_path (str): Path where the file is stored (relative or S3 key)
            media_type (str): Type of media (e.g., 'image', 'video', 'document', 'audio')
            mimetype (str): MIME type (e.g., 'image/jpeg', 'video/mp4')
            size_bytes (int): File size in bytes
            description (str, optional): Description of the media
            metadata (dict, optional): Dictionary containing media-specific attributes:
                - For images: width, height
                - For videos: duration_seconds, thumbnail_url, resolution, codec, aspect_ratio

        Returns:
            Media: The created Media object
        """
        cleaned_file_name = self._clean_filename(file_name)
        # Unpack metadata if provided
        width = metadata.get('width') if metadata else None
        height = metadata.get('height') if metadata else None
        duration_seconds = metadata.get('duration_seconds') if metadata else None
        thumbnail_url = metadata.get('thumbnail_url') if metadata else None
        resolution = metadata.get('resolution') if metadata else None
        codec = metadata.get('codec') if metadata else None
        aspect_ratio = metadata.get('aspect_ratio') if metadata else None

        new_media = Media(
            filename=cleaned_file_name,
            file_path=file_path,
            media_type=media_type,
            mimetype=mimetype,
            size_bytes=size_bytes,
            description=description,
            width=width,
            height=height,
            duration_seconds=duration_seconds,
            thumbnail_url=thumbnail_url,
            resolution=resolution,
            codec=codec,
            aspect_ratio=aspect_ratio
        )
        self.db_session.add(new_media)
        self.db_session.commit()
        self.db_session.refresh(new_media)
        return new_media

    def get_media_by_id(self, media_id):
        """
        Retrieve a media item by its ID.

        Args:
            media_id (int): The media ID

        Returns:
            Media: The Media object if found

        Raises:
            MediaNotFound: If no media with the given ID exists
        """
        media = self.db_session.query(Media).filter_by(id=media_id).first()
        if not media:
            raise MediaNotFound(f"Media with ID {media_id} not found")
        return media

    def get_media_by_filename(self, file_name):
        """
        Retrieve a media item by its filename (after cleaning).

        Args:
            file_name (str): The filename

        Returns:
            Media: The Media object if found

        Raises:
            MediaNotFound: If no media with the given filename exists
        """
        cleaned = self._clean_filename(file_name)
        media = self.db_session.query(Media).filter_by(filename=cleaned).first()
        if not media:
            raise MediaNotFound(f"Media with filename '{file_name}' (cleaned: '{cleaned}') not found")
        return media

    def associate_media_with_property(self, media_id, property_id):
        """
        Create an association between a media item and a property.

        Args:
            media_id (int): The media ID
            property_id (int): The property ID

        Returns:
            PropertyMedia: The created association object
        """
        # Check if association already exists
        existing = self.db_session.query(PropertyMedia).filter_by(
            media_id=media_id,
            property_id=property_id
        ).first()
        if existing:
            return existing

        association = PropertyMedia(
            media_id=media_id,
            property_id=property_id
        )
        self.db_session.add(association)
        self.db_session.commit()
        self.db_session.refresh(association)
        return association

    def associate_media_with_job(self, media_id, job_id):
        """
        Create an association between a media item and a job.

        Args:
            media_id (int): The media ID
            job_id (int): The job ID

        Returns:
            JobMedia: The created association object
        """
        existing = self.db_session.query(JobMedia).filter_by(
            media_id=media_id,
            job_id=job_id
        ).first()
        if existing:
            return existing

        association = JobMedia(
            media_id=media_id,
            job_id=job_id
        )
        self.db_session.add(association)
        self.db_session.commit()
        self.db_session.refresh(association)
        return association

    def get_media_for_property(self, property_id):
        """
        Retrieve all media items associated with a property.

        Args:
            property_id (int): The property ID

        Returns:
            list[Media]: List of Media objects
        """
        associations = self.db_session.query(PropertyMedia).filter_by(
            property_id=property_id
        ).all()
        media_ids = [assoc.media_id for assoc in associations]
        if not media_ids:
            return []
        return self.db_session.query(Media).filter(Media.id.in_(media_ids)).all()

    def get_media_for_job(self, job_id):
        """
        Retrieve all media items associated with a job.

        Args:
            job_id (int): The job ID

        Returns:
            list[Media]: List of Media objects
        """
        associations = self.db_session.query(JobMedia).filter_by(
            job_id=job_id
        ).all()
        media_ids = [assoc.media_id for assoc in associations]
        if not media_ids:
            return []
        return self.db_session.query(Media).filter(Media.id.in_(media_ids)).all()

    def update_media_description(self, media_id, description):
        """
        Update the description of a media item.

        Args:
            media_id (int): The media ID
            description (str): New description

        Returns:
            Media: Updated Media object

        Raises:
            MediaNotFound: If no media with the given ID exists
        """
        media = self.get_media_by_id(media_id)
        media.description = description
        self.db_session.commit()
        self.db_session.refresh(media)
        return media

    def delete_media(self, media_id):
        """
        Delete a media item and all its associations.

        Args:
            media_id (int): The media ID

        Returns:
            bool: True if deleted

        Raises:
            MediaNotFound: If no media with the given ID exists
        """
        media = self.get_media_by_id(media_id)

        # Delete property associations
        self.db_session.query(PropertyMedia).filter_by(media_id=media_id).delete()
        # Delete job associations
        self.db_session.query(JobMedia).filter_by(media_id=media_id).delete()

        self.db_session.delete(media)
        self.db_session.commit()
        return True

    def remove_association_from_property(self, media_id, property_id):
        """
        Remove a specific media-property association.

        Args:
            media_id (int): The media ID
            property_id (int): The property ID

        Returns:
            bool: True if removed, False if association not found
        """
        association = self.db_session.query(PropertyMedia).filter_by(
            media_id=media_id,
            property_id=property_id
        ).first()
        if not association:
            return False
        self.db_session.delete(association)
        self.db_session.commit()
        return True

    def remove_association_from_job(self, media_id, job_id):
        """
        Remove a specific media-job association.

        Args:
            media_id (int): The media ID
            job_id (int): The job ID

        Returns:
            bool: True if removed, False if association not found
        """
        association = self.db_session.query(JobMedia).filter_by(
            media_id=media_id,
            job_id=job_id
        ).first()
        if not association:
            return False
        self.db_session.delete(association)
        self.db_session.commit()
        return True

    # ========== BATCH OPERATION METHODS ==========

    def associate_media_batch_with_property(self, property_id: int, media_ids: List[int]) -> List[PropertyMedia]:
        """
        Associate multiple media items with a property.

        Args:
            property_id (int): The property ID
            media_ids (List[int]): List of media IDs to associate

        Returns:
            List[PropertyMedia]: List of created association objects
        """
        associations = []
        for media_id in media_ids:
            # Check if association already exists
            existing = self.db_session.query(PropertyMedia).filter_by(
                media_id=media_id,
                property_id=property_id
            ).first()
            if existing:
                associations.append(existing)
                continue

            association = PropertyMedia(
                media_id=media_id,
                property_id=property_id
            )
            self.db_session.add(association)
            associations.append(association)
        
        self.db_session.commit()
        # Refresh all associations to get IDs
        for assoc in associations:
            self.db_session.refresh(assoc)
        return associations

    def associate_media_batch_with_job(self, job_id: int, media_ids: List[int]) -> List[JobMedia]:
        """
        Associate multiple media items with a job.

        Args:
            job_id (int): The job ID
            media_ids (List[int]): List of media IDs to associate

        Returns:
            List[JobMedia]: List of created association objects
        """
        associations = []
        for media_id in media_ids:
            # Check if association already exists
            existing = self.db_session.query(JobMedia).filter_by(
                media_id=media_id,
                job_id=job_id
            ).first()
            if existing:
                associations.append(existing)
                continue

            association = JobMedia(
                media_id=media_id,
                job_id=job_id
            )
            self.db_session.add(association)
            associations.append(association)
        
        self.db_session.commit()
        # Refresh all associations to get IDs
        for assoc in associations:
            self.db_session.refresh(assoc)
        return associations

    def disassociate_media_batch_from_property(self, property_id: int, media_ids: List[int]) -> Dict[str, Any]:
        """
        Disassociate multiple media items from a property.

        Args:
            property_id (int): The property ID
            media_ids (List[int]): List of media IDs to disassociate

        Returns:
            Dict[str, Any]: Result with success/failure details
        """
        successful = []
        failed = []
        
        for media_id in media_ids:
            association = self.db_session.query(PropertyMedia).filter_by(
                media_id=media_id,
                property_id=property_id
            ).first()
            
            if association:
                self.db_session.delete(association)
                successful.append(media_id)
            else:
                failed.append({"id": media_id, "error": "Association not found"})
        
        self.db_session.commit()
        
        return {
            "success": len(failed) == 0,
            "successful_items": successful,
            "failed_items": failed,
            "total_processed": len(media_ids)
        }

    def disassociate_media_batch_from_job(self, job_id: int, media_ids: List[int]) -> Dict[str, Any]:
        """
        Disassociate multiple media items from a job.

        Args:
            job_id (int): The job ID
            media_ids (List[int]): List of media IDs to disassociate

        Returns:
            Dict[str, Any]: Result with success/failure details
        """
        successful = []
        failed = []
        
        for media_id in media_ids:
            association = self.db_session.query(JobMedia).filter_by(
                media_id=media_id,
                job_id=job_id
            ).first()
            
            if association:
                self.db_session.delete(association)
                successful.append(media_id)
            else:
                failed.append({"id": media_id, "error": "Association not found"})
        
        self.db_session.commit()
        
        return {
            "success": len(failed) == 0,
            "successful_items": successful,
            "failed_items": failed,
            "total_processed": len(media_ids)
        }

    def upload_and_associate_with_property(self, property_id: int, files_data: List[dict]) -> List[Media]:
        """
        Upload multiple files and associate them with a property.

        Args:
            property_id (int): The property ID
            files_data (List[dict]): List of file data dictionaries with keys:
                - 'file_name': Original filename
                - 'file_path': Storage path
                - 'media_type': Type of media
                - 'mimetype': MIME type
                - 'size_bytes': File size
                - 'description': Optional description
                - 'metadata': Optional metadata dict

        Returns:
            List[Media]: List of created Media objects
        """
        media_items = []
        for file_data in files_data:
            media = self.add_media(
                file_name=file_data.get('file_name'),
                file_path=file_data.get('file_path'),
                media_type=file_data.get('media_type'),
                mimetype=file_data.get('mimetype'),
                size_bytes=file_data.get('size_bytes'),
                description=file_data.get('description'),
                metadata=file_data.get('metadata')
            )
            media_items.append(media)
        
        # Associate all created media with the property
        media_ids = [media.id for media in media_items]
        self.associate_media_batch_with_property(property_id, media_ids)
        
        return media_items

    def upload_and_associate_with_job(self, job_id: int, files_data: List[dict]) -> List[Media]:
        """
        Upload multiple files and associate them with a job.

        Args:
            job_id (int): The job ID
            files_data (List[dict]): List of file data dictionaries with keys:
                - 'file_name': Original filename
                - 'file_path': Storage path
                - 'media_type': Type of media
                - 'mimetype': MIME type
                - 'size_bytes': File size
                - 'description': Optional description
                - 'metadata': Optional metadata dict

        Returns:
            List[Media]: List of created Media objects
        """
        media_items = []
        for file_data in files_data:
            media = self.add_media(
                file_name=file_data.get('file_name'),
                file_path=file_data.get('file_path'),
                media_type=file_data.get('media_type'),
                mimetype=file_data.get('mimetype'),
                size_bytes=file_data.get('size_bytes'),
                description=file_data.get('description'),
                metadata=file_data.get('metadata')
            )
            media_items.append(media)
        
        # Associate all created media with the job
        media_ids = [media.id for media in media_items]
        self.associate_media_batch_with_job(job_id, media_ids)
        
        return media_items

    def get_all_media(self):
        """
        Retrieve all media items.

        Returns:
            list[Media]: List of all Media objects
        """
        return self.db_session.query(Media).all()
