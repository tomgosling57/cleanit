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
                const editTeamForm = teamModalContent.querySelector('#editTeamForm');
                if (editTeamForm) {
                    editTeamForm.querySelector('#editTeamId').value = teamId;
                    editTeamForm.querySelector('#editTeamName').value = teamName;

                    // Populate members dropdown
                    const memberSelect = editTeamForm.querySelector('#editTeamMembers');
                    Array.from(memberSelect.options).forEach(option => {
                        const isMember = teamMembers.includes(option.textContent.split(' ')[0]);
                        option.selected = isMember;
                        // Grey out users already on other teams
                        if (option.dataset.teamId && option.dataset.teamId !== teamId) {
                            option.disabled = true;
                        } else {
                            option.disabled = false;
                        }
                    });

                    // Populate leader dropdown
                    const leaderSelect = editTeamForm.querySelector('#editTeamLeader');
                    Array.from(leaderSelect.options).forEach(option => {
                        const userId = option.value;
                        option.selected = (userId === teamLeadId);
                        // Existing logic for greying out leaders (if applicable)
                        // if (option.dataset.userRole === 'owner' || option.dataset.userRole === 'team_leader') {
                        //     if (userId !== teamLeadId) {
                        //         option.disabled = true;
                        //     }
                        // }
                    });
                }
            } catch (error) {
                console.error('Error loading edit team form:', error);
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
});