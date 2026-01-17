"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the src directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

# Create a test client
client = TestClient(app)


class TestRootEndpoint:
    """Test the root endpoint"""
    
    def test_root_redirect(self):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestActivitiesEndpoint:
    """Test the activities endpoint"""
    
    def test_get_activities_returns_dict(self):
        """Test that get_activities returns a dictionary"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    def test_get_activities_contains_required_fields(self):
        """Test that activities contain required fields"""
        response = client.get("/activities")
        data = response.json()
        
        # Check that we have some activities
        assert len(data) > 0
        
        # Check that each activity has required fields
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupEndpoint:
    """Test the signup endpoint"""
    
    def test_signup_for_valid_activity(self):
        """Test signing up for a valid activity"""
        response = client.post("/activities/Chess%20Club/signup?email=test@mergington.edu")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@mergington.edu" in data["message"]
    
    def test_signup_for_nonexistent_activity(self):
        """Test signing up for an activity that doesn't exist"""
        response = client.post("/activities/NonexistentActivity/signup?email=test@mergington.edu")
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_duplicate_email(self):
        """Test signing up with an email that's already registered"""
        # First, get the list of activities to find one with participants
        activities_response = client.get("/activities")
        activities = activities_response.json()
        
        # Find an activity with at least one participant
        for activity_name, activity_data in activities.items():
            if activity_data["participants"]:
                existing_email = activity_data["participants"][0]
                # Try to sign up with the same email
                response = client.post(
                    f"/activities/{activity_name.replace(' ', '%20')}/signup?email={existing_email}"
                )
                assert response.status_code == 400
                data = response.json()
                assert "already signed up" in data["detail"]
                break
    
    def test_signup_response_structure(self):
        """Test that signup response has correct structure"""
        response = client.post("/activities/Programming%20Class/signup?email=newstudent@mergington.edu")
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
            assert isinstance(data["message"], str)


class TestActivitiesIntegration:
    """Integration tests for the activities workflow"""
    
    def test_new_participant_appears_in_list(self):
        """Test that a newly signed up participant appears in the activities list"""
        # Get activities before signup
        response_before = client.get("/activities")
        activities_before = response_before.json()
        
        # Pick an activity and count participants
        activity_name = "Tennis"
        if activity_name in activities_before:
            count_before = len(activities_before[activity_name]["participants"])
            
            # Sign up a new student
            test_email = f"integration_test_{count_before}@mergington.edu"
            signup_response = client.post(
                f"/activities/{activity_name.replace(' ', '%20')}/signup?email={test_email}"
            )
            
            if signup_response.status_code == 200:
                # Get activities after signup
                response_after = client.get("/activities")
                activities_after = response_after.json()
                
                # Verify the participant was added
                count_after = len(activities_after[activity_name]["participants"])
                assert count_after == count_before + 1
                assert test_email in activities_after[activity_name]["participants"]
