/**
 * Media Gallery Controller - Main Entry Point
 * Combines core, DOM, and events modules
 * Global object: window.MEDIA_GALLERY
 */

(function() {
    'use strict';

    /**
     * Initialize the gallery
     * @param {Array} mediaItems - Array of media objects
     */
    function init(mediaItems = []) {
        // Cache DOM elements
        GalleryDOM.cacheElements();
        
        // Set initial media items
        GalleryCore.setItems(mediaItems);
        GalleryCore.setCurrentIndex(0);
        
        // Setup event listeners
        setupEventListeners();
        
        // Initial render
        render();
        
        console.log('MEDIA_GALLERY initialized with', GalleryCore.getItemCount(), 'items');
    }

    /**
     * Setup event listeners
     */
    function setupEventListeners() {
        // Setup DOM event listeners
        GalleryDOM.setupEventListeners({
            close: close
        });
        
        // Setup keyboard listeners
        GalleryDOM.setupKeyboardListeners({
            prev: prev,
            next: next,
            close: close
        });
    }

    /**
     * Render the current state to the UI
     */
    function render() {
        const itemCount = GalleryCore.getItemCount();
        const currentIndex = GalleryCore.getCurrentIndex();
        
        if (itemCount === 0) {
            GalleryDOM.showEmptyState();
            return;
        }

        const currentItem = GalleryCore.getCurrentItem();
        if (!currentItem) {
            GalleryDOM.showErrorState();
            return;
        }

        // Update counter
        GalleryDOM.updateCounter(currentIndex, itemCount);
        
        // Update description
        GalleryDOM.updateDescription(currentItem.description || 'No description available');
        
        // Show appropriate media element
        showMedia(currentItem);
        
        // Update thumbnails
        GalleryDOM.renderThumbnails(GalleryCore.getState().items, currentIndex, goTo);
        
        // Update button states
        GalleryDOM.updateButtonStates(currentIndex, itemCount);
        
        // Update media info
        GalleryDOM.updateMediaInfo(currentItem);
    }

    /**
     * Show the appropriate media element based on type
     * @param {Object} mediaItem
     */
    function showMedia(mediaItem) {
        // Hide all media elements first
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
     * Open gallery modal
     * @param {Array} mediaItems - Array of media objects
     */
    function open(mediaItems = []) {
        if (mediaItems && mediaItems.length > 0) {
            init(mediaItems);
        }
        
        GalleryDOM.showModal();
        GalleryCore.setOpen(true);
        
        console.log('Gallery opened with', GalleryCore.getItemCount(), 'items');
    }

    /**
     * Close gallery modal
     */
    function close() {
        GalleryDOM.hideModal();
        GalleryCore.setOpen(false);
        
        console.log('Gallery closed');
    }

    /**
     * HTMX integration helper
     * @param {string|Object} response - HTMX response data
     */
    function loadFromHTMX(response) {
        try {
            const data = typeof response === 'string' ? JSON.parse(response) : response;
            if (Array.isArray(data)) {
                open(data);
            } else if (data.media && Array.isArray(data.media)) {
                open(data.media);
            } else {
                console.error('Invalid gallery data format:', data);
            }
        } catch (error) {
            console.error('Failed to parse gallery data:', error);
        }
    }

    // Public API
    window.MEDIA_GALLERY = {
        // State (read-only access)
        get items() {
            return GalleryCore.getState().items;
        },
        get currentIndex() {
            return GalleryCore.getCurrentIndex();
        },
        
        // Core functions
        init: init,
        render: render,
        prev: prev,
        next: next,
        goTo: goTo,
        open: open,
        close: close,
        
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