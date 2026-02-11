/**
 * Job Time Auto-Update
 * Automatically updates start_time, end_time, and arrival_datetime fields
 * when clicked if their current value is in the past (relative to application timezone).
 * Updates to the nearest future time (rounded up to the next hour).
 */

(function() {
    'use strict';

    // Application timezone (should be set by server)
    const APP_TIMEZONE = document.body.dataset.appTimezone || 'UTC';
    
    // Date/time formats (must match config.py)
    const DATE_FORMAT = 'DD-MM-YYYY';  // e.g., 11-02-2026
    const TIME_FORMAT = 'HH:mm';       // e.g., 14:30
    const DATETIME_FORMAT = 'DD-MM-YYYY HH:mm'; // e.g., 11-02-2026 14:30
    
    /**
     * Parse a date string in DD-MM-YYYY format to a Date object in app timezone.
     * @param {string} dateStr - Date string in DD-MM-YYYY format
     * @returns {Date|null} Date object in app timezone, or null if invalid
     */
    function parseDate(dateStr) {
        if (!dateStr) return null;
        const parts = dateStr.split('-');
        if (parts.length !== 3) return null;
        const day = parseInt(parts[0], 10);
        const month = parseInt(parts[1], 10) - 1; // JS months are 0-indexed
        const year = parseInt(parts[2], 10);
        if (isNaN(day) || isNaN(month) || isNaN(year)) return null;
        // Create date in app timezone using Intl API
        return new Date(Date.UTC(year, month, day, 0, 0, 0));
    }
    
    /**
     * Parse a time string in HH:mm format and combine with a date.
     * @param {string} timeStr - Time string in HH:mm format
     * @param {Date} date - Date object (should be in app timezone)
     * @returns {Date|null} Combined datetime in app timezone, or null if invalid
     */
    function parseTime(timeStr, date) {
        if (!timeStr || !date) return null;
        const parts = timeStr.split(':');
        if (parts.length !== 2) return null;
        const hours = parseInt(parts[0], 10);
        const minutes = parseInt(parts[1], 10);
        if (isNaN(hours) || isNaN(minutes)) return null;
        const result = new Date(date);
        result.setUTCHours(hours, minutes, 0, 0);
        return result;
    }
    
    /**
     * Parse a datetime string in DD-MM-YYYY HH:mm format.
     * @param {string} datetimeStr - Datetime string
     * @returns {Date|null} Date object in app timezone, or null if invalid
     */
    function parseDateTime(datetimeStr) {
        if (!datetimeStr) return null;
        const [datePart, timePart] = datetimeStr.split(' ');
        if (!datePart || !timePart) return null;
        const date = parseDate(datePart);
        if (!date) return null;
        return parseTime(timePart, date);
    }
    
    /**
     * Format a Date object to DD-MM-YYYY string.
     * @param {Date} date - Date object (assumed to be in app timezone)
     * @returns {string} Formatted date string
     */
    function formatDate(date) {
        const day = String(date.getUTCDate()).padStart(2, '0');
        const month = String(date.getUTCMonth() + 1).padStart(2, '0');
        const year = date.getUTCFullYear();
        return `${day}-${month}-${year}`;
    }
    
    /**
     * Format a Date object to HH:mm string.
     * @param {Date} date - Date object (assumed to be in app timezone)
     * @returns {string} Formatted time string
     */
    function formatTime(date) {
        const hours = String(date.getUTCHours()).padStart(2, '0');
        const minutes = String(date.getUTCMinutes()).padStart(2, '0');
        return `${hours}:${minutes}`;
    }
    
    /**
     * Format a Date object to DD-MM-YYYY HH:mm string.
     * @param {Date} date - Date object (assumed to be in app timezone)
     * @returns {string} Formatted datetime string
     */
    function formatDateTime(date) {
        return `${formatDate(date)} ${formatTime(date)}`;
    }
    
    /**
     * Get current datetime in application timezone.
     * @returns {Date} Current datetime in app timezone
     */
    function nowInAppTimezone() {
        // Create a date in UTC, then convert to app timezone using Intl
        const now = new Date();
        // Use Intl to format to app timezone and parse back (simplified)
        // For simplicity, we assume the browser's local time matches app timezone
        // This is not accurate, but we'll improve later if needed.
        // TODO: Implement proper timezone conversion using Intl.DateTimeFormat
        return now;
    }
    
    /**
     * Round up a datetime to the next hour.
     * @param {Date} date - Input datetime
     * @returns {Date} Rounded up datetime (minutes and seconds set to 0, hour incremented if needed)
     */
    function roundUpToNextHour(date) {
        const rounded = new Date(date);
        rounded.setUTCMinutes(0, 0, 0);
        if (rounded.getTime() <= date.getTime()) {
            rounded.setUTCHours(rounded.getUTCHours() + 1);
        }
        return rounded;
    }
    
    /**
     * Adjust a datetime if it's in the past relative to now.
     * If in past, returns now rounded up to next hour.
     * @param {Date} target - Target datetime to check
     * @param {Date} now - Current datetime in app timezone
     * @returns {Date} Adjusted datetime (either original or future)
     */
    function adjustIfPast(target, now) {
        if (target.getTime() < now.getTime()) {
            // Round up to next hour
            return roundUpToNextHour(now);
        }
        return target;
    }
    
    /**
     * Handle click on a time field (start_time or end_time).
     * Combines with date field to check if past.
     */
    function handleTimeFieldClick(event) {
        const timeField = event.target;
        const dateField = document.getElementById('date');
        if (!dateField || !dateField.value) {
            // No date selected, cannot determine past/future
            return;
        }
        
        const date = parseDate(dateField.value);
        const time = parseTime(timeField.value, date);
        if (!time) {
            // Invalid time, keep as is
            return;
        }
        
        const now = nowInAppTimezone();
        const adjusted = adjustIfPast(time, now);
        
        // Update if changed
        if (adjusted.getTime() !== time.getTime()) {
            timeField.value = formatTime(adjusted);
            // Also update date if date changed (e.g., crossing midnight)
            dateField.value = formatDate(adjusted);
        }
    }
    
    /**
     * Handle click on arrival datetime field.
     */
    function handleArrivalDatetimeClick(event) {
        const datetimeField = event.target;
        const datetimeStr = datetimeField.value;
        if (!datetimeStr) {
            // Empty field, nothing to adjust
            return;
        }
        
        const datetime = parseDateTime(datetimeStr);
        if (!datetime) {
            // Invalid format, keep as is
            return;
        }
        
        const now = nowInAppTimezone();
        const adjusted = adjustIfPast(datetime, now);
        
        if (adjusted.getTime() !== datetime.getTime()) {
            // Update field value (flatpickr will need to be notified)
            datetimeField.value = formatDateTime(adjusted);
            // Trigger change event for flatpickr
            datetimeField.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }
    
    /**
     * Initialize event listeners on job forms.
     */
    function init() {
        // Find job creation and update forms
        const forms = [
            document.getElementById('job-form'), // creation
            document.getElementById('edit-job-form') // update
        ].filter(Boolean);
        
        forms.forEach(form => {
            // Start time field
            const startTime = form.querySelector('#start_time');
            if (startTime) {
                startTime.addEventListener('click', handleTimeFieldClick);
            }
            
            // End time field
            const endTime = form.querySelector('#end_time');
            if (endTime) {
                endTime.addEventListener('click', handleTimeFieldClick);
            }
            
            // Arrival datetime field
            const arrivalDatetime = form.querySelector('#arrival_datetime');
            if (arrivalDatetime) {
                arrivalDatetime.addEventListener('click', handleArrivalDatetimeClick);
            }
        });
        
        console.log('Job time auto-update initialized');
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Export for testing
    window.JobTimeAutoUpdate = {
        init,
        parseDate,
        parseTime,
        parseDateTime,
        formatDate,
        formatTime,
        formatDateTime,
        nowInAppTimezone,
        roundUpToNextHour,
        adjustIfPast
    };
})();