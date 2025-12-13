# tests/test_team_views.py
from tests.helpers import login_admin, wait_for_modal
from playwright.sync_api import expect

def _navigate_to_teams_page(page) -> None:
    # Navigate to the teams page
    page.get_by_text("Teams").click()
    # Wait for the teams grid to be visible
    teams_grid = page.locator(".teams-grid")
    expect(teams_grid).to_be_visible()

def test_team_cards(page, goto) -> None:
    login_admin(page, goto)
    _navigate_to_teams_page(page)

    # Get all of the team cards
    team_cards = page.locator('div.team-card')
    expect(team_cards).to_have_count(5)
    # Get first team card
    team_card = team_cards.first
    # Assert expected details are visible
    expect(team_card.get_by_text("Initial Team")).to_be_visible()
    team_leader_card = team_card.locator('li.team-leader-member')
    expect(team_leader_card).to_be_visible()
    expect(team_leader_card.get_by_text("Lily Hargrave")).to_be_visible()

# def test_update_team(page, goto) -> None:
#     login_admin(page, goto)
#     _navigate_to_teams_page(page)

#     # Get first team card
#     team_card = page.locator('div.team-card').first

#     # Click the Edit button
#     with page.expect_response(f"**/teams/team/{team_card.get_attribute('data-team-id')}/update**"):
#         team_card.get_by_text("edit").click()

#     # Wait for the modal to appear
#     modal = page.locator("#team-modal")
#     modal.wait_for(state="attached")
#     modal.wait_for(state="visible")

#     # Assert modal title
#     expect(modal.locator("h2")).to_have_text("Update Team")

#     # Assert form fields have expected values
#     expect(modal.locator("#name")).to_have_value("Initial Team")
#     expect(modal.locator("#team_leader_id")).to_have_value("2")  # Assuming Lily Hargrave has ID 2

#     # Close the modal
#     modal.get_by_text("×").click()
#     expect(modal).to_be_hidden()

def test_team_reassignment_removes_old_team_leader(page, goto) -> None:
    """Test that when a team leader is reassigned to a new team, the old team removes that team leader and auto reassigns.
    
    Args:
        page: The Playwright page object.
        goto: The goto fixture to navigate to the app."""
    login_admin(page, goto)
    _navigate_to_teams_page(page)

    # Get the team cards
    team_cards = page.locator('div.team-card')
    old_team = team_cards.nth(1)
    new_team = team_cards.nth(2)
    expect(old_team).to_be_visible()
    expect(new_team).to_be_visible()
    # Verify initial team leader of old team
    old_team_leader = old_team.locator('li.team-leader-member').first.get_by_text("Benjara Brown")
    expect(old_team_leader).to_be_visible()
    # Drag team leader to new team
    old_team_leader.drag_to(new_team)    
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
    _navigate_to_teams_page(page)

    # Get all team cards
    team_cards = page.locator('div.team-card')
    initial_team_count = team_cards.count()
    assert initial_team_count > 0, "There should be at least one team to delete."

    # Get the last team card and its delete button
    last_team_card = team_cards.last
    last_team_id = last_team_card.get_attribute('data-team-id')
    delete_button = last_team_card.get_by_role("button", name="Delete")

    # Handle the confirmation dialog
    page.on('dialog', lambda d: d.accept())

    # 1. Delete the last team in the grid
    with page.expect_response(f"**/teams/team/{last_team_id}/delete**"):
        page.wait_for_load_state("networkidle")
        delete_button.click()
    
    # Wait for the HTMX swap to complete and the team to be removed from the grid
    page.locator(".teams-grid").wait_for()
    expect(page.locator(f'div.team-card[data-team-id="{last_team_id}"]')).not_to_be_attached()
    expect(team_cards).to_have_count(initial_team_count - 1)

    # 2. Attempt to delete the same team again (should show error messages)
    # Simulate the delete request again
    with page.expect_response(f"**/teams/team/{last_team_id}/delete**") as response_info:
        page.evaluate(f"""
            htmx.ajax('DELETE', '{server_url}/teams/team/{last_team_id}/delete', {{
                target: '#errors-container',
                swap: 'innerHTML'
            }})
        """)

    response = response_info.value
    assert response.status == 200, f"Expected 200 but got {response.status}"

    # 3. Assert that the error message appears in the errors container
    errors_container = page.locator("#errors-container")
    assert errors_container.count() == 1, "Expected errors container to be present"
    expect(errors_container).to_be_visible()
    expect(errors_container).to_contain_text("Team not found")

