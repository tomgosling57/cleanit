def test_app_is_running(page, goto):
    """Test that the application launches and is accessible"""
    goto("/")
    assert page.url is not None
    assert "CleanIt" in page.title()

def test_browser_fixture(browser):
    """Test that browser fixture works"""
    assert browser is not None
