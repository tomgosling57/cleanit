from tests.helpers import login_owner, wait_for_modal
from playwright.sync_api import expect

def _navigate_to_teams_page(page) -> None:
    # Navigate to the teams page
    page.get_by_text("Teams").click()
    # Wait for the teams grid to be visible
    teams_grid = page.locator(".teams-grid")
    expect(teams_grid).to_be_visible()

def test_team_cards(page, goto) -> None:
    login_owner(page, goto)
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
#     login_owner(page, goto)
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
    login_owner(page, goto)
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
    old_team.locator(".edit-team-icon").click()
    modal = wait_for_modal(page, "#team-modal")
    expect(modal.locator("form")).to_have_attribute("data-team-leader-id", "None")

