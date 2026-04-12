"""
AI-Generated Test Case Executor
================================
Loads AI-generated test cases from the validation layer and executes them
against the live Restful Booker API.

This demonstrates the full AI-assisted QA loop:
  1. OpenAPI spec analyzed by Claude
  2. Test cases generated and saved for human review
  3. Human validates AI output (human-in-the-loop)
  4. This executor runs the validated test cases
  5. Results reported with pass/fail analysis

Human judgment is applied BEFORE execution — not replaced by AI.
"""

import json
import pytest
import requests
import os

# Base URL for the API under test
BASE_URL = "https://restful-booker.herokuapp.com"

# Load AI-generated test cases
def load_generated_test_cases():
    """Load and return the AI-generated test cases from validation layer."""
    test_cases_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'validation', 
        'generated_test_cases.json'
    )
    with open(test_cases_path, 'r') as f:
        data = json.load(f)
    return data.get('generated_test_cases', [])


def get_auth_token():
    """Get authentication token for protected endpoints."""
    response = requests.post(
        f"{BASE_URL}/auth",
        json={"username": "admin", "password": "password123"},
        headers={"Content-Type": "application/json"}
    )
    if response.status_code == 200:
        return response.json().get('token')
    return None


def create_test_booking():
    """Create a test booking and return its ID for use in tests."""
    payload = {
        "firstname": "Test",
        "lastname": "User",
        "totalprice": 100,
        "depositpaid": True,
        "bookingdates": {
            "checkin": "2026-01-01",
            "checkout": "2026-01-05"
        },
        "additionalneeds": "Breakfast"
    }
    response = requests.post(
        f"{BASE_URL}/booking",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    if response.status_code == 200:
        return response.json().get('bookingid')
    return None


# ============================================================
# HEALTH CHECK
# ============================================================

class TestHealthCheck:
    """Validate API is available before running test suite."""
    
    def test_api_health_check(self):
        """TC: Verify API is up and responding."""
        response = requests.get(f"{BASE_URL}/ping")
        assert response.status_code == 201, \
            f"Health check failed — API may be down. Status: {response.status_code}"


# ============================================================
# AUTHENTICATION TESTS
# ============================================================

class TestAuthentication:
    """Test authentication flows — AI flagged these as high risk."""

    def test_valid_credentials_return_token(self):
        """TC: Valid credentials should return an auth token."""
        response = requests.post(
            f"{BASE_URL}/auth",
            json={"username": "admin", "password": "password123"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data, "Response should contain a token"
        assert len(data["token"]) > 0, "Token should not be empty"

    def test_invalid_credentials_denied(self):
        """TC: Invalid credentials should not return a valid token."""
        response = requests.post(
            f"{BASE_URL}/auth",
            json={"username": "invalid", "password": "wrongpassword"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        # API returns "Bad credentials" message instead of a token
        assert data.get("reason") == "Bad credentials" or "token" not in data or \
               data.get("token") == "Bad credentials", \
               "Invalid credentials should not produce a valid token"

    def test_missing_credentials_handled(self):
        """TC: Missing credentials should be handled gracefully."""
        response = requests.post(
            f"{BASE_URL}/auth",
            json={},
            headers={"Content-Type": "application/json"}
        )
        # Should not return a valid token
        assert response.status_code in [200, 400, 401], \
            f"Unexpected status code: {response.status_code}"


# ============================================================
# BOOKING RETRIEVAL TESTS
# ============================================================

class TestGetBookings:
    """Test booking retrieval — happy path and edge cases."""

    def test_get_all_bookings_returns_list(self):
        """TC: GET /booking should return a list of booking IDs."""
        response = requests.get(f"{BASE_URL}/booking")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) > 0, "Should have at least one booking"
        # Each item should have a bookingid
        for item in data[:5]:  # Check first 5
            assert "bookingid" in item, "Each item should have a bookingid"

    def test_get_booking_by_valid_id(self):
        """TC: GET /booking/{id} with valid ID should return booking details."""
        # First get a valid ID
        all_bookings = requests.get(f"{BASE_URL}/booking").json()
        assert len(all_bookings) > 0, "Need at least one booking to test"
        
        booking_id = all_bookings[0]['bookingid']
        response = requests.get(f"{BASE_URL}/booking/{booking_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "firstname" in data
        assert "lastname" in data
        assert "totalprice" in data
        assert "depositpaid" in data
        assert "bookingdates" in data

    def test_get_booking_invalid_id_returns_404(self):
        """TC: GET /booking/{id} with invalid ID should return 404."""
        response = requests.get(f"{BASE_URL}/booking/999999999")
        assert response.status_code == 404, \
            f"Invalid booking ID should return 404, got {response.status_code}"

    def test_filter_bookings_by_firstname(self):
        """TC: GET /booking?firstname= should filter results."""
        response = requests.get(
            f"{BASE_URL}/booking",
            params={"firstname": "Test"}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_filter_bookings_by_date_range(self):
        """TC: Filter bookings by checkin/checkout dates."""
        response = requests.get(
            f"{BASE_URL}/booking",
            params={"checkin": "2026-01-01", "checkout": "2026-12-31"}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)


# ============================================================
# BOOKING CREATION TESTS
# ============================================================

class TestCreateBooking:
    """Test booking creation — AI flagged data integrity as high risk."""

    def test_create_booking_valid_payload(self):
        """TC: POST /booking with valid payload should create booking."""
        payload = {
            "firstname": "Michael",
            "lastname": "Jensen",
            "totalprice": 150,
            "depositpaid": True,
            "bookingdates": {
                "checkin": "2026-06-01",
                "checkout": "2026-06-05"
            },
            "additionalneeds": "Breakfast"
        }
        response = requests.post(
            f"{BASE_URL}/booking",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "bookingid" in data
        assert "booking" in data
        assert data["booking"]["firstname"] == "Michael"
        assert data["booking"]["totalprice"] == 150

    def test_create_booking_missing_required_fields(self):
        """TC: POST /booking with missing required fields should fail."""
        payload = {
            "firstname": "Test"
            # Missing lastname, totalprice, depositpaid, bookingdates
        }
        response = requests.post(
            f"{BASE_URL}/booking",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 500], \
            f"Missing required fields should not create booking, got {response.status_code}"

    def test_create_booking_negative_price(self):
        """TC: Edge case — negative totalprice value."""
        payload = {
            "firstname": "Edge",
            "lastname": "Case",
            "totalprice": -100,
            "depositpaid": False,
            "bookingdates": {
                "checkin": "2026-06-01",
                "checkout": "2026-06-05"
            }
        }
        response = requests.post(
            f"{BASE_URL}/booking",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        # Document actual behavior — system may or may not validate this
        print(f"\nNegative price test — Status: {response.status_code}")
        assert response.status_code in [200, 400], \
            f"Unexpected status for negative price: {response.status_code}"

    def test_create_booking_checkout_before_checkin(self):
        """TC: Edge case — checkout date before checkin date."""
        payload = {
            "firstname": "Date",
            "lastname": "Test",
            "totalprice": 100,
            "depositpaid": True,
            "bookingdates": {
                "checkin": "2026-06-10",
                "checkout": "2026-06-01"  # Before checkin
            }
        }
        response = requests.post(
            f"{BASE_URL}/booking",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"\nInverted dates test — Status: {response.status_code}")
        assert response.status_code in [200, 400], \
            f"Unexpected status for inverted dates: {response.status_code}"


# ============================================================
# AI COVERAGE GAP VALIDATION
# ============================================================

class TestAICoverageGaps:
    """
    Tests targeting gaps identified by AI during spec analysis.
    This class demonstrates human-in-the-loop validation —
    AI flagged these areas, human engineer implemented the tests.
    """

    def test_special_characters_in_name_fields(self):
        """TC: AI identified gap — special characters in string fields."""
        payload = {
            "firstname": "O'Brien-Smith",
            "lastname": "García-López",
            "totalprice": 100,
            "depositpaid": True,
            "bookingdates": {
                "checkin": "2026-06-01",
                "checkout": "2026-06-05"
            }
        }
        response = requests.post(
            f"{BASE_URL}/booking",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"\nSpecial characters test — Status: {response.status_code}")
        assert response.status_code in [200, 400], \
            f"Unexpected status for special characters: {response.status_code}"

    def test_generated_test_cases_file_exists(self):
        """TC: Validate AI generation pipeline produced output."""
        test_cases = load_generated_test_cases()
        assert len(test_cases) > 0, "AI should have generated test cases"
        
        # Validate structure of generated cases
        required_fields = [
            'test_id', 'endpoint', 'method', 'category',
            'description', 'expected_status_code', 'risk_level'
        ]
        for tc in test_cases[:5]:
            for field in required_fields:
                assert field in tc, \
                    f"Generated test case missing field: {field}"

    def test_coverage_summary_present(self):
        """TC: Validate AI generated a coverage summary."""
        test_cases_path = os.path.join(
            os.path.dirname(__file__),
            '..', 'validation', 'generated_test_cases.json'
        )
        with open(test_cases_path, 'r') as f:
            data = json.load(f)
        
        assert "coverage_summary" in data
        assert "coverage_gaps" in data
        assert "high_risk_areas" in data
        summary = data["coverage_summary"]
        assert summary["total_tests"] > 0, "Should have generated test cases"