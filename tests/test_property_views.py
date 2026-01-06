from flask import url_for
from playwright.sync_api import expect
from datetime import datetime, time, timedelta

import pytest
from config import DATETIME_FORMATS
from tests.helpers import get_first_property_card, login_admin, open_address_book, open_property_details


def test_edit_property_notes(page, live_server, goto, role):
    """Test editing property notes functionality."""
    login_admin(page, goto)    
    # Navigate to address book and open a property
    open_address_book(page)
    property_card = get_first_property_card(page)
    open_property_details(page, property_card) 