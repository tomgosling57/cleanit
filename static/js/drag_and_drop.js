// drag_and_drop.js

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

    const drake = dragula(containers);

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
        headers: { 'Content-Type': 'application/json' },
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

    console.log(`Job ${jobId} dropped from team ${oldTeamId} to team ${newTeamId}`);

    const urlPattern = document.getElementById("team-timetable-view").dataset.jobReassignUrl;
    const apiUrl = urlPattern.replace('0', jobId);

    fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            new_team_id: newTeamId,
            old_team_id: oldTeamId
        })
    })
    .then(res => res.json())
    .then(data => {
        if (!data.success) {
            alert('Error: ' + (data.error || 'Unknown error'));
            // Revert the drag if the server operation failed
            source.appendChild(el);
            return;
        }
        // HTMX will handle the re-rendering of the job cards and team columns
        // No need to manually re-initialize Dragula here, as HTMX will trigger a full re-render
        // and the main script will re-initialize Dragula for jobs.
        console.log('Job reassigned successfully:', data);
        // Trigger a custom event to signal that job assignments have been updated
        document.body.dispatchEvent(new CustomEvent('jobAssignmentsUpdated'));
    })
    .catch(error => {
        console.error('Error reassigning job:', error);
        // Revert the drag if there was a network error
        source.appendChild(el);
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

document.addEventListener('DOMContentLoaded', () => {
    initTeamMemberDragula();

    document.body.addEventListener('teamListUpdated', () => {
        console.log('Team list updated, re-initializing Dragula for team members.');
        initTeamMemberDragula();
    });

    // Listen for HTMX content swaps that might affect team member lists
    document.body.addEventListener('htmx:afterSwap', (event) => {
        // Re-initialize Dragula if the swapped content is part of the teams grid or a team card
        // This covers cases where team cards or the entire list are updated
        if (event.detail.target.closest('.teams-grid') || event.detail.target.classList.contains('team-card')) {
            console.log('HTMX swap detected in teams area, re-initializing Dragula for team members.');
            initTeamMemberDragula();
        }
    });
});