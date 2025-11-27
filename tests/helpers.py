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
    page.get_by_role("textbox", name="password").fill("ownerpassword")
    page.get_by_role("button", name="Login").click()