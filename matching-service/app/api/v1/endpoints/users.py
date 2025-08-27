from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.matching import (
    User, 
    UserCreate, 
    PersonalityQuestionnaireCreate, 
    PersonalityResponse
)
from app.models.user import User as UserModel, PersonalityResponse as PersonalityResponseModel

router = APIRouter()

@router.post("/", response_model=User)
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new user.
    This endpoint is typically called by the main NestJS API.
    """
    # Check if user already exists
    existing_user = db.query(UserModel).filter(UserModel.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    db_user = UserModel(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return User.model_validate(db_user)

@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get user by ID.
    """
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return User.model_validate(user)

@router.post("/{user_id}/personality", response_model=List[PersonalityResponse])
async def submit_personality_questionnaire(
    user_id: int,
    questionnaire: PersonalityQuestionnaireCreate,
    db: Session = Depends(get_db)
):
    """
    Submit personality questionnaire responses for a user.
    This is required before the user can receive matches.
    """
    # Check if user exists
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate questionnaire completeness
    if len(questionnaire.responses) != 10:  # Based on specs: 10 personality questions
        raise HTTPException(
            status_code=400, 
            detail="Personality questionnaire must have exactly 10 responses"
        )
    
    # Remove existing responses
    db.query(PersonalityResponseModel)\
        .filter(PersonalityResponseModel.user_id == user_id)\
        .delete()
    
    # Add new responses
    db_responses = []
    for response in questionnaire.responses:
        if not (1 <= response.question_id <= 10):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid question_id: {response.question_id}. Must be between 1 and 10."
            )
        
        if not (1 <= response.response_value <= 5):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid response_value: {response.response_value}. Must be between 1 and 5."
            )
        
        db_response = PersonalityResponseModel(
            user_id=user_id,
            question_id=response.question_id,
            response_value=response.response_value
        )
        db.add(db_response)
        db_responses.append(db_response)
    
    db.commit()
    
    # Refresh all responses
    for response in db_responses:
        db.refresh(response)
    
    return [PersonalityResponse.model_validate(response) for response in db_responses]

@router.get("/{user_id}/personality", response_model=List[PersonalityResponse])
async def get_personality_responses(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get personality questionnaire responses for a user.
    """
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    responses = db.query(PersonalityResponseModel)\
        .filter(PersonalityResponseModel.user_id == user_id)\
        .order_by(PersonalityResponseModel.question_id)\
        .all()
    
    return [PersonalityResponse.model_validate(response) for response in responses]

@router.put("/{user_id}/premium", response_model=User)
async def update_premium_status(
    user_id: int,
    is_premium: bool,
    db: Session = Depends(get_db)
):
    """
    Update user's premium subscription status.
    Called by the main API when subscription status changes.
    """
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_premium = is_premium
    db.commit()
    db.refresh(user)
    
    return User.model_validate(user)

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a user and all associated data.
    Used for GDPR compliance and account deletion.
    """
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete associated data (cascade should handle this, but being explicit)
    db.query(PersonalityResponseModel)\
        .filter(PersonalityResponseModel.user_id == user_id)\
        .delete()
    
    # Delete user
    db.delete(user)
    db.commit()
    
    return {"message": f"User {user_id} deleted successfully"}