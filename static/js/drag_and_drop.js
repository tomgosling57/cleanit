// drag_and_drop.js

const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

// Generic Dragula initialization function
function initDragula(containers, dropHandler) {
    // If there's an existing instance, clean it up
    if (window.drake) {
        try {
            window.drake.destroy();
        } catch (e) {
            console.warn('Could not destroy existing Dragula instance:', e);
        }
    }

    if (containers.length === 0) return;

    const drake = dragula(containers, {
        moves: function(el, source, handle, sibling) {
            // Prevent dragging if element has 'no-drag' class
            return !el.classList.contains('no-drag');
        }
    });

    drake.on('drop', dropHandler);

    window.drake = drake; // keep global ref
    console.log('Dragula initialised for', containers.length, 'containers');
}

// Specific handler for team member drops
function handleTeamMemberDrop(el, target, source) {
    const memberId = el.dataset.memberId;
    const newTeamId = target.closest('.team-card').id;
    const newTeamIdNumber = newTeamId.split('-').pop();
    const oldTeamId = source.closest('.team-card').id;
    const oldTeamIdNumber = oldTeamId.split('-').pop();
    const apiUrl = `/teams/team/${newTeamIdNumber}/member/add`;

    fetch(apiUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            user_id: memberId,
            old_team_id: oldTeamIdNumber
        })
    })
    .then(res => res.json())
    .then(data => {
        if (!data.success) {
            alert('Error: ' + (data.error || 'Unknown error'));
            return;
        }
        const oldTeamElement = htmx.find('#' + oldTeamId);
        const newTeamElement = htmx.find('#' + newTeamId);

        if (oldTeamElement) {
            oldTeamElement.outerHTML = data.oldTeam;
            htmx.process(htmx.find('#' + oldTeamId)); // Re-process HTMX attributes
        }
        if (newTeamElement) {
            newTeamElement.outerHTML = data.newTeam;
            htmx.process(htmx.find('#' + newTeamId)); // Re-process HTMX attributes
        }

        // Re-initialize Dragula for team members after DOM update
        initTeamMemberDragula();
    })
    .catch(console.error);
}

// Specific handler for job card drops
function handleJobCardDrop(el, target, source) {
    const jobId = el.id.split('-').pop();
    const newTeamColumn = target.closest('.team-column');
    const newTeamId = newTeamColumn ? newTeamColumn.dataset.teamId : null;
    const oldTeamColumn = source.closest('.team-column');
    const oldTeamId = oldTeamColumn ? oldTeamColumn.dataset.teamId : null;

    if (!newTeamId) {
        console.error('Could not determine new team ID for job card drop.');
        // Revert the drag if the target is not a valid team column
        source.appendChild(el);
        return;
    }

    const urlPattern = document.getElementById("team-timetable-view").dataset.jobReassignUrl;
    const apiUrl = urlPattern;

htmx.ajax('POST', apiUrl, {
    headers: {
        'X-CSRFToken': csrfToken
    },
    values: {
        new_team_id: newTeamId,
        old_team_id: oldTeamId,
        job_id: jobId // Pass job_id explicitly for the backend
    },
    target: '#team-timetable-view',
    swap: 'innerHTML',
    // Revert the drag if the HTMX request fails
    onLoad: function(evt) {
        if (evt.detail.xhr.status >= 400) {
            console.error('Error reassigning job:', evt.detail.xhr.responseText);
            alert('Error: Failed to reassign job.');
            source.appendChild(el); // Revert the drag
        } else {
            // Re-initialize Dragula for job cards after HTMX swap
            // This is necessary because the entire #team-timetable-view is swapped
            // and Dragula instances are lost.
            initJobCardDragula();
        }
    }
});
}

// Initialization for team members
export function initTeamMemberDragula() {
    const teamContainers = Array.from(document.querySelectorAll('.members-list'));
    initDragula(teamContainers, handleTeamMemberDrop);
}

