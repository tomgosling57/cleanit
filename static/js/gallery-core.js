/**
 * Gallery Core Module
 * State management and core logic for media gallery
 */

const GalleryCore = (function() {
    'use strict';

    // Constants
    const MEDIA_TYPES = {
        IMAGE: 'image',
        VIDEO: 'video',
        UNKNOWN: 'unknown'
    };

    // Placeholder URLs
    const PLACEHOLDERS = {
        image: '/static/images/placeholders/image-not-found.png',
        video: '/static/images/placeholders/image-not-found.png',
        unknown: '/static/images/placeholders/image-not-found.png'
    };

    // State
    const state = {
        items: [],
        currentIndex: 0,
        isOpen: false,
        keyboardEnabled: false
    };

    /**
     * Get current media type
     * @returns {string}
     */
    function getCurrentMediaType() {
        const currentItem = state.items[state.currentIndex];
        if (!currentItem) return MEDIA_TYPES.UNKNOWN;
        return (currentItem.media_type || MEDIA_TYPES.UNKNOWN).toLowerCase();
    }

    /**
     * Get current item
     * @returns {Object|null}
     */
    function getCurrentItem() {
        return state.items[state.currentIndex] || null;
    }

    /**
     * Get item count
     * @returns {number}
     */
    function getItemCount() {
        return state.items.length;
    }

    /**
     * Check if gallery is open
     * @returns {boolean}
     */
    function isOpen() {
        return state.isOpen;
    }

    /**
     * Set gallery open state
     * @param {boolean} open
     */
    function setOpen(open) {
        state.isOpen = open;
    }

    /**
     * Set media items
     * @param {Array} items
     */
    function setItems(items) {
        state.items = Array.isArray(items) ? items : [];
    }

    /**
     * Set current index
     * @param {number} index
     */
    function setCurrentIndex(index) {
        if (index >= 0 && index < state.items.length) {
            state.currentIndex = index;
        }
    }

    /**
     * Get current index
     * @returns {number}
     */
    function getCurrentIndex() {
        return state.currentIndex;
    }

    /**
     * Navigate to previous item
     * @returns {boolean} True if navigation occurred
     */
    function prev() {
        if (state.currentIndex > 0) {
            state.currentIndex--;
            return true;
        }
        return false;
    }

    /**
     * Navigate to next item
     * @returns {boolean} True if navigation occurred
     */
    function next() {
        if (state.currentIndex < state.items.length - 1) {
            state.currentIndex++;
            return true;
        }
        return false;
    }

    /**
     * Navigate to specific index
     * @param {number} index
     * @returns {boolean} True if navigation occurred
     */
    function goTo(index) {
        if (index >= 0 && index < state.items.length) {
            state.currentIndex = index;
            return true;
        }
        return false;
    }

    /**
     * Get media type constants
     * @returns {Object}
     */
    function getMediaTypes() {
        return MEDIA_TYPES;
    }

    /**
     * Get placeholder URLs
     * @returns {Object}
     */
    function getPlaceholders() {
        return PLACEHOLDERS;
    }

    /**
     * Get state (for debugging)
     * @returns {Object}
     */
    function getState() {
        return { ...state };
    }

    /**
     * Reset state
     */
    function reset() {
        state.items = [];
        state.currentIndex = 0;
        state.isOpen = false;
        state.keyboardEnabled = false;
    }

    // Public API
    return {
        // State getters/setters
        getCurrentMediaType,
        getCurrentItem,
        getItemCount,
        isOpen,
        setOpen,
        setItems,
        setCurrentIndex,
        getCurrentIndex,
        
        // Navigation
        prev,
        next,
        goTo,
        
        // Constants
        getMediaTypes,
        getPlaceholders,
        
        // Debug
        getState,
        reset
    };
})();