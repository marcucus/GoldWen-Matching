import pytest
from fastapi.testclient import TestClient

def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "goldwen-matching-service"

def test_create_user(client):
    """Test user creation endpoint."""
    user_data = {
        "email": "test@example.com",
        "first_name": "John",
        "age": 25,
        "gender": "male",
        "location_city": "Paris",
        "location_latitude": 48.8566,
        "location_longitude": 2.3522
    }
    
    response = client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["first_name"] == user_data["first_name"]
    assert data["age"] == user_data["age"]
    assert data["is_premium"] is False

def test_create_duplicate_user(client):
    """Test creating a user with duplicate email."""
    user_data = {
        "email": "test@example.com",
        "first_name": "John",
        "age": 25,
        "gender": "male",
        "location_city": "Paris"
    }
    
    # Create first user
    response1 = client.post("/api/v1/users/", json=user_data)
    assert response1.status_code == 200
    
    # Try to create duplicate
    response2 = client.post("/api/v1/users/", json=user_data)
    assert response2.status_code == 400
    assert "User already exists" in response2.json()["detail"]

def test_submit_personality_questionnaire(client):
    """Test personality questionnaire submission."""
    # First create a user
    user_data = {
        "email": "test@example.com",
        "first_name": "John",
        "age": 25,
        "gender": "male",
        "location_city": "Paris"
    }
    user_response = client.post("/api/v1/users/", json=user_data)
    user_id = user_response.json()["id"]
    
    # Submit personality questionnaire
    questionnaire_data = {
        "responses": [
            {"question_id": i, "response_value": (i % 5) + 1}
            for i in range(1, 11)
        ]
    }
    
    response = client.post(f"/api/v1/users/{user_id}/personality", json=questionnaire_data)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 10  # Should have 10 responses
    assert all(r["user_id"] == user_id for r in data)

def test_invalid_personality_questionnaire(client):
    """Test personality questionnaire with invalid data."""
    # First create a user
    user_data = {
        "email": "test@example.com",
        "first_name": "John",
        "age": 25,
        "gender": "male",
        "location_city": "Paris"
    }
    user_response = client.post("/api/v1/users/", json=user_data)
    user_id = user_response.json()["id"]
    
    # Submit incomplete questionnaire (only 5 responses instead of 10)
    questionnaire_data = {
        "responses": [
            {"question_id": i, "response_value": 3}
            for i in range(1, 6)
        ]
    }
    
    response = client.post(f"/api/v1/users/{user_id}/personality", json=questionnaire_data)
    assert response.status_code == 400
    assert "exactly 10 responses" in response.json()["detail"]

def test_get_daily_selection_without_personality(client):
    """Test getting daily selection for user without personality responses."""
    # Create a user
    user_data = {
        "email": "test@example.com",
        "first_name": "John",
        "age": 25,
        "gender": "male",
        "location_city": "Paris"
    }
    user_response = client.post("/api/v1/users/", json=user_data)
    user_id = user_response.json()["id"]
    
    # Try to get daily selection without personality responses
    response = client.get(f"/api/v1/matching/daily-selection/{user_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["user_id"] == user_id
    assert len(data["candidates"]) == 0  # Should be empty without personality data

def test_compatibility_score_calculation(client):
    """Test compatibility score calculation between users."""
    # Create two users
    user1_data = {
        "email": "user1@example.com",
        "first_name": "Alice",
        "age": 25,
        "gender": "female",
        "location_city": "Paris"
    }
    user2_data = {
        "email": "user2@example.com",
        "first_name": "Bob",
        "age": 27,
        "gender": "male",
        "location_city": "Lyon"
    }
    
    user1_response = client.post("/api/v1/users/", json=user1_data)
    user2_response = client.post("/api/v1/users/", json=user2_data)
    
    user1_id = user1_response.json()["id"]
    user2_id = user2_response.json()["id"]
    
    # Add personality responses for both users
    questionnaire_data = {
        "responses": [
            {"question_id": i, "response_value": 3}
            for i in range(1, 11)
        ]
    }
    
    client.post(f"/api/v1/users/{user1_id}/personality", json=questionnaire_data)
    client.post(f"/api/v1/users/{user2_id}/personality", json=questionnaire_data)
    
    # Calculate compatibility score
    compatibility_request = {
        "user1_id": user1_id,
        "user2_id": user2_id
    }
    
    response = client.post("/api/v1/matching/compatibility-score", json=compatibility_request)
    assert response.status_code == 200
    
    data = response.json()
    assert data["user1_id"] == user1_id
    assert data["user2_id"] == user2_id
    assert 0.0 <= data["compatibility_score"] <= 1.0