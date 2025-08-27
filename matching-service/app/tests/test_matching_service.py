import pytest
from app.services.matching_service import MatchingService
from app.models.user import User, PersonalityResponse

def test_calculate_compatibility_score(db_session):
    """Test compatibility score calculation between users."""
    # Create two users
    user1 = User(
        email="user1@example.com",
        first_name="Alice",
        age=25,
        gender="female",
        location_city="Paris"
    )
    user2 = User(
        email="user2@example.com",
        first_name="Bob",
        age=27,
        gender="male",
        location_city="Lyon"
    )
    db_session.add(user1)
    db_session.add(user2)
    db_session.commit()
    db_session.refresh(user1)
    db_session.refresh(user2)
    
    # Add similar personality responses for high compatibility
    for i in range(1, 11):
        response1 = PersonalityResponse(user_id=user1.id, question_id=i, response_value=3)
        response2 = PersonalityResponse(user_id=user2.id, question_id=i, response_value=3)
        db_session.add(response1)
        db_session.add(response2)
    db_session.commit()
    
    # Test compatibility calculation
    matching_service = MatchingService(db_session)
    score = matching_service.calculate_compatibility_score(user1.id, user2.id)
    
    # Should be 1.0 (perfect match) since all responses are identical
    assert score == 1.0

def test_calculate_compatibility_score_different_responses(db_session):
    """Test compatibility score with different personality responses."""
    # Create two users
    user1 = User(
        email="user1@example.com",
        first_name="Alice",
        age=25,
        gender="female",
        location_city="Paris"
    )
    user2 = User(
        email="user2@example.com",
        first_name="Bob",
        age=27,
        gender="male",
        location_city="Lyon"
    )
    db_session.add(user1)
    db_session.add(user2)
    db_session.commit()
    db_session.refresh(user1)
    db_session.refresh(user2)
    
    # Add completely different personality responses
    for i in range(1, 11):
        response1 = PersonalityResponse(user_id=user1.id, question_id=i, response_value=1)
        response2 = PersonalityResponse(user_id=user2.id, question_id=i, response_value=5)
        db_session.add(response1)
        db_session.add(response2)
    db_session.commit()
    
    # Test compatibility calculation
    matching_service = MatchingService(db_session)
    score = matching_service.calculate_compatibility_score(user1.id, user2.id)
    
    # Should be low compatibility
    assert 0.0 <= score <= 1.0
    assert score < 0.5  # Should be quite low for opposite responses

def test_generate_daily_selection(db_session):
    """Test daily selection generation."""
    # Create main user
    main_user = User(
        email="main@example.com",
        first_name="Main",
        age=25,
        gender="female",
        location_city="Paris",
        is_premium=False
    )
    db_session.add(main_user)
    db_session.commit()
    db_session.refresh(main_user)
    
    # Add personality responses for main user
    for i in range(1, 11):
        response = PersonalityResponse(user_id=main_user.id, question_id=i, response_value=3)
        db_session.add(response)
    
    # Create candidate users
    candidates = []
    for j in range(5):
        candidate = User(
            email=f"candidate{j}@example.com",
            first_name=f"Candidate{j}",
            age=25 + j,
            gender="male",
            location_city="Paris"
        )
        db_session.add(candidate)
        db_session.commit()
        db_session.refresh(candidate)
        candidates.append(candidate)
        
        # Add personality responses (varying similarity)
        for i in range(1, 11):
            response_value = 3 if j < 3 else (j % 5) + 1  # First 3 are more similar
            response = PersonalityResponse(
                user_id=candidate.id, 
                question_id=i, 
                response_value=response_value
            )
            db_session.add(response)
    
    db_session.commit()
    
    # Test daily selection generation
    matching_service = MatchingService(db_session)
    selection = matching_service.generate_daily_selection(main_user.id)
    
    # Should return candidates
    assert len(selection) > 0
    assert len(selection) <= 5  # Max 5 candidates
    
    # Should be sorted by compatibility score (descending)
    for i in range(1, len(selection)):
        assert selection[i-1].compatibility_score >= selection[i].compatibility_score

def test_cosine_similarity(db_session):
    """Test cosine similarity calculation."""
    matching_service = MatchingService(db_session)
    
    # Test identical vectors
    vec1 = [1, 2, 3, 4, 5]
    vec2 = [1, 2, 3, 4, 5]
    similarity = matching_service._cosine_similarity(vec1, vec2)
    assert similarity == 1.0
    
    # Test orthogonal vectors
    vec3 = [1, 0]
    vec4 = [0, 1]
    similarity = matching_service._cosine_similarity(vec3, vec4)
    assert similarity == 0.0
    
    # Test opposite vectors
    vec5 = [1, 1, 1]
    vec6 = [-1, -1, -1]
    similarity = matching_service._cosine_similarity(vec5, vec6)
    assert similarity == -1.0