// Initialization for job cards
export function initJobCardDragula() {
    const jobContainers = Array.from(document.querySelectorAll('.team-column'));
    initDragula(jobContainers, handleJobCardDrop);
}

// Make initialization functions globally available
window.initTeamMemberDragula = initTeamMemberDragula;
window.initJobCardDragula = initJobCardDragula;

function setupDragAndDropListeners() {
    // Remove any existing listeners first to avoid duplicates
    document.removeEventListener('teamListUpdated', handleTeamListUpdated);
    document.removeEventListener('htmx:afterSwap', handleHtmxAfterSwap);
    document.removeEventListener('htmx:afterSettle', handleHtmxAfterSettle);
    
    // Custom event for team list updates
    document.addEventListener('teamListUpdated', handleTeamListUpdated);
    
    // Comprehensive HTMX swap listener
    document.addEventListener('htmx:afterSwap', handleHtmxAfterSwap);
    
    // Also listen for HTMX content settled event for more reliable reinitialization
    document.addEventListener('htmx:afterSettle', handleHtmxAfterSettle);
    
    console.log('Drag and drop listeners setup complete');
}

function handleTeamListUpdated() {
    console.log('Team list updated, re-initializing Dragula for team members.');
    initTeamMemberDragula();
}

function handleHtmxAfterSwap(event) {
    const target = event.detail.target;
    
    // First check for data attribute for precise control
    let reinitType = target.getAttribute('data-reinit-dragula');
    if (!reinitType) {
        const closestWithAttr = target.closest('[data-reinit-dragula]');
        if (closestWithAttr) {
            reinitType = closestWithAttr.getAttribute('data-reinit-dragula');
        }
    }
    
    if (reinitType === 'team-members') {
        console.log('Data attribute indicates team members need reinitialization.');
        initTeamMemberDragula();
        return;
    } else if (reinitType === 'job-cards') {
        console.log('Data attribute indicates job cards need reinitialization.');
        initJobCardDragula();
        return;
    } else if (reinitType === 'both') {
        console.log('Data attribute indicates both need reinitialization.');
        initTeamMemberDragula();
        initJobCardDragula();
        return;
    }
    
    // Fall back to DOM-based detection if no data attribute
    // Check if swap affects team member drag and drop
    if (target.closest('.teams-grid') ||
        target.classList.contains('team-card') ||
        target.closest('.team-card')) {
        console.log('HTMX swap detected in teams area, re-initializing Dragula for team members.');
        initTeamMemberDragula();
    }
    
    // Check if swap affects job card drag and drop
    if (target.closest('#team-columns-container') ||
        target.closest('.team-column') ||
        target.id === 'team-timetable-view' ||
        target.closest('.timetable-container')) {
        console.log('HTMX swap detected in timetable area, re-initializing Dragula for job cards.');
        initJobCardDragula();
    }
    
    // Check if swap contains drag-and-drop containers directly
    if (target.querySelector('.members-list') || target.querySelector('.team-column')) {
        console.log('HTMX swap contains drag-and-drop containers, re-initializing both.');
        initTeamMemberDragula();
        initJobCardDragula();
    }
}

function handleHtmxAfterSettle(event) {
    const target = event.detail.target;
    
    // Re-check for drag-and-drop containers after content has settled
    if (target.querySelector('.members-list')) {
        console.log('Content settled with team members, re-initializing team member Dragula.');
        initTeamMemberDragula();
    }
    
    if (target.querySelector('.team-column')) {
        console.log('Content settled with job columns, re-initializing job card Dragula.');
        initJobCardDragula();
    }
}

// Initialize on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    initTeamMemberDragula();
    initJobCardDragula();
    setupDragAndDropListeners();
});

// Also set up listeners immediately if DOM is already loaded
if (document.readyState === 'loading') {
    // DOM is still loading, wait for DOMContentLoaded
    document.addEventListener('DOMContentLoaded', setupDragAndDropListeners);
} else {
    // DOM is already loaded, set up listeners now
    setupDragAndDropListeners();
}