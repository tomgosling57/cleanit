/**
 * Enhanced Media Gallery Controller
 * Updated for new job/property gallery endpoints with batch operations
 * Global object: window.ENHANCED_GALLERY
 */

(function() {
    'use strict';

    // Configuration
    const config = {
        endpoints: {
            job: '/jobs/{id}/media',
            property: '/address-book/property/{id}/media'
        },
        batchOperations: {
            maxFiles: 50,
            allowedTypes: ['image/jpeg', 'image/png', 'image/gif', 'video/mp4', 'video/webm']
        }
    };

    // State
    let currentEntity = null; // {type: 'job'|'property', id: number}
    let isEditMode = false;
    let selectedMediaIds = new Set();

    /**
     * Initialize the enhanced gallery
     * @param {Array} mediaItems - Array of media objects
     * @param {Object} entity - Entity info {type: 'job'|'property', id: number}
     */
    function init(mediaItems = [], entity = null) {
        // Cache DOM elements
        cacheElements();
        
        // Set entity context
        if (entity) {
            currentEntity = entity;
            updateEntityInfo();
        }
        
        // Set initial media items
        GalleryCore.setItems(mediaItems);
        GalleryCore.setCurrentIndex(0);
        
        // Setup event listeners
        setupEventListeners();
        
        // Initial render
        render();
        
        console.log('ENHANCED_GALLERY initialized for', currentEntity?.type, currentEntity?.id, 'with', GalleryCore.getItemCount(), 'items');
    }

    /**
     * Cache DOM element references
     */
    function cacheElements() {
        // Use existing gallery elements
        GalleryDOM.cacheElements();
        
        // Get DOM elements from GalleryDOM module
        const domElements = GalleryDOM.getElements();
        
        // Enhanced gallery specific elements
        elements.editToggle = document.getElementById('gallery-edit-toggle');
        elements.batchDeleteButton = document.getElementById('batch-delete-button');
        elements.batchUploadButton = document.getElementById('batch-upload-button');
        elements.fileInput = document.getElementById('gallery-file-input');
        elements.entityInfo = document.getElementById('gallery-entity-info');
        elements.selectedCount = document.getElementById('selected-count');
        elements.mediaCheckboxes = null; // Will be populated during render
        
        // Copy essential DOM elements from GalleryDOM
        elements.thumbnailContainer = domElements.thumbnailContainer;
        elements.thumbnailTemplate = domElements.thumbnailTemplate;
        
        console.debug('ENHANCED_GALLERY: Cached elements:', {
            hasThumbnailContainer: !!elements.thumbnailContainer,
            hasThumbnailTemplate: !!elements.thumbnailTemplate,
            thumbnailContainerId: elements.thumbnailContainer?.id,
            thumbnailTemplateId: elements.thumbnailTemplate?.id
        });
    }

    const elements = {};

    /**
     * Update entity information display
     */
    function updateEntityInfo() {
        if (!elements.entityInfo || !currentEntity) return;
        
        const typeLabel = currentEntity.type === 'job' ? 'Job' : 'Property';
        elements.entityInfo.textContent = `${typeLabel} #${currentEntity.id} Gallery`;
    }

    /**
     * Setup event listeners
     */
    function setupEventListeners() {
        // Setup DOM event listeners from base gallery
        GalleryDOM.setupEventListeners({
            close: close
        });
        
        // Setup keyboard listeners
        GalleryDOM.setupKeyboardListeners({
            prev: prev,
            next: next,
            close: close
        });

        // Enhanced gallery listeners
        if (elements.editToggle) {
            elements.editToggle.addEventListener('click', toggleEditMode);
        }
        
        if (elements.batchDeleteButton) {
            elements.batchDeleteButton.addEventListener('click', handleBatchDelete);
        }
        
        if (elements.batchUploadButton) {
            elements.batchUploadButton.addEventListener('click', triggerFileUpload);
        }
        
        if (elements.fileInput) {
            elements.fileInput.addEventListener('change', handleFileUpload);
        }
    }

    /**
     * Render the current state to the UI
     */
    function render() {
        console.debug('ENHANCED_GALLERY: render called');
        const itemCount = GalleryCore.getItemCount();
        const currentIndex = GalleryCore.getCurrentIndex();
        
        console.debug('ENHANCED_GALLERY: itemCount:', itemCount, 'currentIndex:', currentIndex);
        
        if (itemCount === 0) {
            console.debug('ENHANCED_GALLERY: No items, showing empty state');
            GalleryDOM.showEmptyState();
            updateEditModeUI();
            return;
        }

        const currentItem = GalleryCore.getCurrentItem();
        if (!currentItem) {
            console.error('ENHANCED_GALLERY: Current item is null');
            GalleryDOM.showErrorState();
            return;
        }

        console.debug('ENHANCED_GALLERY: Current item:', currentItem);
        
        // Update counter
        GalleryDOM.updateCounter(currentIndex, itemCount);
        
        // Update description
        GalleryDOM.updateDescription(currentItem.description || 'No description available');
        
        // Show appropriate media element
        showMedia(currentItem);
        
        // Update thumbnails with enhanced functionality
        console.debug('ENHANCED_GALLERY: Calling renderEnhancedThumbnails');
        renderEnhancedThumbnails(GalleryCore.getState().items, currentIndex);
        
        // Update button states
        GalleryDOM.updateButtonStates(currentIndex, itemCount);
        
        // Update media info
        GalleryDOM.updateMediaInfo(currentItem);
        
        // Update edit mode UI
        updateEditModeUI();
        
        console.debug('ENHANCED_GALLERY: Render completed');
    }

    /**
     * Render enhanced thumbnails with selection checkboxes
     * @param {Array} items
     * @param {number} currentIndex
     */
    function renderEnhancedThumbnails(items, currentIndex) {
        console.debug('ENHANCED_GALLERY: renderEnhancedThumbnails called with', items.length, 'items');
        console.debug('ENHANCED_GALLERY: elements.thumbnailContainer:', elements.thumbnailContainer);
        console.debug('ENHANCED_GALLERY: elements.thumbnailTemplate:', elements.thumbnailTemplate);
        
        if (!elements.thumbnailContainer || !elements.thumbnailTemplate) {
            console.error('ENHANCED_GALLERY: Missing required DOM elements for thumbnails');
            console.error('ENHANCED_GALLERY: thumbnailContainer:', elements.thumbnailContainer);
            console.error('ENHANCED_GALLERY: thumbnailTemplate:', elements.thumbnailTemplate);
            return;
        }
        
        // Clear existing thumbnails
        elements.thumbnailContainer.innerHTML = '';
        
        console.debug('ENHANCED_GALLERY: Creating thumbnails for', items.length, 'items');
        
        // Create thumbnails for each item
        items.forEach((item, index) => {
            const thumbnail = createEnhancedThumbnail(item, index);
            if (thumbnail) {
                elements.thumbnailContainer.appendChild(thumbnail);
            }
        });
        
        console.debug('ENHANCED_GALLERY: Created', elements.thumbnailContainer.children.length, 'thumbnails');
        
        // Mark active thumbnail
        GalleryDOM.markActiveThumbnail(currentIndex);
    }

    /**
     * Create enhanced thumbnail with selection checkbox
     * @param {Object} item
     * @param {number} index
     * @returns {HTMLElement|null}
     */
    function createEnhancedThumbnail(item, index) {
        const template = elements.thumbnailTemplate;
        if (!template) return null;
        
        const clone = template.content.cloneNode(true);
        const thumbnail = clone.querySelector('.thumbnail');
        
        if (!thumbnail) return null;
        
        // Set data attributes
        thumbnail.dataset.index = index;
        thumbnail.dataset.mediaId = item.id;
        thumbnail.setAttribute('aria-label', `Thumbnail ${index + 1}`);
        
        // Set thumbnail image
        const img = thumbnail.querySelector('.thumbnail-image');
        if (img) {
            const placeholders = GalleryCore.getPlaceholders();
            img.src = item.thumbnail_url || item.url || placeholders.unknown;
            img.alt = `Thumbnail for ${item.description || 'media'}`;
        }
        
        // Set type icon
        const icon = thumbnail.querySelector('.thumbnail-type-icon');
        if (icon) {
            const mediaTypes = GalleryCore.getMediaTypes();
            icon.textContent = item.media_type === mediaTypes.VIDEO ? '▶' : '🖼️';
        }
        
        // Add selection checkbox in edit mode
        if (isEditMode) {
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'media-checkbox';
            checkbox.dataset.mediaId = item.id;
            checkbox.checked = selectedMediaIds.has(item.id);
            checkbox.addEventListener('change', handleMediaSelection);
            
            const checkboxContainer = document.createElement('div');
            checkboxContainer.className = 'thumbnail-checkbox';
            checkboxContainer.appendChild(checkbox);
            thumbnail.appendChild(checkboxContainer);
        }
        
        // Add click handler for navigation
        thumbnail.addEventListener('click', (event) => {
            // Don't navigate if clicking checkbox
            if (event.target.type === 'checkbox') return;
            goTo(index);
        });
        
        // Add keyboard support
        thumbnail.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                goTo(index);
            }
        });
        
        return thumbnail;
    }

    /**
     * Show the appropriate media element based on type
     * @param {Object} mediaItem
     */
    function showMedia(mediaItem) {
        // Use base gallery functionality
        GalleryDOM.hideAllMedia();
        
        const mediaType = mediaItem.media_type || GalleryCore.getMediaTypes().UNKNOWN;
        const mediaUrl = mediaItem.url || '';
        
        switch(mediaType.toLowerCase()) {
            case GalleryCore.getMediaTypes().IMAGE:
                GalleryDOM.showImage(mediaUrl);
                break;
            case GalleryCore.getMediaTypes().VIDEO:
                GalleryDOM.showVideo(mediaUrl, mediaItem.mimetype || 'video/mp4');
                break;
            default:
                GalleryDOM.showPlaceholder();
                break;
        }
    }

    /**
     * Navigate to previous item
     */
    function prev() {
        if (GalleryCore.prev()) {
            render();
        }
    }

    /**
     * Navigate to next item
     */
    function next() {
        if (GalleryCore.next()) {
            render();
        }
    }

    /**
     * Navigate to specific index
     * @param {number} index
     */
    function goTo(index) {
        if (GalleryCore.goTo(index)) {
            render();
        }
    }

    /**
     * Open gallery modal for specific entity
     * @param {Object} entity - {type: 'job'|'property', id: number}
     * @param {Array} mediaItems - Optional pre-loaded media items
     */
    function open(entity, mediaItems = null) {
        if (!entity || !entity.type || !entity.id) {
            console.error('Invalid entity provided to open gallery:', entity);
            return;
        }
        
        currentEntity = entity;
        
        if (mediaItems && mediaItems.length > 0) {
            init(mediaItems, entity);
        } else {
            // Fetch media from server
            fetchEntityMedia(entity);
        }
        
        GalleryDOM.showModal();
        GalleryCore.setOpen(true);
        
        console.log('Gallery opened for', entity.type, entity.id);
    }

    /**
     * Fetch media for entity from server
     * @param {Object} entity
     */
    async function fetchEntityMedia(entity) {
        if (!entity || !entity.type || !entity.id) return;
        
        const endpoint = config.endpoints[entity.type].replace('{id}', entity.id);
        
        try {
            const response = await fetch(endpoint);
            if (!response.ok) {
                throw new Error(`Failed to fetch media: ${response.status}`);
            }
            
            const data = await response.json();
            if (data.success && Array.isArray(data.media)) {
                init(data.media, entity);
            } else {
                console.error('Invalid response format:', data);
                init([], entity);
            }
        } catch (error) {
            console.error('Error fetching media:', error);
            init([], entity);
        }
    }

    /**
     * Close gallery modal
     */
    function close() {
        GalleryDOM.hideModal();
        GalleryCore.setOpen(false);
        currentEntity = null;
        isEditMode = false;
        selectedMediaIds.clear();
        
        console.log('Gallery closed');
    }

    /**
     * Toggle edit mode
     */
    function toggleEditMode() {
        isEditMode = !isEditMode;
        selectedMediaIds.clear();
        render();
    }

    /**
     * Update edit mode UI
     */
    function updateEditModeUI() {
        if (!elements.editToggle || !elements.batchDeleteButton || !elements.batchUploadButton) return;
        
        // Update edit toggle button
        elements.editToggle.textContent = isEditMode ? 'View Mode' : 'Edit Mode';
        elements.editToggle.classList.toggle('active', isEditMode);
        
        // Show/hide batch buttons
        elements.batchDeleteButton.style.display = isEditMode ? 'block' : 'none';
        elements.batchUploadButton.style.display = isEditMode ? 'block' : 'none';
        
        // Update selected count
        if (elements.selectedCount) {
            elements.selectedCount.textContent = selectedMediaIds.size;
            elements.selectedCount.style.display = selectedMediaIds.size > 0 ? 'inline' : 'none';
        }
        
        // Update batch delete button state
        if (elements.batchDeleteButton) {
            elements.batchDeleteButton.disabled = selectedMediaIds.size === 0;
        }
    }

    /**
     * Handle media selection checkbox change
     * @param {Event} event
     */
    function handleMediaSelection(event) {
        const mediaId = parseInt(event.target.dataset.mediaId);
        if (isNaN(mediaId)) return;
        
        if (event.target.checked) {
            selectedMediaIds.add(mediaId);
        } else {
            selectedMediaIds.delete(mediaId);
        }
        
        updateEditModeUI();
    }

    /**
     * Handle batch delete
     */
    async function handleBatchDelete() {
        if (!currentEntity || selectedMediaIds.size === 0) return;
        
        if (!confirm(`Delete ${selectedMediaIds.size} selected media item(s)? This action cannot be undone.`)) {
            return;
        }
        
        const endpoint = config.endpoints[currentEntity.type].replace('{id}', currentEntity.id);
        const mediaIds = Array.from(selectedMediaIds);
        
        try {
            const response = await fetch(endpoint, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ media_ids: mediaIds })
            });
            
            if (!response.ok) {
                throw new Error(`Delete failed: ${response.status}`);
            }
            
            const data = await response.json();
            if (data.success) {
                // Refresh gallery
                fetchEntityMedia(currentEntity);
                selectedMediaIds.clear();
            } else {
                alert('Failed to delete media: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error deleting media:', error);
            alert('Error deleting media. Please try again.');
        }
    }

    /**
     * Trigger file upload dialog
     */
    function triggerFileUpload() {
        if (elements.fileInput) {
            elements.fileInput.click();
        }
    }

    /**
     * Handle file upload
     * @param {Event} event
     */
    async function handleFileUpload(event) {
        const files = Array.from(event.target.files);
        if (files.length === 0 || !currentEntity) return;
        
        // Validate files
        const validFiles = files.filter(file => 
            config.batchOperations.allowedTypes.includes(file.type) &&
            file.size <= 100 * 1024 * 1024 // 100MB limit
        );
        
        if (validFiles.length === 0) {
            alert('No valid files selected. Supported types: JPEG, PNG, GIF, MP4, WebM. Max size: 100MB.');
            return;
        }
        
        if (validFiles.length > config.batchOperations.maxFiles) {
            alert(`Too many files. Maximum ${config.batchOperations.maxFiles} files allowed.`);
            return;
        }
        
        // Create form data
        const formData = new FormData();
        validFiles.forEach((file, index) => {
            formData.append('files[]', file);
            formData.append('descriptions[]', file.name);
        });
        
        const endpoint = config.endpoints[currentEntity.type].replace('{id}', currentEntity.id);
        
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken()
                },
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`Upload failed: ${response.status}`);
            }
            
            const data = await response.json();
            if (data.success) {
                // Refresh gallery
                fetchEntityMedia(currentEntity);
                alert(`Successfully uploaded ${validFiles.length} file(s)`);
            } else {
                alert('Upload failed: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error uploading files:', error);
            alert('Error uploading files. Please try again.');
        }
        
        // Reset file input
        event.target.value = '';
    }

    /**
     * Get CSRF token from page
     * @returns {string}
     */
    function getCSRFToken() {
        return document.querySelector('meta[name="csrf-token"]')?.content ||
               document.body.dataset.csrfToken ||
               '';
    }

    /**
     * HTMX integration helper
     * @param {string|Object} response - HTMX response data
     */
    function loadFromHTMX(response) {
        try {
            const data = typeof response === 'string' ? JSON.parse(response) : response;
            if (Array.isArray(data)) {
                open({ type: 'unknown', id: 0 }, data);
            } else if (data.media && Array.isArray(data.media)) {
                open({ type: 'unknown', id: 0 }, data.media);
            } else {
                console.error('Invalid gallery data format:', data);
            }
        } catch (error) {
            console.error('Failed to parse gallery data:', error);
        }
    }

    // Public API
    window.ENHANCED_GALLERY = {
        // State (read-only access)
        get items() {
            return GalleryCore.getState().items;
        },
        get currentIndex() {
            return GalleryCore.getCurrentIndex();
        },
        get currentEntity() {
            return currentEntity;
        },
        get isEditMode() {
            return isEditMode;
        },
        get selectedCount() {
            return selectedMediaIds.size;
        },
        
        // Core functions
        init: init,
        render: render,
        prev: prev,
        next: next,
        goTo: goTo,
        open: open,
        close: close,
        
        // Enhanced functions
        toggleEditMode: toggleEditMode,
        handleBatchDelete: handleBatchDelete,
        triggerFileUpload: triggerFileUpload,
        
        // Utility functions
        getCurrentItem: GalleryCore.getCurrentItem,
        getItemCount: GalleryCore.getItemCount,
        isOpen: GalleryCore.isOpen,
        
        // HTMX integration
        loadFromHTMX: loadFromHTMX
    };

    // Auto-initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            init();
        });
    } else {
        init();
    }

})();
