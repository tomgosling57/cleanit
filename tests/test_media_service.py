import pytest
from services.media_service import MediaService, MediaNotFound
from database import Media, PropertyMedia, JobMedia, Property, Job


def test_add_media(media_service):
    """Test adding a new media with cleaned filename."""
    # Add media with a simple filename
    media = media_service.add_media("test.jpg", "/uploads/test.jpg", "image", "image/jpeg", 1024, "A test image")
    assert media is not None
    assert media.id is not None
    assert media.filename == "test.jpg"
    assert media.file_path == "/uploads/test.jpg"
    assert media.media_type == "image"
    assert media.mimetype == "image/jpeg"
    assert media.size_bytes == 1024
    assert media.description == "A test image"

    # Add media with a path - should be cleaned
    media2 = media_service.add_media("/uploads/temp/test2.png", "/uploads/test2.png", "image", "image/png", 2048, "Another test")
    assert media2.filename == "test2.png"

    # Add media with CDN URL - should be cleaned
    media3 = media_service.add_media(
        "https://cdn.example.com/uploads/2025/01/photo.jpg?token=abc",
        "/uploads/photo.jpg",
        "image",
        "image/jpeg",
        3072,
        "CDN image"
    )
    assert media3.filename == "photo.jpg"


def test_get_media_by_id(media_service):
    """Test retrieving media by ID."""
    media = media_service.add_media("retrieve.jpg", "/uploads/retrieve.jpg", "image", "image/jpeg", 1024, "To retrieve")
    retrieved = media_service.get_media_by_id(media.id)
    assert retrieved is not None
    assert retrieved.id == media.id
    assert retrieved.filename == "retrieve.jpg"

    # Non-existent ID
    with pytest.raises(MediaNotFound):
        media_service.get_media_by_id(9999)


def test_get_media_by_filename(media_service):
    """Test retrieving media by filename (with cleaning)."""
    media = media_service.add_media("unique.png", "/uploads/unique.png", "image", "image/png", 1024, "Unique")
    # Retrieve with same filename
    retrieved = media_service.get_media_by_filename("unique.png")
    assert retrieved.id == media.id

    # Retrieve with path - should clean and find
    retrieved2 = media_service.get_media_by_filename("/some/path/unique.png")
    assert retrieved2.id == media.id

    # Non-existent filename
    with pytest.raises(MediaNotFound):
        media_service.get_media_by_filename("nonexistent.jpg")


def test_associate_media_with_property(media_service, seeded_test_data):
    """Test associating a media with a property."""
    property_obj = list(seeded_test_data['properties'].values())[0]
    media = media_service.add_media("prop_image.jpg", "/uploads/prop_image.jpg", "image", "image/jpeg", 1024, "Property image")

    association = media_service.associate_media_with_property(media.id, property_obj.id)
    assert association is not None
    assert association.media_id == media.id
    assert association.property_id == property_obj.id

    # Duplicate association should return existing
    association2 = media_service.associate_media_with_property(media.id, property_obj.id)
    assert association2.id == association.id


def test_associate_media_with_job(media_service, seeded_test_data):
    """Test associating a media with a job."""
    job = list(seeded_test_data['jobs'].values())[0]
    media = media_service.add_media("job_image.jpg", "/uploads/job_image.jpg", "image", "image/jpeg", 1024, "Job image")

    association = media_service.associate_media_with_job(media.id, job.id)
    assert association is not None
    assert association.media_id == media.id
    assert association.job_id == job.id

    # Duplicate association should return existing
    association2 = media_service.associate_media_with_job(media.id, job.id)
    assert association2.id == association.id


def test_get_media_for_property(media_service, seeded_test_data):
    """Test retrieving media associated with a property."""
    property_obj = list(seeded_test_data['properties'].values())[0]
    # Initially no media
    media_list = media_service.get_media_for_property(property_obj.id)
    assert len(media_list) == 0

    # Add two media and associate them
    media1 = media_service.add_media("img1.jpg", "/uploads/img1.jpg", "image", "image/jpeg", 1024, "First")
    media2 = media_service.add_media("img2.jpg", "/uploads/img2.jpg", "image", "image/jpeg", 2048, "Second")
    media_service.associate_media_with_property(media1.id, property_obj.id)
    media_service.associate_media_with_property(media2.id, property_obj.id)

    media_list = media_service.get_media_for_property(property_obj.id)
    assert len(media_list) == 2
    media_ids = {m.id for m in media_list}
    assert media1.id in media_ids
    assert media2.id in media_ids


