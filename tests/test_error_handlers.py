"""
Tests for error handlers in the CleanIt application.
Focuses on 404 page functionality and authentication handler dominance.
"""

import pytest
from flask import url_for


class TestErrorHandlers:
    """Test error handlers for 404 and authentication scenarios."""
    
    def test_unauthorized_request_to_nonexistent_route(self, app):
        """
        Test that unauthorized requests to non-existent routes redirect to login.
        
        Expectation: When an unauthenticated user requests a non-existent route,
        they should be redirected to the login page (not shown a 404 page).
        This tests that the authentication handler has dominance over the 404 handler.
        """
        with app.test_client() as client:
            # Make a request to a non-existent route without authentication
            response = client.get('/nonexistent-route-that-does-not-exist', follow_redirects=False)
            
            # Should redirect to login page (not show 404)
            assert response.status_code in [302, 401], f"Expected 302 redirect or 401, got {response.status_code}"
            
            # If it's a redirect, check it goes to login
            if response.status_code == 302:
                # The login URL should be in the Location header
                assert '/users/user/login' in response.location or '/login' in response.location
            elif response.status_code == 401:
                # Some endpoints might return 401 directly for API requests
                # This is also acceptable as it's not a 404
                pass
    
    def test_authorized_request_to_nonexistent_route(self, admin_client_no_csrf):
        """
        Test that authorized requests to non-existent routes show the 404 template.
        
        Expectation: When an authenticated user requests a non-existent route,
        they should see the 404 page (not_found.html template).
        """
        # Make a request to a non-existent route with authentication
        response = admin_client_no_csrf.get('/nonexistent-route-that-does-not-exist')
        
        # Should return 404 status
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        
        # Should contain elements from the not_found.html template
        assert b'Page Not Found' in response.data
        assert b'404' in response.data
        assert b'Go to Timetable' in response.data
    
    def test_media_not_found_error_handler(self, admin_client_no_csrf):
        """
        Test that MediaNotFound exceptions are handled by the specialized handler.
        """
        # Request a non-existent media ID (should trigger MediaNotFound exception)
        response = admin_client_no_csrf.get(
            '/media/999999',
            headers={'Accept': 'application/json'}
        )
        
        # Should return 404 status
        assert response.status_code == 404
        
        # Should return JSON for API requests
        assert response.content_type == 'application/json'
        
        # Should contain media-specific error message
        import json
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Media not found' in data.get('error', '')
    
    def test_authenticated_user_can_access_protected_route(self, admin_client_no_csrf):
        """
        Test that authenticated users can access protected routes without redirect.
        This ensures the authentication system is working correctly alongside error handling.
        """
        # Access a protected route (timetable requires authentication)
        response = admin_client_no_csrf.get('/jobs/timetable')
        
        # Should return 200 (or whatever the actual status is for timetable)
        # Not a redirect to login
        assert response.status_code != 302, "Authenticated user should not be redirected to login"
        assert response.status_code != 401, "Authenticated user should not get 401"
    
    def test_unauthenticated_user_redirected_from_protected_route(self, app):
        """
        Test that unauthenticated users are redirected from protected routes.
        """
        with app.test_client() as client:
            # Access a protected route without authentication
            response = client.get('/jobs/timetable', follow_redirects=False)
            
            # Should redirect to login
            assert response.status_code == 302
            assert '/users/user/login' in response.location