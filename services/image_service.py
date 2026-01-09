from database import Image, PropertyImage, JobImage
import os
from werkzeug.utils import secure_filename


class ImageNotFound(Exception):
    """Exception raised when an image is not found."""
    pass


class ImageService:
    """
    Service layer for image-related operations.
    Handles CRUD for images and their associations with properties and jobs.
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

    def add_image(self, file_name, description=None):
        """
        Create a new image record in the database.

        Args:
            file_name (str): The filename (will be cleaned of CDN/temp paths)
            description (str, optional): Description of the image

        Returns:
            Image: The created Image object
        """
        cleaned_file_name = self._clean_filename(file_name)
        # Ensure uniqueness? The database column has unique constraint
        new_image = Image(
            file_name=cleaned_file_name,
            description=description
        )
        self.db_session.add(new_image)
        self.db_session.commit()
        self.db_session.refresh(new_image)
        return new_image

    def get_image_by_id(self, image_id):
        """
        Retrieve an image by its ID.

        Args:
            image_id (int): The image ID

        Returns:
            Image: The Image object if found

        Raises:
            ImageNotFound: If no image with the given ID exists
        """
        image = self.db_session.query(Image).filter_by(id=image_id).first()
        if not image:
            raise ImageNotFound(f"Image with ID {image_id} not found")
        return image

    def get_image_by_filename(self, file_name):
        """
        Retrieve an image by its filename (after cleaning).

        Args:
            file_name (str): The filename

        Returns:
            Image: The Image object if found

        Raises:
            ImageNotFound: If no image with the given filename exists
        """
        cleaned = self._clean_filename(file_name)
        image = self.db_session.query(Image).filter_by(file_name=cleaned).first()
        if not image:
            raise ImageNotFound(f"Image with filename '{file_name}' (cleaned: '{cleaned}') not found")
        return image

    def associate_image_with_property(self, image_id, property_id):
        """
        Create an association between an image and a property.

        Args:
            image_id (int): The image ID
            property_id (int): The property ID

        Returns:
            PropertyImage: The created association object
        """
        # Check if association already exists
        existing = self.db_session.query(PropertyImage).filter_by(
            image_id=image_id,
            property_id=property_id
        ).first()
        if existing:
            return existing

        association = PropertyImage(
            image_id=image_id,
            property_id=property_id
        )
        self.db_session.add(association)
        self.db_session.commit()
        self.db_session.refresh(association)
        return association

    def associate_image_with_job(self, image_id, job_id):
        """
        Create an association between an image and a job.

        Args:
            image_id (int): The image ID
            job_id (int): The job ID

        Returns:
            JobImage: The created association object
        """
        existing = self.db_session.query(JobImage).filter_by(
            image_id=image_id,
            job_id=job_id
        ).first()
        if existing:
            return existing

        association = JobImage(
            image_id=image_id,
            job_id=job_id
        )
        self.db_session.add(association)
        self.db_session.commit()
        self.db_session.refresh(association)
        return association

    def get_images_for_property(self, property_id):
        """
        Retrieve all images associated with a property.

        Args:
            property_id (int): The property ID

        Returns:
            list[Image]: List of Image objects
        """
        associations = self.db_session.query(PropertyImage).filter_by(
            property_id=property_id
        ).all()
        image_ids = [assoc.image_id for assoc in associations]
        if not image_ids:
            return []
        return self.db_session.query(Image).filter(Image.id.in_(image_ids)).all()

    def get_images_for_job(self, job_id):
        """
        Retrieve all images associated with a job.

        Args:
            job_id (int): The job ID

        Returns:
            list[Image]: List of Image objects
        """
        associations = self.db_session.query(JobImage).filter_by(
            job_id=job_id
        ).all()
        image_ids = [assoc.image_id for assoc in associations]
        if not image_ids:
            return []
        return self.db_session.query(Image).filter(Image.id.in_(image_ids)).all()

    def update_image_description(self, image_id, description):
        """
        Update the description of an image.

        Args:
            image_id (int): The image ID
            description (str): New description

        Returns:
            Image: Updated Image object

        Raises:
            ImageNotFound: If no image with the given ID exists
        """
        image = self.get_image_by_id(image_id)
        image.description = description
        self.db_session.commit()
        self.db_session.refresh(image)
        return image

    def delete_image(self, image_id):
        """
        Delete an image and all its associations.

        Args:
            image_id (int): The image ID

        Returns:
            bool: True if deleted

        Raises:
            ImageNotFound: If no image with the given ID exists
        """
        image = self.get_image_by_id(image_id)

        # Delete property associations
        self.db_session.query(PropertyImage).filter_by(image_id=image_id).delete()
        # Delete job associations
        self.db_session.query(JobImage).filter_by(image_id=image_id).delete()

        self.db_session.delete(image)
        self.db_session.commit()
        return True

    def remove_association_from_property(self, image_id, property_id):
        """
        Remove a specific image-property association.

        Args:
            image_id (int): The image ID
            property_id (int): The property ID

        Returns:
            bool: True if removed, False if association not found
        """
        association = self.db_session.query(PropertyImage).filter_by(
            image_id=image_id,
            property_id=property_id
        ).first()
        if not association:
            return False
        self.db_session.delete(association)
        self.db_session.commit()
        return True

    def remove_association_from_job(self, image_id, job_id):
        """
        Remove a specific image-job association.

        Args:
            image_id (int): The image ID
            job_id (int): The job ID

        Returns:
            bool: True if removed, False if association not found
        """
        association = self.db_session.query(JobImage).filter_by(
            image_id=image_id,
            job_id=job_id
        ).first()
        if not association:
            return False
        self.db_session.delete(association)
        self.db_session.commit()
        return True

    def get_all_images(self):
        """
        Retrieve all images.

        Returns:
            list[Image]: List of all Image objects
        """
        return self.db_session.query(Image).all()