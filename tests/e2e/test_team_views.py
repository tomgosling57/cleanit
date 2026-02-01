# tests/test_team_views.py
import re
import pytest
from tests.helpers import login_admin, wait_for_modal, setup_team_page, get_all_team_cards, assert_modal_title, close_modal, click_and_wait_for_response, drag_to_and_wait_for_response, simulate_htmx_delete_and_expect_response, assert_element_is_draggable, assert_element_is_not_draggable
from playwright.sync_api import expect

def test_team_cards(page, goto, server_url) -> None:
    login_admin(page, goto)
    setup_team_page(page)

    # Get all of the team cards
    team_cards = get_all_team_cards(page)
    expect(team_cards).to_have_count(5)
    # Get first team card
    team_card = team_cards.first
    # Assert expected details are visible
    expect(team_card.get_by_text("Initial Team")).to_be_visible()
    team_leader_card = team_card.locator('li.team-leader-member')
    expect(team_leader_card).to_be_visible()
    expect(team_leader_card.get_by_text("Lily Hargrave")).to_be_visible()

def test_team_reassignment(admin_page) -> None:
    """Tests:
    1. That team members can be dragged to a new team to reassign them.
    2. That team reassignments persist in the backend.
    3. That teams render in a consistent order.
    4. That when a team leader is reassigned to a new team, the old team removes that team leader and auto reassigns a new leader.
    
    Args:
        admin_page: The Playwright page object with admin privileges."""
    page = admin_page
    setup_team_page(page)

    # Get the team cards
    team_cards = get_all_team_cards(page)
    old_team = team_cards.nth(1)
    new_team = team_cards.nth(2)
    expect(old_team).to_be_visible()
    expect(new_team).to_be_visible()
    # Verify initial team leader of old team
    old_team_leader = old_team.locator('li.team-leader-member').first.get_by_text("Benjara Brown")
    expect(old_team_leader).to_be_visible()
    new_team_id = new_team.get_attribute('data-team-id')
    # Drag team leader to new team (covers #1)
    drag_to_and_wait_for_response(page, old_team_leader, new_team, f"**/teams/team/{new_team_id}/member/add**")

    # Assert that the reassignment persists after refreshing . the page (covers #2)
    pre_refresh_team_members = page.locator('.team-members').all()
    page.reload()  
    team_members = page.locator('.team-members').all()
    page.locator('.teams-container').wait_for(state="visible")    
    # Verify team members text matches pre-refresh state (covers #3)
    for i in range(len(pre_refresh_team_members)):
        expect(team_members[i]).to_have_text(pre_refresh_team_members[i].inner_text())
        for j in range(team_members[i].locator('li.member-item').count()): # Unnecessary sanity check
            expect(team_members[i].locator('li.member-item').nth(j)).to_have_text(pre_refresh_team_members[i].locator('li.member-item').nth(j).inner_text())

    # Verify new team has the new team leader (covers #4)    
    new_team_leader = new_team.locator('li.team-leader-member').first.get_by_text("Benjara Brown")
    expect(new_team_leader).to_be_visible()
    # Verify old team has removed the team leader
    expect(old_team_leader).to_be_hidden()
    old_team.get_by_role("button", name="Edit").click()
    modal = wait_for_modal(page, "#team-modal")
    expect(modal.locator("form")).to_have_attribute("data-team-leader-id", "None")


def test_delete_team_error_handling(page, goto, server_url) -> None:
    """Test deleting a team and handling errors when trying to delete a non-existent team.
    
    Args:
        page: The Playwright page object.
        goto: The goto fixture to navigate to the app.
        base_url: The base URL of the live server.
        """
    login_admin(page, goto)
    setup_team_page(page)

    # Get all team cards
    team_cards = get_all_team_cards(page)
    initial_team_count = team_cards.count()
    assert initial_team_count > 0, "There should be at least one team to delete."

    # Get the last team card and its delete button
    last_team_card = team_cards.last
    last_team_id = last_team_card.get_attribute('data-team-id')
    delete_button = last_team_card.get_by_role("button", name="Delete")

    # Handle the confirmation dialog
    page.on('dialog', lambda d: d.accept())

    # 1. Delete the last team in the grid
    click_and_wait_for_response(page, delete_button, f"**/teams/team/{last_team_id}/delete**")
    
    # Wait for the HTMX swap to complete and the team to be removed from the grid
    expect(page.locator(".teams-grid")).to_be_visible()
    expect(page.locator(f'div.team-card[data-team-id="{last_team_id}"]')).not_to_be_attached()
    expect(team_cards).to_have_count(initial_team_count - 1)

    # 2. Attempt to delete the same team again (should show error messages)
    # Simulate the delete request again
    response_info = simulate_htmx_delete_and_expect_response(
        page,
        server_url,
        f"/teams/team/{last_team_id}/delete",
        '#errors-container'
    )
    response = response_info.value
    assert response.status == 200, f"Expected 200 but got {response.status}"

    # 3. Assert that the error message appears in the errors container
    errors_container = page.locator("#errors-container")
    assert errors_container.count() == 1, "Expected errors container to be present"
    expect(errors_container).to_be_visible()
    expect(errors_container).to_contain_text("Team not found")

def test_draggable_elements(admin_page, request) -> None:
    """Tests that team members are draggable and 'No members in this team' message is not draggable."""
    # # Skip this test if not running in headed mode
    # # The --headed flag is passed to pytest-playwright
    # if not request.config.option.headed:
    #     pytest.skip("test_draggable_elements requires --headed flag to run")
    
    page = admin_page
    setup_team_page(page)

    # Get all team cards
    team_cards = get_all_team_cards(page)
    expect(team_cards).to_have_count(5)
    
    # First team card - should have draggable members
    first_team = team_cards.first
    first_team_members = first_team.locator('.members-list li.member-item')
    expect(first_team_members).to_have_count(2)  # Should have 2 members based on test data
    
    # Check that team members are draggable by verifying they don't have the no-drag class
    for i in range(first_team_members.count()):
        member = first_team_members.nth(i)
        expect(member).not_to_have_class('no-drag')
    
    # Test that team members are actually draggable using our new helper
    # First, test one member is draggable (visual feedback and basic drag)
    second_team = team_cards.nth(1)
    second_team_members_list = second_team.locator('.members-list')
    first_member = first_team_members.first
    
    # Use the helper to assert the element is draggable
    assert_element_is_draggable(page, first_member, second_team_members_list)
    
    # Now test the full drag with network request (which also tests the API integration)
    second_team_id = second_team.get_attribute('data-team-id')
    drag_to_and_wait_for_response(
        page,
        first_member,
        second_team_members_list,
        f"**/teams/team/{second_team_id}/member/add**"
    )
    
    # Third team card - should have "no members" message
    third_team = team_cards.nth(2)  # 0-based index
    no_members_message = third_team.locator('.no-members.no-drag')
    expect(no_members_message).to_be_visible()
    expect(no_members_message).to_have_text('No members in this team')
    
    # Verify the "no members" message has the no-drag class
    expect(no_members_message).to_have_class(re.compile(r'no-drag'))
    
    # Test that the "no members" message is NOT draggable using our new helper
    # First, get a reference to a target (another team's member list)
    fourth_team = team_cards.nth(3)
    fourth_team_members_list = fourth_team.locator('.members-list')
    
    # Use the helper to assert the element is not draggable
    assert_element_is_not_draggable(page, no_members_message, fourth_team_members_list)
    
    