from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from datetime import datetime
from typing import Optional

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)  # "male", "female", "non-binary"
    location_city = Column(String, nullable=False)
    location_latitude = Column(Float, nullable=True)
    location_longitude = Column(Float, nullable=True)
    is_premium = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    personality_responses = relationship("PersonalityResponse", back_populates="user")
    daily_selections = relationship("DailySelection", foreign_keys="DailySelection.user_id", back_populates="user")
    user_choices = relationship("UserChoice", back_populates="user")

class PersonalityResponse(Base):
    __tablename__ = "personality_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, nullable=False)  # 1-10 for the 10 personality questions
    response_value = Column(Integer, nullable=False)  # 1-5 scale typically
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationship
    user = relationship("User", back_populates="personality_responses")

class DailySelection(Base):
    __tablename__ = "daily_selections"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    candidate_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    compatibility_score = Column(Float, nullable=False)
    selection_date = Column(DateTime, nullable=False)
    rank_position = Column(Integer, nullable=False)  # 1-5 ranking in daily selection
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="daily_selections")
    candidate = relationship("User", foreign_keys=[candidate_user_id])

class UserChoice(Base):
    __tablename__ = "user_choices"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    chosen_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    choice_date = Column(DateTime, nullable=False)
    is_match = Column(Boolean, default=False)  # True if both users chose each other
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationship
    user = relationship("User", back_populates="user_choices")
    chosen_user = relationship("User", foreign_keys=[chosen_user_id])

class CompatibilityCache(Base):
    __tablename__ = "compatibility_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user2_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    compatibility_score = Column(Float, nullable=False)
    calculated_at = Column(DateTime, server_default=func.now())
    
    # Ensure user1_id < user2_id for consistency
    def __init__(self, user1_id: int, user2_id: int, compatibility_score: float):
        if user1_id > user2_id:
            user1_id, user2_id = user2_id, user1_id
        self.user1_id = user1_id
        self.user2_id = user2_id
        self.compatibility_score = compatibility_score