def test_get_media_for_job(media_service, seeded_test_data):
    """Test retrieving media associated with a job."""
    job = list(seeded_test_data['jobs'].values())[0]
    # Initially no media
    media_list = media_service.get_media_for_job(job.id)
    assert len(media_list) == 0

    # Add media and associate
    media1 = media_service.add_media("jobimg1.jpg", "/uploads/jobimg1.jpg", "image", "image/jpeg", 1024, "Job image 1")
    media2 = media_service.add_media("jobimg2.jpg", "/uploads/jobimg2.jpg", "image", "image/jpeg", 2048, "Job image 2")
    media_service.associate_media_with_job(media1.id, job.id)
    media_service.associate_media_with_job(media2.id, job.id)

    media_list = media_service.get_media_for_job(job.id)
    assert len(media_list) == 2
    media_ids = {m.id for m in media_list}
    assert media1.id in media_ids
    assert media2.id in media_ids


def test_update_media_description(media_service):
    """Test updating media description."""
    media = media_service.add_media("update.jpg", "/uploads/update.jpg", "image", "image/jpeg", 1024, "Old description")
    updated = media_service.update_media_description(media.id, "New description")
    assert updated is not None
    assert updated.description == "New description"

    # Verify persistence
    retrieved = media_service.get_media_by_id(media.id)
    assert retrieved.description == "New description"

    # Update non-existent media
    with pytest.raises(MediaNotFound):
        media_service.update_media_description(9999, "Nothing")


def test_delete_media(media_service):
    """Test deleting a media and its associations."""
    media = media_service.add_media("delete.jpg", "/uploads/delete.jpg", "image", "image/jpeg", 1024, "To delete")
    media_id = media.id

    # Delete the media
    result = media_service.delete_media(media_id)
    assert result is True

    # Verify media is gone
    with pytest.raises(MediaNotFound):
        media_service.get_media_by_id(media_id)

    # Delete non-existent media
    with pytest.raises(MediaNotFound):
        media_service.delete_media(9999)


def test_delete_media_with_associations(media_service, seeded_test_data):
    """Test that deleting a media also removes its associations."""
    property_obj = list(seeded_test_data['properties'].values())[0]
    job = list(seeded_test_data['jobs'].values())[0]

    media = media_service.add_media("assoc.jpg", "/uploads/assoc.jpg", "image", "image/jpeg", 1024, "With associations")
    media_service.associate_media_with_property(media.id, property_obj.id)
    media_service.associate_media_with_job(media.id, job.id)

    # Verify associations exist
    media_for_prop = media_service.get_media_for_property(property_obj.id)
    assert len(media_for_prop) == 1
    media_for_job = media_service.get_media_for_job(job.id)
    assert len(media_for_job) == 1

    # Delete media
    media_service.delete_media(media.id)

    # Associations should be removed
    media_for_prop = media_service.get_media_for_property(property_obj.id)
    assert len(media_for_prop) == 0
    media_for_job = media_service.get_media_for_job(job.id)
    assert len(media_for_job) == 0


def test_remove_association_from_property(media_service, seeded_test_data):
    """Test removing a specific media-property association."""
    property_obj = list(seeded_test_data['properties'].values())[0]
    media = media_service.add_media("remove.jpg", "/uploads/remove.jpg", "image", "image/jpeg", 1024, "Remove")
    media_service.associate_media_with_property(media.id, property_obj.id)

    # Verify association exists
    media_list = media_service.get_media_for_property(property_obj.id)
    assert len(media_list) == 1

    # Remove association
    result = media_service.remove_association_from_property(media.id, property_obj.id)
    assert result is True

    # Verify association removed
    media_list = media_service.get_media_for_property(property_obj.id)
    assert len(media_list) == 0

    # Remove non-existent association
    result = media_service.remove_association_from_property(9999, property_obj.id)
    assert result is False


def test_remove_association_from_job(media_service, seeded_test_data):
    """Test removing a specific media-job association."""
    job = list(seeded_test_data['jobs'].values())[0]
    media = media_service.add_media("remove_job.jpg", "/uploads/remove_job.jpg", "image", "image/jpeg", 1024, "Remove job")
    media_service.associate_media_with_job(media.id, job.id)

    # Verify association exists
    media_list = media_service.get_media_for_job(job.id)
    assert len(media_list) == 1

    # Remove association
    result = media_service.remove_association_from_job(media.id, job.id)
    assert result is True

    # Verify association removed
    media_list = media_service.get_media_for_job(job.id)
    assert len(media_list) == 0

    # Remove non-existent association
    result = media_service.remove_association_from_job(9999, job.id)
    assert result is False


def test_get_all_media(media_service):
    """Test retrieving all media."""
    # Initially there may be some media from other tests due to rollback
    # but we can still test adding and retrieving
    initial_count = len(media_service.get_all_media())

    media1 = media_service.add_media("all1.jpg", "/uploads/all1.jpg", "image", "image/jpeg", 1024, "First")
    media2 = media_service.add_media("all2.jpg", "/uploads/all2.jpg", "image", "image/jpeg", 2048, "Second")

    all_media = media_service.get_all_media()
    assert len(all_media) >= initial_count + 2
    ids = {m.id for m in all_media}
    assert media1.id in ids
    assert media2.id in ids