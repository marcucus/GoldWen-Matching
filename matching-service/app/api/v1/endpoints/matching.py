from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.services.matching_service import MatchingService
from app.schemas.matching import (
    DailySelectionResponse, 
    CompatibilityScoreRequest, 
    CompatibilityScoreResponse,
    UserChoiceCreate,
    UserChoiceResponse,
    MatchingRequest,
    MatchingResponse
)
from app.core.config import settings
from app.models.user import User, UserChoice

router = APIRouter()

@router.get("/daily-selection/{user_id}", response_model=DailySelectionResponse)
async def get_daily_selection(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get daily selection of profiles for a user.
    Returns 3-5 highly compatible profiles based on personality matching.
    """
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    matching_service = MatchingService(db)
    candidates = matching_service.get_today_selection(user_id)
    
    # Determine max choices based on subscription
    max_choices = 3 if user.is_premium else 1
    
    return DailySelectionResponse(
        user_id=user_id,
        selection_date=datetime.utcnow(),
        candidates=candidates,
        max_choices_allowed=max_choices
    )

@router.post("/generate-selection/{user_id}", response_model=DailySelectionResponse)
async def generate_new_selection(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Force generate a new daily selection for a user.
    Useful for testing or manual triggers.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    matching_service = MatchingService(db)
    candidates = matching_service.generate_daily_selection(user_id)
    
    max_choices = 3 if user.is_premium else 1
    
    return DailySelectionResponse(
        user_id=user_id,
        selection_date=datetime.utcnow(),
        candidates=candidates,
        max_choices_allowed=max_choices
    )

@router.post("/compatibility-score", response_model=CompatibilityScoreResponse)
async def calculate_compatibility(
    request: CompatibilityScoreRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate compatibility score between two users.
    """
    # Check if both users exist
    user1 = db.query(User).filter(User.id == request.user1_id).first()
    user2 = db.query(User).filter(User.id == request.user2_id).first()
    
    if not user1 or not user2:
        raise HTTPException(status_code=404, detail="One or both users not found")
    
    matching_service = MatchingService(db)
    score = matching_service.calculate_compatibility_score(request.user1_id, request.user2_id)
    
    return CompatibilityScoreResponse(
        user1_id=request.user1_id,
        user2_id=request.user2_id,
        compatibility_score=score,
        calculated_at=datetime.utcnow()
    )

@router.post("/user-choice/{user_id}", response_model=UserChoiceResponse)
async def make_user_choice(
    user_id: int,
    choice: UserChoiceCreate,
    db: Session = Depends(get_db)
):
    """
    Record a user's choice and check for mutual match.
    """
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if chosen user exists
    chosen_user = db.query(User).filter(User.id == choice.chosen_user_id).first()
    if not chosen_user:
        raise HTTPException(status_code=404, detail="Chosen user not found")
    
    # Check daily choice limit
    today = datetime.utcnow().date()
    today_choices = db.query(UserChoice).filter(
        UserChoice.user_id == user_id,
        UserChoice.choice_date >= datetime.combine(today, datetime.min.time())
    ).count()
    
    max_choices = 3 if user.is_premium else 1
    if today_choices >= max_choices:
        raise HTTPException(
            status_code=429, 
            detail=f"Daily choice limit exceeded. You can make {max_choices} choices per day."
        )
    
    # Create user choice
    user_choice = UserChoice(
        user_id=user_id,
        chosen_user_id=choice.chosen_user_id,
        choice_date=datetime.utcnow()
    )
    
    # Check if it's a mutual match
    reverse_choice = db.query(UserChoice).filter(
        UserChoice.user_id == choice.chosen_user_id,
        UserChoice.chosen_user_id == user_id
    ).first()
    
    if reverse_choice:
        user_choice.is_match = True
        reverse_choice.is_match = True
        db.add(reverse_choice)
    
    db.add(user_choice)
    db.commit()
    db.refresh(user_choice)
    
    return UserChoiceResponse(
        id=user_choice.id,
        user_id=user_choice.user_id,
        chosen_user_id=user_choice.chosen_user_id,
        choice_date=user_choice.choice_date,
        is_match=user_choice.is_match
    )

@router.get("/user-choices/{user_id}", response_model=List[UserChoiceResponse])
async def get_user_choices(
    user_id: int,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get user's choice history.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    choices = db.query(UserChoice)\
        .filter(UserChoice.user_id == user_id)\
        .order_by(UserChoice.choice_date.desc())\
        .limit(limit)\
        .all()
    
    return [
        UserChoiceResponse(
            id=choice.id,
            user_id=choice.user_id,
            chosen_user_id=choice.chosen_user_id,
            choice_date=choice.choice_date,
            is_match=choice.is_match
        )
        for choice in choices
    ]

@router.post("/matching-candidates", response_model=MatchingResponse)
async def get_matching_candidates(
    request: MatchingRequest,
    db: Session = Depends(get_db)
):
    """
    Get matching candidates for a user with optional filtering.
    Used by the main API for custom matching requests.
    """
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    matching_service = MatchingService(db)
    
    # Temporarily exclude specified users
    original_excluded = matching_service._get_excluded_user_ids(request.user_id)
    all_excluded = list(set(original_excluded + (request.exclude_user_ids or [])))
    
    # Get potential candidates manually
    candidates = matching_service._get_potential_candidates(user, all_excluded)
    
    # Score and rank candidates
    scored_candidates = []
    for candidate in candidates:
        score = matching_service.calculate_compatibility_score(request.user_id, candidate.id)
        if score >= settings.COMPATIBILITY_THRESHOLD:
            scored_candidates.append((candidate, score))
    
    # Sort and limit
    scored_candidates.sort(key=lambda x: x[1], reverse=True)
    max_results = min(request.max_results or 5, 10)  # Max 10 results
    top_candidates = scored_candidates[:max_results]
    
    # Convert to response format
    result_candidates = []
    for i, (candidate, score) in enumerate(top_candidates):
        result_candidates.append({
            "user_id": candidate.id,
            "first_name": candidate.first_name,
            "age": candidate.age,
            "location_city": candidate.location_city,
            "compatibility_score": score,
            "rank_position": i + 1
        })
    
    return MatchingResponse(
        user_id=request.user_id,
        candidates=result_candidates,
        generated_at=datetime.utcnow()
    )