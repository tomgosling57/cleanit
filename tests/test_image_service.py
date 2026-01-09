import pytest
from services.image_service import ImageService, ImageNotFound
from database import Image, PropertyImage, JobImage, Property, Job


def test_add_image(image_service):
    """Test adding a new image with cleaned filename."""
    # Add image with a simple filename
    image = image_service.add_image("test.jpg", "A test image")
    assert image is not None
    assert image.id is not None
    assert image.file_name == "test.jpg"
    assert image.description == "A test image"

    # Add image with a path - should be cleaned
    image2 = image_service.add_image("/uploads/temp/test2.png", "Another test")
    assert image2.file_name == "test2.png"

    # Add image with CDN URL - should be cleaned
    image3 = image_service.add_image(
        "https://cdn.example.com/uploads/2025/01/photo.jpg?token=abc",
        "CDN image"
    )
    assert image3.file_name == "photo.jpg"


def test_get_image_by_id(image_service):
    """Test retrieving image by ID."""
    image = image_service.add_image("retrieve.jpg", "To retrieve")
    retrieved = image_service.get_image_by_id(image.id)
    assert retrieved is not None
    assert retrieved.id == image.id
    assert retrieved.file_name == "retrieve.jpg"

    # Non-existent ID
    with pytest.raises(ImageNotFound):
        image_service.get_image_by_id(9999)


def test_get_image_by_filename(image_service):
    """Test retrieving image by filename (with cleaning)."""
    image = image_service.add_image("unique.png", "Unique")
    # Retrieve with same filename
    retrieved = image_service.get_image_by_filename("unique.png")
    assert retrieved.id == image.id

    # Retrieve with path - should clean and find
    retrieved2 = image_service.get_image_by_filename("/some/path/unique.png")
    assert retrieved2.id == image.id

    # Non-existent filename
    with pytest.raises(ImageNotFound):
        image_service.get_image_by_filename("nonexistent.jpg")


def test_associate_image_with_property(image_service, seeded_test_data):
    """Test associating an image with a property."""
    property_obj = list(seeded_test_data['properties'].values())[0]
    image = image_service.add_image("prop_image.jpg", "Property image")

    association = image_service.associate_image_with_property(image.id, property_obj.id)
    assert association is not None
    assert association.image_id == image.id
    assert association.property_id == property_obj.id

    # Duplicate association should return existing
    association2 = image_service.associate_image_with_property(image.id, property_obj.id)
    assert association2.id == association.id


def test_associate_image_with_job(image_service, seeded_test_data):
    """Test associating an image with a job."""
    job = list(seeded_test_data['jobs'].values())[0]
    image = image_service.add_image("job_image.jpg", "Job image")

    association = image_service.associate_image_with_job(image.id, job.id)
    assert association is not None
    assert association.image_id == image.id
    assert association.job_id == job.id

    # Duplicate association should return existing
    association2 = image_service.associate_image_with_job(image.id, job.id)
    assert association2.id == association.id


def test_get_images_for_property(image_service, seeded_test_data):
    """Test retrieving images associated with a property."""
    property_obj = list(seeded_test_data['properties'].values())[0]
    # Initially no images
    images = image_service.get_images_for_property(property_obj.id)
    assert len(images) == 0

    # Add two images and associate them
    image1 = image_service.add_image("img1.jpg", "First")
    image2 = image_service.add_image("img2.jpg", "Second")
    image_service.associate_image_with_property(image1.id, property_obj.id)
    image_service.associate_image_with_property(image2.id, property_obj.id)

    images = image_service.get_images_for_property(property_obj.id)
    assert len(images) == 2
    image_ids = {img.id for img in images}
    assert image1.id in image_ids
    assert image2.id in image_ids


def test_get_images_for_job(image_service, seeded_test_data):
    """Test retrieving images associated with a job."""
    job = list(seeded_test_data['jobs'].values())[0]
    # Initially no images
    images = image_service.get_images_for_job(job.id)
    assert len(images) == 0

    # Add images and associate
    image1 = image_service.add_image("jobimg1.jpg", "Job image 1")
    image2 = image_service.add_image("jobimg2.jpg", "Job image 2")
    image_service.associate_image_with_job(image1.id, job.id)
    image_service.associate_image_with_job(image2.id, job.id)

    images = image_service.get_images_for_job(job.id)
    assert len(images) == 2
    image_ids = {img.id for img in images}
    assert image1.id in image_ids
    assert image2.id in image_ids


