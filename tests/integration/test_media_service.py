import pytest
from services.media_service import MediaService, MediaNotFound
from database import Media, PropertyMedia, JobMedia, Property, Job


def test_basic_media_crud(media_service):
    """Test basic CRUD operations for media."""
    # 1. Test adding media with cleaned filename
    media = media_service.add_media("test.jpg", "/uploads/test.jpg", "image", "image/jpeg", 1024, "A test image")
    assert media is not None
    assert media.id is not None
    assert media.filename == "test.jpg"
    assert media.file_path == "/uploads/test.jpg"
    assert media.media_type == "image"
    assert media.mimetype == "image/jpeg"
    assert media.size_bytes == 1024
    assert media.description == "A test image"

    # Test filename cleaning with path
    media2 = media_service.add_media("/uploads/temp/test2.png", "/uploads/test2.png", "image", "image/png", 2048, "Another test")
    assert media2.filename == "test2.png"

    # Test filename cleaning with CDN URL
    media3 = media_service.add_media(
        "https://cdn.example.com/uploads/2025/01/photo.jpg?token=abc",
        "/uploads/photo.jpg",
        "image",
        "image/jpeg",
        3072,
        "CDN image"
    )
    assert media3.filename == "photo.jpg"

    # 2. Test retrieving media by ID
    retrieved = media_service.get_media_by_id(media.id)
    assert retrieved is not None
    assert retrieved.id == media.id
    assert retrieved.filename == "test.jpg"

    # Non-existent ID
    with pytest.raises(MediaNotFound):
        media_service.get_media_by_id(9999)

    # 3. Test retrieving media by filename (with cleaning)
    retrieved_by_name = media_service.get_media_by_filename("test.jpg")
    assert retrieved_by_name.id == media.id

    # Retrieve with path - should clean and find
    retrieved_by_path = media_service.get_media_by_filename("/some/path/test.jpg")
    assert retrieved_by_path.id == media.id

    # Non-existent filename
    with pytest.raises(MediaNotFound):
        media_service.get_media_by_filename("nonexistent.jpg")

    # 4. Test updating media description
    updated = media_service.update_media_description(media.id, "New description")
    assert updated is not None
    assert updated.description == "New description"

    # Verify persistence
    retrieved_updated = media_service.get_media_by_id(media.id)
    assert retrieved_updated.description == "New description"

    # Update non-existent media
    with pytest.raises(MediaNotFound):
        media_service.update_media_description(9999, "Nothing")

    # 5. Test retrieving all media
    initial_count = len(media_service.get_all_media())
    assert initial_count >= 3  # We added at least 3 media items

    all_media = media_service.get_all_media()
    ids = {m.id for m in all_media}
    assert media.id in ids
    assert media2.id in ids
    assert media3.id in ids


def test_media_associations(media_service, seeded_test_data):
    """Test media associations with properties and jobs."""
    property_obj = list(seeded_test_data['properties'].values())[0]
    job = list(seeded_test_data['jobs'].values())[0]
    
    # Create test media
    media = media_service.add_media("assoc_test.jpg", "/uploads/assoc_test.jpg", "image", "image/jpeg", 1024, "Association test")
    
    # Test property association
    prop_assoc = media_service.associate_media_with_property(media.id, property_obj.id)
    assert prop_assoc is not None
    assert prop_assoc.media_id == media.id
    assert prop_assoc.property_id == property_obj.id
    
    # Test job association
    job_assoc = media_service.associate_media_with_job(media.id, job.id)
    assert job_assoc is not None
    assert job_assoc.media_id == media.id
    assert job_assoc.job_id == job.id
    
    # Test duplicate associations return existing
    prop_assoc2 = media_service.associate_media_with_property(media.id, property_obj.id)
    assert prop_assoc2.id == prop_assoc.id
    job_assoc2 = media_service.associate_media_with_job(media.id, job.id)
    assert job_assoc2.id == job_assoc.id
    
    # Test retrieving media for property
    prop_media = media_service.get_media_for_property(property_obj.id)
    assert len(prop_media) == 1
    assert prop_media[0].id == media.id
    
    # Test retrieving media for job
    job_media = media_service.get_media_for_job(job.id)
    assert len(job_media) == 1
    assert job_media[0].id == media.id
    
    # Test removing associations
    prop_removed = media_service.remove_association_from_property(media.id, property_obj.id)
    assert prop_removed is True
    assert len(media_service.get_media_for_property(property_obj.id)) == 0
    
    job_removed = media_service.remove_association_from_job(media.id, job.id)
    assert job_removed is True
    assert len(media_service.get_media_for_job(job.id)) == 0
    
    # Test removing non-existent associations
    assert media_service.remove_association_from_property(9999, property_obj.id) is False
    assert media_service.remove_association_from_job(9999, job.id) is False


def test_media_deletion(media_service, seeded_test_data):
    """Test deleting media and its associations."""
    property_obj = list(seeded_test_data['properties'].values())[0]
    job = list(seeded_test_data['jobs'].values())[0]
    
    # Create media with associations
    media = media_service.add_media("delete_test.jpg", "/uploads/delete_test.jpg", "image", "image/jpeg", 1024, "Delete test")
    media_service.associate_media_with_property(media.id, property_obj.id)
    media_service.associate_media_with_job(media.id, job.id)
    
    # Verify associations exist
    assert len(media_service.get_media_for_property(property_obj.id)) == 1
    assert len(media_service.get_media_for_job(job.id)) == 1
    
    # Delete the media
    result = media_service.delete_media(media.id)
    assert result is True
    
    # Verify media is gone
    with pytest.raises(MediaNotFound):
        media_service.get_media_by_id(media.id)
    
    # Verify associations are removed
    assert len(media_service.get_media_for_property(property_obj.id)) == 0
    assert len(media_service.get_media_for_job(job.id)) == 0
    
    # Delete non-existent media
    with pytest.raises(MediaNotFound):
        media_service.delete_media(9999)


