/**
 * Global Alert Manager for CleanIt
 * Provides toast-style notifications for success, error, warning, and info messages
 * Integrates with HTMX for automatic error handling
 */

(function() {
    'use strict';

    const AlertManager = {
        // Configuration
        config: {
            defaultDuration: 5000, // 5 seconds
            maxAlerts: 5,
            position: 'top-right',
            animationDuration: 300
        },

        // State
        alerts: [],
        container: null,
        template: null,

        /**
         * Initialize the alert manager
         */
        init: function() {
            this.createContainer();
            this.createTemplate();
            this.setupHtmxListeners();
            this.setupGlobalErrorHandler();
            
            console.log('AlertManager initialized');
        },

        /**
         * Create the global alerts container if it doesn't exist
         */
        createContainer: function() {
            let container = document.getElementById('global-alerts');
            
            if (!container) {
                container = document.createElement('div');
                container.id = 'global-alerts';
                container.setAttribute('aria-live', 'polite');
                container.setAttribute('aria-atomic', 'true');
                document.body.appendChild(container);
            }
            
            this.container = container;
        },

        /**
         * Create the alert template
         */
        createTemplate: function() {
            const template = document.createElement('template');
            template.id = 'alert-template';
            template.innerHTML = `
                <div class="alert" role="alert">
                    <div class="alert-content">
                        <span class="alert-icon" aria-hidden="true"></span>
                        <div class="alert-text">
                            <div class="alert-message"></div>
                            <div class="alert-details" style="display: none;"></div>
                        </div>
                    </div>
                    <button class="alert-dismiss" aria-label="Dismiss alert">×</button>
                    <div class="alert-progress"></div>
                </div>
            `;
            
            document.body.appendChild(template);
            this.template = template;
        },

        /**
         * Show an alert
         * @param {string} type - 'success', 'error', 'warning', 'info'
         * @param {string} message - The alert message
         * @param {object} options - Additional options
         */
        show: function(type, message, options = {}) {
            const alertId = 'alert-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
            const duration = options.duration || this.config.defaultDuration;
            const details = options.details || '';
            
            // Create alert element
            const alertElement = this.template.content.cloneNode(true).querySelector('.alert');
            alertElement.id = alertId;
            alertElement.classList.add('alert-' + type);
            
            // Set message and details
            const messageEl = alertElement.querySelector('.alert-message');
            messageEl.textContent = message;
            
            const detailsEl = alertElement.querySelector('.alert-details');
            if (details) {
                detailsEl.textContent = typeof details === 'string' ? details : JSON.stringify(details);
                detailsEl.style.display = 'block';
            }
            
            // Set icon based on type
            const iconEl = alertElement.querySelector('.alert-icon');
            const icons = {
                success: '✓',
                error: '✗',
                warning: '⚠',
                info: 'ℹ'
            };
            iconEl.textContent = icons[type] || '•';
            
            // Setup dismiss button
            const dismissBtn = alertElement.querySelector('.alert-dismiss');
            dismissBtn.addEventListener('click', () => {
                this.dismiss(alertId);
            });
            
            // Setup auto-dismiss if duration is positive
            if (duration > 0) {
                const progressEl = alertElement.querySelector('.alert-progress');
                progressEl.style.animationDuration = duration + 'ms';
                
                setTimeout(() => {
                    this.dismiss(alertId);
                }, duration);
            }
            
            // Add to container and alerts array
            this.container.appendChild(alertElement);
            this.alerts.push({
                id: alertId,
                element: alertElement,
                type: type,
                message: message
            });
            
            // Limit number of alerts
            if (this.alerts.length > this.config.maxAlerts) {
                const oldestAlert = this.alerts.shift();
                this.dismiss(oldestAlert.id);
            }
            
            // Focus on new alert for accessibility
            setTimeout(() => {
                alertElement.setAttribute('tabindex', '-1');
                alertElement.focus();
            }, 100);
            
            return alertId;
        },

        /**
         * Dismiss an alert by ID
         * @param {string} alertId - The ID of the alert to dismiss
         */
        dismiss: function(alertId) {
            const alertIndex = this.alerts.findIndex(alert => alert.id === alertId);
            
            if (alertIndex === -1) return;
            
            const alert = this.alerts[alertIndex];
            alert.element.classList.add('alert-exiting');
            
            // Remove from DOM after animation
            setTimeout(() => {
                if (alert.element.parentNode) {
                    alert.element.parentNode.removeChild(alert.element);
                }
                this.alerts.splice(alertIndex, 1);
            }, this.config.animationDuration);
        },

        /**
         * Clear all alerts
         */
        clearAll: function() {
            this.alerts.forEach(alert => {
                this.dismiss(alert.id);
            });
        },

        /**
         * Setup HTMX event listeners for automatic error handling
         */
        setupHtmxListeners: function() {
            // Handle HTMX response errors
            document.addEventListener('htmx:responseError', (event) => {
                this.handleHtmxError(event.detail.xhr);
            });
            
            // Handle HTMX validation errors (422)
            document.addEventListener('htmx:beforeSwap', (event) => {
                const xhr = event.detail.xhr;
                
                if (xhr.status >= 400 && xhr.status < 600) {
                    // Try to parse error response
                    try {
                        const response = JSON.parse(xhr.responseText);
                        const errorInfo = this.parseErrorResponse(response);
                        
                        // Show error alert
                        this.show('error', errorInfo.message, {
                            details: errorInfo.details
                        });
                        
                        // Prevent HTMX from swapping content for error responses
                        // unless it's a validation error that should be handled by the form
                        if (xhr.status !== 422) {
                            event.detail.shouldSwap = false;
                        }
                    } catch (e) {
                        // If we can't parse JSON, show generic error
                        this.show('error', `Request failed with status ${xhr.status}`);
                        event.detail.shouldSwap = false;
                    }
                }
            });
            
            // Handle successful HTMX responses with messages
            document.addEventListener('htmx:afterSwap', (event) => {
                // Check if response contains a success message
                const response = event.detail.xhr.responseText;
                
                try {
                    const data = JSON.parse(response);
                    if (data.success && data.message) {
                        this.show('success', data.message);
                    }
                } catch (e) {
                    // Not JSON, ignore
                }
            });
        },

        /**
         * Setup global error handler for uncaught errors
         */
        setupGlobalErrorHandler: function() {
            window.addEventListener('error', (event) => {
                // Don't show alerts for errors without messages
                if (!event.message) return;
                
                // Only show errors that aren't likely to be network errors
                if (!event.message.includes('Failed to fetch') && 
                    !event.message.includes('NetworkError')) {
                    this.show('error', `JavaScript Error: ${event.message}`);
                }
            });
        },

        /**
         * Parse error response from backend
         * @param {object|string} response - The error response
         * @returns {object} Parsed error information
         */
        parseErrorResponse: function(response) {
            if (typeof response === 'string') {
                return {
                    message: response,
                    type: 'server_error',
                    details: {}
                };
            }
            
            if (response && typeof response === 'object') {
                // New format: { success: false, error: { message, type, details } }
                if (response.error && typeof response.error === 'object') {
                    return {
                        message: response.error.message || 'Unknown error',
                        type: response.error.type || 'server_error',
                        details: response.error.details || {}
                    };
                }
                
                // Old format: { error: "message" }
                if (response.error && typeof response.error === 'string') {
                    return {
                        message: response.error,
                        type: 'server_error',
                        details: {}
                    };
                }
                
                // Fallback: use first string value
                for (const key in response) {
                    if (typeof response[key] === 'string') {
                        return {
                            message: response[key],
                            type: 'server_error',
                            details: {}
                        };
                    }
                }
            }
            
            return {
                message: 'An unknown error occurred',
                type: 'server_error',
                details: {}
            };
        },

        /**
         * Convenience methods for different alert types
         */
        success: function(message, options = {}) {
            return this.show('success', message, options);
        },
        
        error: function(message, options = {}) {
            return this.show('error', message, options);
        },
        
        warning: function(message, options = {}) {
            return this.show('warning', message, options);
        },
        
        info: function(message, options = {}) {
            return this.show('info', message, options);
        },

        /**
         * Handle HTMX error response
         * @param {XMLHttpRequest} xhr - The XHR object
         */
        handleHtmxError: function(xhr) {
            let errorMessage = 'Request failed';
            
            if (xhr.status === 0) {
                errorMessage = 'Network error: Unable to connect to server';
            } else if (xhr.status === 401) {
                errorMessage = 'Unauthorized: Please log in again';
            } else if (xhr.status === 403) {
                errorMessage = 'Forbidden: You do not have permission';
            } else if (xhr.status === 404) {
                errorMessage = 'Resource not found';
            } else if (xhr.status === 422) {
                errorMessage = 'Validation error';
            } else if (xhr.status >= 500) {
                errorMessage = 'Server error: Please try again later';
            }
            
            // Try to get more specific error from response
            try {
                const response = JSON.parse(xhr.responseText);
                const errorInfo = this.parseErrorResponse(response);
                this.show('error', errorInfo.message, {
                    details: errorInfo.details
                });
            } catch (e) {
                // If we can't parse JSON, use generic message
                this.show('error', `${errorMessage} (Status: ${xhr.status})`);
            }
        }
    };

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            AlertManager.init();
        });
    } else {
        AlertManager.init();
    }

    // Export to global scope
    window.AlertManager = AlertManager;
    
    // Also expose convenience functions
    window.showAlert = AlertManager.show.bind(AlertManager);
    window.showSuccess = AlertManager.success.bind(AlertManager);
    window.showError = AlertManager.error.bind(AlertManager);
    window.showWarning = AlertManager.warning.bind(AlertManager);
    window.showInfo = AlertManager.info.bind(AlertManager);
    
})();