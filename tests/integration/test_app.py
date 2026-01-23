# test_app.py
import pytest

def test_app_fixture(app):
    """Test that app fixture works"""
    assert app is not None

def test_blueprints_registered(app):
    """Test that all blueprints have routes registered"""
    routes = {rule.endpoint: rule.rule for rule in app.url_map.iter_rules()}
    
    # Check each blueprint has at least one route
    assert any('user.' in endpoint for endpoint in routes), "User blueprint not registered"
    assert any('job.' in endpoint for endpoint in routes), "Job blueprint not registered"
    assert any('teams.' in endpoint for endpoint in routes), "Teams blueprint not registered"
    assert any('properties.' in endpoint for endpoint in routes), "Properties blueprint not registered"
    
    # Check specific important routes exist
    assert 'index' in routes, "Root route not registered"
    assert 'user.login' in routes, "Login route not registered"