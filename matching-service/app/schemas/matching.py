from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class UserBase(BaseModel):
    email: str
    first_name: str
    age: int
    gender: str
    location_city: str
    location_latitude: Optional[float] = None
    location_longitude: Optional[float] = None

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    is_premium: bool = False
    is_active: bool = True
    created_at: datetime
    
    class Config:
        orm_mode = True

class PersonalityResponseBase(BaseModel):
    question_id: int
    response_value: int

class PersonalityResponseCreate(PersonalityResponseBase):
    pass

class PersonalityResponse(PersonalityResponseBase):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        orm_mode = True

class PersonalityQuestionnaireCreate(BaseModel):
    responses: List[PersonalityResponseCreate]

class DailySelectionCandidate(BaseModel):
    user_id: int
    first_name: str
    age: int
    location_city: str
    compatibility_score: float
    rank_position: int
    
    class Config:
        orm_mode = True

class DailySelectionResponse(BaseModel):
    user_id: int
    selection_date: datetime
    candidates: List[DailySelectionCandidate]
    max_choices_allowed: int  # 1 for free users, 3 for premium

class UserChoiceCreate(BaseModel):
    chosen_user_id: int

class UserChoiceResponse(BaseModel):
    id: int
    user_id: int
    chosen_user_id: int
    choice_date: datetime
    is_match: bool
    
    class Config:
        orm_mode = True

class CompatibilityScoreRequest(BaseModel):
    user1_id: int
    user2_id: int

class CompatibilityScoreResponse(BaseModel):
    user1_id: int
    user2_id: int
    compatibility_score: float
    calculated_at: datetime

class MatchingRequest(BaseModel):
    user_id: int
    exclude_user_ids: Optional[List[int]] = []
    max_results: Optional[int] = 5

class MatchingResponse(BaseModel):
    user_id: int
    candidates: List[DailySelectionCandidate]
    generated_at: datetime