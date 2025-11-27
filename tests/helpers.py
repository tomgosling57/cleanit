# tests/helpers.py
def login_owner(page, goto) -> None:
    """
    Executes the login flow for the owner.

    Args:
        page: The page pytest-playwright fixture representing the current browser page.
        goto: A fixture to navigate to a specified URL.

    Returns:
        None
    """
    goto("/")                               
    page.get_by_role("textbox", name="email").click()
    page.get_by_role("textbox", name="email").fill("owner@example.com")
    page.get_by_role("textbox", name="password").click()
    page.get_by_role("textbox", name="password").fill("owner_password")
    page.get_by_role("button", name="Login").click()

def login_team_leader(page, goto) -> None:
    """
    Executes the login flow for the team leader.

    Args:
        page: The page pytest-playwright fixture representing the current browser page.
        goto: A fixture to navigate to a specified URL.

    Returns:
        None
    """
    goto("/")                               
    page.get_by_role("textbox", name="email").click()
    page.get_by_role("textbox", name="email").fill("team_leader@example.com")
    page.get_by_role("textbox", name="password").click()
    page.get_by_role("textbox", name="password").fill("team_leader_password")
    page.get_by_role("button", name="Login").click()

def login_cleaner(page, goto) -> None:
    """
    Executes the login flow for the cleaner.

    Args:
        page: The page pytest-playwright fixture representing the current browser page.
        goto: A fixture to navigate to a specified URL.
    
    Returns:
        None
    """
    goto("/")                               
    page.get_by_role("textbox", name="email").click()
    page.get_by_role("textbox", name="email").fill("cleaner@example.com")
    page.get_by_role("textbox", name="password").click()
    page.get_by_role("textbox", name="password").fill("cleaner_password")
    page.get_by_role("button", name="Login").click()