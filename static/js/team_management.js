// team_management.js
import { initTeamMemberDragula } from './drag_and_drop.js';

document.addEventListener('DOMContentLoaded', () => {
    const teamModal = document.getElementById('team-modal');
    const closeButton = teamModal.querySelector('.close-button');
    const teamModalContent = document.getElementById('team-modal-content');

    // Helper function to populate select fields
    const populateTeamFormSelects = async (formElement, teamId = null, teamLeadId = null, teamMembers = []) => {
        const memberSelect = formElement.querySelector('select[name="members"]');
        const leaderSelect = formElement.querySelector('select[name="team_leader_id"]');

        if (!memberSelect || !leaderSelect) return;

        memberSelect.innerHTML = '';
        leaderSelect.innerHTML = '<option value="">No Leader</option>';

        const url = teamId ? `/teams/team/${teamId}/categorized_users` : `/users/all_categorized`; // Assuming a new endpoint for all users
        const response = await fetch(url);
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
            'on_a_different_team': 'On a Different Team',
            'unassigned': 'Unassigned'
        };

        for (const categoryKey in memberCategories) {
            if (categorizedUsers[categoryKey] && categorizedUsers[categoryKey].length > 0) {
                const optgroup = document.createElement('optgroup');
                optgroup.label = memberCategories[categoryKey];
                categorizedUsers[categoryKey].forEach(user => {
                    const isSelected = teamMembers.includes(user.username);
                    const isDisabled = false;
                    optgroup.appendChild(createOption(user, isSelected, isDisabled));
                });
                memberSelect.appendChild(optgroup);
            }
        }

        // Populate leaderSelect
        const leaderCategories = {
            'on_this_team': 'On This Team',
            'unassigned': 'Unassigned',
            'on_a_different_team': 'On a Different Team'
        };

        for (const categoryKey in leaderCategories) {
            if (categorizedUsers[categoryKey] && categorizedUsers[categoryKey].length > 0) {
                const optgroup = document.createElement('optgroup');
                optgroup.label = leaderCategories[categoryKey];
                categorizedUsers[categoryKey].forEach(user => {
                    const isSelected = (String(user.id) === String(teamLeadId));
                    const isDisabled = false;
                    optgroup.appendChild(createOption(user, isSelected, isDisabled));
                });
                leaderSelect.appendChild(optgroup);
            }
        }
    };

    // --- Event Delegation for edit team button ---
    document.body.addEventListener('click', async (event) => {
        const teamHeader = event.target.closest('.team-header');
        if (teamHeader) {
            event.preventDefault();

            const teamId = teamHeader.dataset.teamId;
            const teamName = teamHeader.dataset.teamName;
            const teamLeadId = teamHeader.dataset.teamLeadId;
            const teamMembers = teamHeader.dataset.teamMembers ? teamHeader.dataset.teamMembers.split(', ').map(name => name.trim()) : [];

            try {
                await htmx.ajax('GET', `/teams/team/${teamId}/edit_form`, {
                    target: '#team-modal-content',
                    swap: 'innerHTML'
                });

                const editTeamForm = teamModalContent.querySelector('#edit-team-form');
                if (editTeamForm) {
                    editTeamForm.querySelector('#edit-team-id').value = teamId;
                    editTeamForm.querySelector('#edit-team-name').value = teamName;
                    await populateTeamFormSelects(editTeamForm, teamId, teamLeadId, teamMembers);
                }
            } catch (error) {
                console.error('Error loading edit team form or categorized users:', error);
            }
            teamModal.style.display = 'flex';
        }
    });

    // --- Event Listener for create team button ---
    document.body.addEventListener('click', async (event) => {
        if (event.target.id === 'open-create-team-modal') {
            event.preventDefault();
            try {
                await htmx.ajax('GET', `/teams/create_form`, {
                    target: '#team-modal-content',
                    swap: 'innerHTML'
                });
                const createTeamForm = teamModalContent.querySelector('#create-team-form');
                if (createTeamForm) {
                    await populateTeamFormSelects(createTeamForm); // No teamId, teamLeadId, teamMembers for new team
                }
            } catch (error) {
                console.error('Error loading create team form or categorized users:', error);
            }
            teamModal.style.display = 'flex';
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

    document.body.addEventListener('htmx:afterSwap', (event) => {
        if (event.detail.target.id === 'team-modal-content') {
            // Re-initialize any select2 or other custom dropdowns here if you use them
        }
    });

    document.body.addEventListener('teamListUpdated', () => {
        console.log('Team list updated, re-initializing Dragula for team members.');
        initTeamMemberDragula();
    });
    const closeButtons = document.querySelectorAll('.team-close-button');
        closeButtons.forEach(button => {
        button.addEventListener('click', () => {
            const teamId = button.dataset.teamId;
            const numMembers = parseInt(button.dataset.numMembers, 10);
            if (numMembers > 0) {
                alert('Cannot delete a team that has members. Please reassign or remove all members before deleting the team.');
                return;
            }
            const confirmDelete = confirm('Are you sure you want to delete this team? This action cannot be undone.');
            if (!confirmDelete) return;

            htmx.ajax('DELETE', `/teams/team/${teamId}/delete`, {
                target: `#team-card-${teamId}`,
                swap: 'outerHTML'
            });
        });
    });
});

initTeamMemberDragula(); // Initial call to set up Dragula for team members