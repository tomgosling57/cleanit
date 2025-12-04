from tests.helpers import login_owner
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

