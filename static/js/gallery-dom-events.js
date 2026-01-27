/**
 * Gallery DOM and Events Module
 * DOM manipulation and event handling for media gallery
 */

const GalleryDOM = (function() {
    'use strict';

    // DOM Elements cache
    const elements = {
        modal: null,
        image: null,
        video: null,
        videoSource: null,
        placeholder: null,
        description: null,
        currentIndex: null,
        totalCount: null,
        prevButton: null,
        nextButton: null,
        thumbnailContainer: null,
        thumbnailTemplate: null,
        closeButton: null,
        mediaTypeLabel: null,
        mediaDimensions: null,
        mediaDuration: null,
        downloadButton: null,
        fullscreenButton: null
    };

    /**
     * Cache DOM element references
     */
    function cacheElements() {
        elements.modal = document.getElementById('media-gallery-modal');
        elements.image = document.getElementById('gallery-image');
        elements.video = document.getElementById('gallery-video');
        elements.videoSource = elements.video ? elements.video.querySelector('source') : null;
        elements.placeholder = document.getElementById('media-placeholder');
        elements.description = document.getElementById('media-description-text');
        elements.currentIndex = document.getElementById('current-index');
        elements.totalCount = document.getElementById('total-count');
        elements.prevButton = document.querySelector('.prev-button');
        elements.nextButton = document.querySelector('.next-button');
        elements.thumbnailContainer = document.getElementById('thumbnail-container');
        elements.thumbnailTemplate = document.getElementById('thumbnail-template');
        elements.closeButton = document.querySelector('.close-button');
        elements.mediaTypeLabel = document.getElementById('media-type-label');
        elements.mediaDimensions = document.getElementById('media-dimensions');
        elements.mediaDuration = document.getElementById('media-duration');
        elements.downloadButton = document.getElementById('download-button');
        elements.fullscreenButton = document.getElementById('fullscreen-button');
    }

    /**
     * Get DOM elements
     * @returns {Object}
     */
    function getElements() {
        return elements;
    }

    /**
     * Show image media
     * @param {string} url
     */
    function showImage(url) {
        if (!elements.image) return;
        
        elements.image.src = url;
        elements.image.style.display = 'block';
        elements.image.alt = 'Gallery image';
    }

    /**
     * Show video media
     * @param {string} url
     * @param {string} mimeType
     */
    function showVideo(url, mimeType) {
        if (!elements.video || !elements.videoSource) return;
        
        // Reset video
        elements.video.pause();
        elements.video.currentTime = 0;
        
        // Update source
        elements.videoSource.src = url;
        elements.videoSource.type = mimeType;
        
        // Reload video
        elements.video.load();
        
        // Show video
        elements.video.style.display = 'block';
    }

    /**
     * Show placeholder for missing/broken media
     */
    function showPlaceholder() {
        if (!elements.placeholder) return;
        elements.placeholder.style.display = 'block';
    }

    /**
     * Hide all media elements
     */
    function hideAllMedia() {
        if (elements.image) elements.image.style.display = 'none';
        if (elements.video) {
            elements.video.style.display = 'none';
            elements.video.pause();
        }
        if (elements.placeholder) elements.placeholder.style.display = 'none';
    }

    /**
     * Update the media counter display
     * @param {number} currentIndex
     * @param {number} totalCount
     */
    function updateCounter(currentIndex, totalCount) {
        if (elements.currentIndex) {
            elements.currentIndex.textContent = currentIndex + 1;
        }
        if (elements.totalCount) {
            elements.totalCount.textContent = totalCount;
        }
    }

    /**
     * Update the description text
     * @param {string} text
     */
    function updateDescription(text) {
        if (elements.description) {
            elements.description.textContent = text;
        }
    }

    /**
     * Update button states (enable/disable)
     * @param {number} currentIndex
     * @param {number} totalCount
     */
    function updateButtonStates(currentIndex, totalCount) {
        if (elements.prevButton) {
            elements.prevButton.disabled = currentIndex === 0;
        }
        if (elements.nextButton) {
            elements.nextButton.disabled = currentIndex === totalCount - 1;
        }
    }

    /**
     * Render thumbnail strip
     * @param {Array} items
     * @param {number} currentIndex
     * @param {Function} onThumbnailClick
     */
    function renderThumbnails(items, currentIndex, onThumbnailClick) {
        if (!elements.thumbnailContainer || !elements.thumbnailTemplate) return;
        
        // Clear existing thumbnails
        elements.thumbnailContainer.innerHTML = '';
        
        // Create thumbnails for each item
        items.forEach((item, index) => {
            const thumbnail = createThumbnail(item, index, onThumbnailClick);
            if (thumbnail) {
                elements.thumbnailContainer.appendChild(thumbnail);
            }
        });
        
        // Mark active thumbnail
        markActiveThumbnail(currentIndex);
    }

    /**
     * Create a thumbnail element
     * @param {Object} item
     * @param {number} index
     * @param {Function} onClick
     * @returns {HTMLElement|null}
     */
    function createThumbnail(item, index, onClick) {
        const template = elements.thumbnailTemplate;
        if (!template) return null;
        
        const clone = template.content.cloneNode(true);
        const thumbnail = clone.querySelector('.thumbnail');
        
        if (!thumbnail) return null;
        
        // Set data attributes
        thumbnail.dataset.index = index;
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
        
        // Add click handler
        thumbnail.addEventListener('click', () => onClick(index));
        
        // Add keyboard support
        thumbnail.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                onClick(index);
            }
        });
        
        return thumbnail;
    }

    /**
     * Mark the active thumbnail
     * @param {number} currentIndex
     */
    function markActiveThumbnail(currentIndex) {
        const thumbnails = elements.thumbnailContainer.querySelectorAll('.thumbnail');
        thumbnails.forEach((thumb, index) => {
            thumb.classList.toggle('active', index === currentIndex);
            thumb.setAttribute('aria-current', index === currentIndex ? 'true' : 'false');
        });
    }

    /**
     * Update media information display
     * @param {Object} item
     */
    function updateMediaInfo(item) {
        if (!elements.mediaTypeLabel) return;
        
        const mediaType = item.media_type || GalleryCore.getMediaTypes().UNKNOWN;
        elements.mediaTypeLabel.textContent = mediaType.charAt(0).toUpperCase() + mediaType.slice(1);
        
        // Reset dimensions and duration
        if (elements.mediaDimensions) {
            elements.mediaDimensions.textContent = '-';
        }
        if (elements.mediaDuration) {
            elements.mediaDuration.style.display = 'none';
        }
    }

    /**
     * Update image info when loaded
     */
    function updateImageInfo() {
        if (!elements.image || !elements.mediaDimensions) return;
        
        const width = elements.image.naturalWidth;
        const height = elements.image.naturalHeight;
        elements.mediaDimensions.textContent = `${width}×${height}`;
    }

    /**
     * Update video info when metadata loaded
     */
    function updateVideoInfo() {
        if (!elements.video || !elements.mediaDuration) return;
        
        const duration = elements.video.duration;
        if (duration && isFinite(duration)) {
            const minutes = Math.floor(duration / 60);
            const seconds = Math.floor(duration % 60);
            elements.mediaDuration.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            elements.mediaDuration.style.display = 'inline';
        }
    }

    /**
     * Handle image loading error
     */
    function handleImageError() {
        if (!elements.image) return;
        
        console.warn('Failed to load image:', elements.image.src);
        elements.image.style.display = 'none';
        showPlaceholder();
    }

    /**
     * Handle video loading error
     */
    function handleVideoError() {
        if (!elements.video) return;
        
        console.warn('Failed to load video:', elements.videoSource?.src);
        elements.video.style.display = 'none';
        showPlaceholder();
    }

    /**
     * Show modal
     */
    function showModal() {
        if (elements.modal) {
            elements.modal.style.display = 'block';
            elements.modal.focus();
        }
    }

    /**
     * Hide modal
     */
    function hideModal() {
        if (elements.modal) {
            elements.modal.style.display = 'none';
        }
    }

    /**
     * Setup event listeners
     * @param {Object} callbacks - Object containing callback functions
     */
    function setupEventListeners(callbacks) {
        // Close modal when clicking outside content
        if (elements.modal && callbacks.close) {
            elements.modal.addEventListener('click', function(event) {
                if (event.target === elements.modal) {
                    callbacks.close();
                }
            });
        }

        // Close button
        if (elements.closeButton && callbacks.close) {
            elements.closeButton.addEventListener('click', callbacks.close);
        }

        // Video events
        if (elements.video) {
            elements.video.addEventListener('loadedmetadata', updateVideoInfo);
            elements.video.addEventListener('error', handleVideoError);
        }
        
        // Image events
        if (elements.image) {
            elements.image.addEventListener('error', handleImageError);
            elements.image.addEventListener('load', updateImageInfo);
        }
    }

    /**
     * Setup keyboard event listener
     * @param {Object} callbacks - Object containing callback functions
     */
    function setupKeyboardListeners(callbacks) {
        document.addEventListener('keydown', function(event) {
            if (!GalleryCore.isOpen()) return;
            
            switch(event.key) {
                case 'ArrowLeft':
                    event.preventDefault();
                    if (callbacks.prev) callbacks.prev();
                    break;
                case 'ArrowRight':
                    event.preventDefault();
                    if (callbacks.next) callbacks.next();
                    break;
                case 'Escape':
                    event.preventDefault();
                    if (callbacks.close) callbacks.close();
                    break;
                case ' ':
                    // Space to play/pause video
                    if (GalleryCore.getCurrentMediaType() === GalleryCore.getMediaTypes().VIDEO) {
                        event.preventDefault();
                        toggleVideoPlayback();
                    }
                    break;
            }
        });
    }

    /**
     * Toggle video playback
     */
    function toggleVideoPlayback() {
        if (!elements.video) return;
        
        if (elements.video.paused) {
            elements.video.play();
        } else {
            elements.video.pause();
        }
    }

    /**
     * Show empty state (no media items)
     */
    function showEmptyState() {
        hideAllMedia();
        showPlaceholder();
        updateDescription('No media available');
        
        if (elements.currentIndex) elements.currentIndex.textContent = '0';
        if (elements.totalCount) elements.totalCount.textContent = '0';
        
        // Disable navigation
        if (elements.prevButton) elements.prevButton.disabled = true;
        if (elements.nextButton) elements.nextButton.disabled = true;
        
        // Clear thumbnails
        if (elements.thumbnailContainer) {
            elements.thumbnailContainer.innerHTML = '';
        }
    }

    /**
     * Show error state (current item invalid)
     */
    function showErrorState() {
        hideAllMedia();
        showPlaceholder();
        updateDescription('Media could not be loaded');
    }

    // Public API
    return {
        cacheElements,
        getElements,
        showImage,
        showVideo,
        showPlaceholder,
        hideAllMedia,
        updateCounter,
        updateDescription,
        updateButtonStates,
        renderThumbnails,
        markActiveThumbnail,
        updateMediaInfo,
        showModal,
        hideModal,
        setupEventListeners,
        setupKeyboardListeners,
        showEmptyState,
        showErrorState,
        toggleVideoPlayback
    };
})();