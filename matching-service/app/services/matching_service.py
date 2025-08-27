import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_, not_, func
from typing import List, Tuple, Optional
from datetime import datetime, timedelta
import math

from app.models.user import User, PersonalityResponse, DailySelection, UserChoice, CompatibilityCache
from app.schemas.matching import DailySelectionCandidate
from app.core.config import settings

class MatchingService:
    """
    Content-based matching service for GoldWen MVP.
    Implements personality-based compatibility scoring.
    """
    
    def __init__(self, db: Session):
        self.db = db
        
    def calculate_compatibility_score(self, user1_id: int, user2_id: int) -> float:
        """
        Calculate compatibility score between two users based on personality responses.
        Uses cosine similarity on personality question responses.
        """
        # Check cache first
        cached_score = self._get_cached_compatibility(user1_id, user2_id)
        if cached_score is not None:
            return cached_score
        
        # Get personality responses for both users
        user1_responses = self._get_personality_vector(user1_id)
        user2_responses = self._get_personality_vector(user2_id)
        
        if not user1_responses or not user2_responses:
            return 0.0
        
        # Calculate cosine similarity
        score = self._cosine_similarity(user1_responses, user2_responses)
        
        # Cache the result
        self._cache_compatibility(user1_id, user2_id, score)
        
        return score
    
    def _get_personality_vector(self, user_id: int) -> Optional[List[float]]:
        """Get personality response vector for a user."""
        responses = self.db.query(PersonalityResponse)\
            .filter(PersonalityResponse.user_id == user_id)\
            .order_by(PersonalityResponse.question_id)\
            .all()
        
        if len(responses) != settings.PERSONALITY_QUESTIONS_COUNT:
            return None
        
        return [float(r.response_value) for r in responses]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            return 0.0
        
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def _get_cached_compatibility(self, user1_id: int, user2_id: int) -> Optional[float]:
        """Get cached compatibility score if it exists and is recent."""
        # Ensure consistent ordering
        if user1_id > user2_id:
            user1_id, user2_id = user2_id, user1_id
        
        # Check for cache entry from last 24 hours
        cache_cutoff = datetime.utcnow() - timedelta(hours=24)
        cached = self.db.query(CompatibilityCache)\
            .filter(
                and_(
                    CompatibilityCache.user1_id == user1_id,
                    CompatibilityCache.user2_id == user2_id,
                    CompatibilityCache.calculated_at > cache_cutoff
                )
            ).first()
        
        return cached.compatibility_score if cached else None
    
    def _cache_compatibility(self, user1_id: int, user2_id: int, score: float):
        """Cache compatibility score."""
        # Ensure consistent ordering
        if user1_id > user2_id:
            user1_id, user2_id = user2_id, user1_id
        
        # Remove old cache entry if exists
        self.db.query(CompatibilityCache)\
            .filter(
                and_(
                    CompatibilityCache.user1_id == user1_id,
                    CompatibilityCache.user2_id == user2_id
                )
            ).delete()
        
        # Add new cache entry
        cache_entry = CompatibilityCache(
            user1_id=user1_id,
            user2_id=user2_id,
            compatibility_score=score
        )
        self.db.add(cache_entry)
        self.db.commit()
    
    def generate_daily_selection(self, user_id: int) -> List[DailySelectionCandidate]:
        """
        Generate daily selection for a user.
        Returns 3-5 highly compatible profiles.
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        # Get excluded user IDs (already chosen, matched, or in recent selections)
        excluded_ids = self._get_excluded_user_ids(user_id)
        
        # Get potential candidates
        candidates = self._get_potential_candidates(user, excluded_ids)
        
        # Calculate compatibility scores and rank
        scored_candidates = []
        for candidate in candidates:
            score = self.calculate_compatibility_score(user_id, candidate.id)
            if score >= settings.COMPATIBILITY_THRESHOLD:
                scored_candidates.append((candidate, score))
        
        # Sort by score descending and take top candidates
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        top_candidates = scored_candidates[:settings.MAX_DAILY_PROFILES]
        
        # Ensure minimum number of profiles
        if len(top_candidates) < settings.MIN_DAILY_PROFILES and len(scored_candidates) >= settings.MIN_DAILY_PROFILES:
            top_candidates = scored_candidates[:settings.MIN_DAILY_PROFILES]
        
        # Convert to response format
        selection_candidates = []
        for i, (candidate, score) in enumerate(top_candidates):
            selection_candidates.append(
                DailySelectionCandidate(
                    user_id=candidate.id,
                    first_name=candidate.first_name,
                    age=candidate.age,
                    location_city=candidate.location_city,
                    compatibility_score=score,
                    rank_position=i + 1
                )
            )
        
        # Store the selection in database
        self._store_daily_selection(user_id, selection_candidates)
        
        return selection_candidates
    
    def _get_excluded_user_ids(self, user_id: int) -> List[int]:
        """Get list of user IDs to exclude from matching."""
        excluded_ids = [user_id]  # Exclude self
        
        # Exclude users already chosen in last 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        chosen_users = self.db.query(UserChoice.chosen_user_id)\
            .filter(
                and_(
                    UserChoice.user_id == user_id,
                    UserChoice.choice_date > cutoff_date
                )
            ).all()
        excluded_ids.extend([choice.chosen_user_id for choice in chosen_users])
        
        # Exclude users from recent daily selections (last 7 days)
        recent_selections = self.db.query(DailySelection.candidate_user_id)\
            .filter(
                and_(
                    DailySelection.user_id == user_id,
                    DailySelection.selection_date > datetime.utcnow() - timedelta(days=7)
                )
            ).all()
        excluded_ids.extend([selection.candidate_user_id for selection in recent_selections])
        
        return list(set(excluded_ids))
    
    def _get_potential_candidates(self, user: User, excluded_ids: List[int]) -> List[User]:
        """Get potential candidates for matching."""
        # Basic filtering criteria
        query = self.db.query(User)\
            .filter(
                and_(
                    User.id.notin_(excluded_ids),
                    User.is_active == True,
                    User.gender != user.gender,  # Opposite gender for MVP
                    func.abs(User.age - user.age) <= 10  # Age range ±10 years
                )
            )
        
        # Location-based filtering (within reasonable distance)
        if user.location_latitude and user.location_longitude:
            # Simple distance filtering - can be improved with proper geospatial queries
            query = query.filter(
                and_(
                    User.location_latitude.isnot(None),
                    User.location_longitude.isnot(None)
                )
            )
        
        return query.limit(50).all()  # Limit to 50 for performance
    
    def _store_daily_selection(self, user_id: int, candidates: List[DailySelectionCandidate]):
        """Store daily selection in database."""
        selection_date = datetime.utcnow().replace(hour=12, minute=0, second=0, microsecond=0)
        
        # Remove any existing selection for today
        self.db.query(DailySelection)\
            .filter(
                and_(
                    DailySelection.user_id == user_id,
                    func.date(DailySelection.selection_date) == selection_date.date()
                )
            ).delete()
        
        # Add new selections
        for candidate in candidates:
            selection = DailySelection(
                user_id=user_id,
                candidate_user_id=candidate.user_id,
                compatibility_score=candidate.compatibility_score,
                selection_date=selection_date,
                rank_position=candidate.rank_position
            )
            self.db.add(selection)
        
        self.db.commit()
    
    def get_today_selection(self, user_id: int) -> List[DailySelectionCandidate]:
        """Get today's selection for a user."""
        today = datetime.utcnow().date()
        
        selections = self.db.query(DailySelection)\
            .filter(
                and_(
                    DailySelection.user_id == user_id,
                    func.date(DailySelection.selection_date) == today
                )
            )\
            .order_by(DailySelection.rank_position)\
            .all()
        
        if not selections:
            # Generate new selection if none exists
            return self.generate_daily_selection(user_id)
        
        # Convert to response format
        candidates = []
        for selection in selections:
            candidate_user = self.db.query(User)\
                .filter(User.id == selection.candidate_user_id)\
                .first()
            
            if candidate_user:
                candidates.append(
                    DailySelectionCandidate(
                        user_id=candidate_user.id,
                        first_name=candidate_user.first_name,
                        age=candidate_user.age,
                        location_city=candidate_user.location_city,
                        compatibility_score=selection.compatibility_score,
                        rank_position=selection.rank_position
                    )
                )
        
        return candidates