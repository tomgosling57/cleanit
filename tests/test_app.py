import pytest


def test_app_is_running(page):
    """Test that the application launches and is accessible"""
    page.goto("/")
    assert page.url is not None