@pytest.mark.parametrize("association_type,fixture_key", [
    ("property", "properties"),
    ("job", "jobs")
])
def test_batch_operations(media_service, seeded_test_data, association_type, fixture_key):
    """Test batch association, disassociation, and upload operations."""
    target_obj = list(seeded_test_data[fixture_key].values())[0]
    
    # Create multiple media items
    media1 = media_service.add_media(f"batch1.jpg", f"/uploads/batch1.jpg", "image", "image/jpeg", 1024, "Batch 1")
    media2 = media_service.add_media(f"batch2.jpg", f"/uploads/batch2.jpg", "image", "image/jpeg", 2048, "Batch 2")
    media3 = media_service.add_media(f"batch3.jpg", f"/uploads/batch3.jpg", "image", "image/jpeg", 3072, "Batch 3")
    
    media_ids = [media1.id, media2.id, media3.id]
    
    # Test batch association
    if association_type == "property":
        associations = media_service.associate_media_batch_with_property(target_obj.id, media_ids)
    else:
        associations = media_service.associate_media_batch_with_job(target_obj.id, media_ids)
    
    assert len(associations) == 3
    for assoc in associations:
        if association_type == "property":
            assert assoc.property_id == target_obj.id
        else:
            assert assoc.job_id == target_obj.id
        assert assoc.media_id in media_ids
    
    # Verify associations exist
    if association_type == "property":
        media_list = media_service.get_media_for_property(target_obj.id)
    else:
        media_list = media_service.get_media_for_job(target_obj.id)
    assert len(media_list) == 3
    
    # Test duplicate batch association (should return existing)
    if association_type == "property":
        associations2 = media_service.associate_media_batch_with_property(target_obj.id, [media1.id])
    else:
        associations2 = media_service.associate_media_batch_with_job(target_obj.id, [media1.id])
    assert len(associations2) == 1
    assert associations2[0].media_id == media1.id
    
    # Test batch disassociation
    if association_type == "property":
        result = media_service.disassociate_media_batch_from_property(target_obj.id, [media1.id, media2.id])
    else:
        result = media_service.disassociate_media_batch_from_job(target_obj.id, [media1.id, media2.id])
    
    assert result["success"] is True
    assert result["successful_items"] == [media1.id, media2.id]
    assert result["failed_items"] == []
    assert result["total_processed"] == 2
    
    # Verify remaining associations
    if association_type == "property":
        media_list = media_service.get_media_for_property(target_obj.id)
    else:
        media_list = media_service.get_media_for_job(target_obj.id)
    assert len(media_list) == 1
    assert media_list[0].id == media3.id
    
    # Test disassociating non-existent association
    if association_type == "property":
        result = media_service.disassociate_media_batch_from_property(target_obj.id, [9999])
    else:
        result = media_service.disassociate_media_batch_from_job(target_obj.id, [9999])
    assert result["success"] is False
    assert result["failed_items"][0]["id"] == 9999
    assert result["failed_items"][0]["error"] == "Association not found"
    
    # Test upload and associate
    files_data = [
        {
            'file_name': f'upload1.jpg',
            'file_path': f'/uploads/upload1.jpg',
            'media_type': 'image',
            'mimetype': 'image/jpeg',
            'size_bytes': 1024,
            'description': 'First upload',
            'metadata': {'width': 800, 'height': 600}
        },
        {
            'file_name': f'upload2.png',
            'file_path': f'/uploads/upload2.png',
            'media_type': 'image',
            'mimetype': 'image/png',
            'size_bytes': 2048,
            'description': 'Second upload',
            'metadata': {'width': 1024, 'height': 768}
        }
    ]
    
    if association_type == "property":
        media_items = media_service.upload_and_associate_with_property(target_obj.id, files_data)
    else:
        media_items = media_service.upload_and_associate_with_job(target_obj.id, files_data)
    
    assert len(media_items) == 2
    assert media_items[0].filename == 'upload1.jpg'
    assert media_items[1].filename == 'upload2.png'
    
    # Verify new associations
    if association_type == "property":
        media_list = media_service.get_media_for_property(target_obj.id)
    else:
        media_list = media_service.get_media_for_job(target_obj.id)
    # Should have media3 + 2 new uploads = 3 total
    assert len(media_list) == 3


def test_empty_batch_operations(media_service, seeded_test_data):
    """Test batch operations with empty lists."""
    property_obj = list(seeded_test_data['properties'].values())[0]
    job = list(seeded_test_data['jobs'].values())[0]
    
    # Empty association
    associations = media_service.associate_media_batch_with_property(property_obj.id, [])
    assert associations == []
    
    # Empty disassociation
    result = media_service.disassociate_media_batch_from_job(job.id, [])
    assert result["success"] is True
    assert result["successful_items"] == []
    assert result["failed_items"] == []
    assert result["total_processed"] == 0
    
    # Empty upload and associate
    media_items = media_service.upload_and_associate_with_property(property_obj.id, [])
    assert media_items == []