def test_update_image_description(image_service):
    """Test updating image description."""
    image = image_service.add_image("update.jpg", "Old description")
    updated = image_service.update_image_description(image.id, "New description")
    assert updated is not None
    assert updated.description == "New description"

    # Verify persistence
    retrieved = image_service.get_image_by_id(image.id)
    assert retrieved.description == "New description"

    # Update non-existent image
    with pytest.raises(ImageNotFound):
        image_service.update_image_description(9999, "Nothing")


def test_delete_image(image_service):
    """Test deleting an image and its associations."""
    image = image_service.add_image("delete.jpg", "To delete")
    image_id = image.id

    # Delete the image
    result = image_service.delete_image(image_id)
    assert result is True

    # Verify image is gone
    with pytest.raises(ImageNotFound):
        image_service.get_image_by_id(image_id)

    # Delete non-existent image
    with pytest.raises(ImageNotFound):
        image_service.delete_image(9999)


def test_delete_image_with_associations(image_service, seeded_test_data):
    """Test that deleting an image also removes its associations."""
    property_obj = list(seeded_test_data['properties'].values())[0]
    job = list(seeded_test_data['jobs'].values())[0]

    image = image_service.add_image("assoc.jpg", "With associations")
    image_service.associate_image_with_property(image.id, property_obj.id)
    image_service.associate_image_with_job(image.id, job.id)

    # Verify associations exist
    images_for_prop = image_service.get_images_for_property(property_obj.id)
    assert len(images_for_prop) == 1
    images_for_job = image_service.get_images_for_job(job.id)
    assert len(images_for_job) == 1

    # Delete image
    image_service.delete_image(image.id)

    # Associations should be removed
    images_for_prop = image_service.get_images_for_property(property_obj.id)
    assert len(images_for_prop) == 0
    images_for_job = image_service.get_images_for_job(job.id)
    assert len(images_for_job) == 0


def test_remove_association_from_property(image_service, seeded_test_data):
    """Test removing a specific image-property association."""
    property_obj = list(seeded_test_data['properties'].values())[0]
    image = image_service.add_image("remove.jpg", "Remove")
    image_service.associate_image_with_property(image.id, property_obj.id)

    # Verify association exists
    images = image_service.get_images_for_property(property_obj.id)
    assert len(images) == 1

    # Remove association
    result = image_service.remove_association_from_property(image.id, property_obj.id)
    assert result is True

    # Verify association removed
    images = image_service.get_images_for_property(property_obj.id)
    assert len(images) == 0

    # Remove non-existent association
    result = image_service.remove_association_from_property(9999, property_obj.id)
    assert result is False


def test_remove_association_from_job(image_service, seeded_test_data):
    """Test removing a specific image-job association."""
    job = list(seeded_test_data['jobs'].values())[0]
    image = image_service.add_image("remove_job.jpg", "Remove job")
    image_service.associate_image_with_job(image.id, job.id)

    # Verify association exists
    images = image_service.get_images_for_job(job.id)
    assert len(images) == 1

    # Remove association
    result = image_service.remove_association_from_job(image.id, job.id)
    assert result is True

    # Verify association removed
    images = image_service.get_images_for_job(job.id)
    assert len(images) == 0

    # Remove non-existent association
    result = image_service.remove_association_from_job(9999, job.id)
    assert result is False


def test_get_all_images(image_service):
    """Test retrieving all images."""
    # Initially there may be some images from other tests due to rollback
    # but we can still test adding and retrieving
    initial_count = len(image_service.get_all_images())

    image1 = image_service.add_image("all1.jpg", "First")
    image2 = image_service.add_image("all2.jpg", "Second")

    all_images = image_service.get_all_images()
    assert len(all_images) >= initial_count + 2
    ids = {img.id for img in all_images}
    assert image1.id in ids
    assert image2.id in ids