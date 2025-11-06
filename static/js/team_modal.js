document.addEventListener('DOMContentLoaded', () => {
    const teamModal = document.getElementById('team-modal');
    const closeButton = teamModal.querySelector('.close-button');
    const teamModalContent = document.getElementById('team-modal-content');

    document.querySelectorAll('.edit-team-icon').forEach(icon => {
        icon.addEventListener('click', async (event) => {
            const teamId = event.target.dataset.teamId;
            const teamName = event.target.dataset.teamName;
            const teamLeadId = event.target.dataset.teamLeadId;
            const teamMembers = event.target.dataset.teamMembers ? event.target.dataset.teamMembers.split(', ').map(name => name.trim()) : [];

            // Fetch the edit form content dynamically
            try {
                const response = await htmx.ajax('GET', `/teams/team/${teamId}/edit_form`, {
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
                        const userId = option.value;
                        const isMember = teamMembers.includes(option.textContent.split(' ')[0]); // Check if username is in teamMembers
                        if (isMember) {
                            option.selected = true;
                        } else {
                            option.selected = false;
                        }
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
                        if (userId === teamLeadId) {
                            option.selected = true;
                        } else {
                            option.selected = false;
                        }
                        // Grey out users with owner or team_leader roles if they are not the current leader
                        // This logic needs to be refined based on actual user roles from backend
                        // For now, we'll rely on the backend to provide the disabled state
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
        });
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