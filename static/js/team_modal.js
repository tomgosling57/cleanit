function initDragula() {
    // If there's an existing instance, clean it up
    if (window.drake) {
        try {
            window.drake.destroy();
        } catch (e) {
            // Dragula’s destroy() isn’t always defined on all builds, so be safe
            console.warn('Could not destroy existing Dragula instance:', e);
        }
    }

    const teamContainers = Array.from(document.querySelectorAll('.members-list'));
    if (teamContainers.length === 0) return;

    const drake = dragula(teamContainers);

    drake.on('drop', handleDrop);

    window.drake = drake; // keep global ref
    console.log('Dragula initialised for', teamContainers.length, 'containers');
}

function handleDrop(el, target, source) {
    const memberId = el.dataset.memberId;
    const newTeamId = target.closest('.team-card').id;
    const newTeamIdNumber = newTeamId.split('-').pop();
    const oldTeamId = source.closest('.team-card').id;
    const oldTeamIdNumber = oldTeamId.split('-').pop();
    const apiUrl = `/teams/team/${newTeamIdNumber}/add_member`;

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
        htmx.find('#' + oldTeamId).outerHTML = data.oldTeam;
        htmx.find('#' + newTeamId).outerHTML = data.newTeam;

        // reinit for the updated DOM
        initDragula();
    })
    .catch(console.error);
}

document.addEventListener('DOMContentLoaded', () => {
    const teamModal = document.getElementById('team-modal');
    const closeButton = teamModal.querySelector('.close-button');
    const teamModalContent = document.getElementById('team-modal-content');

    // --- Event Delegation for .edit-team-icon ---
    // Attach a single click listener to a static parent (e.g., document.body)
    // This listener will catch clicks on .edit-team-icon elements,
    // even if they are added to the DOM dynamically by HTMX later.
    document.body.addEventListener('click', async (event) => {
        // Check if the clicked element (or its closest ancestor) matches '.edit-team-icon'
        const editIcon = event.target.closest('.edit-team-icon');
        if (editIcon) {
            // Prevent the default action if necessary, though for a span it's usually not needed
            event.preventDefault();

            const teamId = editIcon.dataset.teamId;
            const teamName = editIcon.dataset.teamName;
            const teamLeadId = editIcon.dataset.teamLeadId;
            const teamMembers = editIcon.dataset.teamMembers ? editIcon.dataset.teamMembers.split(', ').map(name => name.trim()) : [];

            try {
                // HTMX request to fetch the edit form content
                await htmx.ajax('GET', `/teams/team/${teamId}/edit_form`, {
                    target: '#team-modal-content',
                    swap: 'innerHTML'
                });

                // After HTMX swaps the content, populate the fields
                const editTeamForm = teamModalContent.querySelector('#edit-team-form');
                if (editTeamForm) {
                    editTeamForm.querySelector('#edit-team-id').value = teamId;
                    editTeamForm.querySelector('#edit-team-name').value = teamName;

                    // Populate members and leader dropdowns with optgroups
                    const memberSelect = editTeamForm.querySelector('#edit-team-members');
                    const leaderSelect = editTeamForm.querySelector('#edit-team-leader');

                    // Clear existing options
                    memberSelect.innerHTML = '';
                    leaderSelect.innerHTML = '<option value="">No Leader</option>'; // Add default "No Leader" option

                    const response = await fetch(`/teams/team/${teamId}/categorized_users`);
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    const categorizedUsers = await response.json();

                    const createOption = (user, isSelected, isDisabled) => {
                        const option = document.createElement('option');
                        option.value = user.id;
                        option.textContent = user.username;
                        option.selected = isSelected;
                        option.disabled = isDisabled;
                        return option;
                    };

                    // Populate memberSelect
                    const memberCategories = {
                        'on_this_team': 'On This Team',
                        'on_a_different_team': 'On A Different Team',
                        'unassigned': 'Unassigned'
                    };

                    for (const categoryKey in memberCategories) {
                        if (categorizedUsers[categoryKey] && categorizedUsers[categoryKey].length > 0) {
                            const optgroup = document.createElement('optgroup');
                            optgroup.label = memberCategories[categoryKey];
                            categorizedUsers[categoryKey].forEach(user => {
                                const isSelected = teamMembers.includes(user.username);
                                const isDisabled = categoryKey === 'on_a_different_team';
                                optgroup.appendChild(createOption(user, isSelected, isDisabled));
                            });
                            memberSelect.appendChild(optgroup);
                        }
                    }

                    // Populate leaderSelect
                    const leaderCategories = {
                        'on_this_team': 'On This Team',
                        'unassigned': 'Unassigned',
                        'on_a_different_team': 'On A Different Team'
                    };

                    for (const categoryKey in leaderCategories) {
                        if (categorizedUsers[categoryKey] && categorizedUsers[categoryKey].length > 0) {
                            const optgroup = document.createElement('optgroup');
                            optgroup.label = leaderCategories[categoryKey];
                            categorizedUsers[categoryKey].forEach(user => {
                                const isSelected = (String(user.id) === String(teamLeadId));
                                const isDisabled = categoryKey === 'on_a_different_team';
                                optgroup.appendChild(createOption(user, isSelected, isDisabled));
                            });
                            leaderSelect.appendChild(optgroup);
                        }
                    }
                }
            } catch (error) {
                console.error('Error loading edit team form or categorized users:', error);
            }

            teamModal.style.display = 'flex'; // Show the modal
        }
    });

    closeButton.addEventListener('click', () => {
        teamModal.style.display = 'none';
    });

    window.addEventListener('click', (event) => {
        if (event.target === teamModal) {
            teamModal.style.display = 'none';
        }
    });

    // Listen for HTMX afterSwap event to re-initialize dropdowns if needed
    document.body.addEventListener('htmx:afterSwap', (event) => {
        if (event.detail.target.id === 'team-modal-content') {
            // Re-initialize any select2 or other custom dropdowns here if you use them
            // For native selects, the population logic above should suffice on modal open
        }
    });

    // Listen for custom event to re-initialize Dragula after team list updates
    document.body.addEventListener('teamListUpdated', () => {
        console.log('Team list updated, re-initializing Dragula.');
        initDragula();
    });
});