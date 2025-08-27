#!/usr/bin/env python3
"""
GoldWen Matching Service Demo

This script demonstrates the key functionality of the matching service
without requiring a full database setup. It shows how the core algorithms work.
"""

import json
from datetime import datetime
from typing import List, Dict

# Mock data for demonstration
SAMPLE_USERS = [
    {
        "id": 1,
        "first_name": "Sophie",
        "age": 29,
        "gender": "female",
        "location_city": "Paris",
        "is_premium": False,
        "personality": [4, 3, 5, 4, 3, 5, 4, 3, 4, 5]  # Openness, conscientiousness, etc.
    },
    {
        "id": 2,
        "first_name": "Marc",
        "age": 34,
        "gender": "male", 
        "location_city": "Lyon",
        "is_premium": True,
        "personality": [4, 4, 4, 4, 3, 5, 4, 3, 4, 4]  # Similar to Sophie
    },
    {
        "id": 3,
        "first_name": "Alice",
        "age": 26,
        "gender": "female",
        "location_city": "Marseille", 
        "is_premium": False,
        "personality": [2, 2, 2, 2, 2, 2, 2, 2, 2, 2]  # Very different from others
    },
    {
        "id": 4,
        "first_name": "Thomas",
        "age": 31,
        "gender": "male",
        "location_city": "Nice",
        "is_premium": False,
        "personality": [5, 5, 3, 5, 4, 5, 5, 4, 5, 5]  # High compatibility with Sophie
    },
    {
        "id": 5,
        "first_name": "Emma",
        "age": 28,
        "gender": "female",
        "location_city": "Toulouse",
        "is_premium": False,
        "personality": [3, 3, 4, 3, 3, 4, 3, 4, 3, 4]  # Moderate compatibility
    }
]

def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if len(vec1) != len(vec2):
        return 0.0
    
    # Calculate dot product
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    
    # Calculate norms
    norm1 = (sum(a * a for a in vec1)) ** 0.5
    norm2 = (sum(a * a for a in vec2)) ** 0.5
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)

def calculate_compatibility(user1: Dict, user2: Dict) -> float:
    """Calculate compatibility score between two users."""
    return cosine_similarity(user1["personality"], user2["personality"])

def filter_candidates(user: Dict, all_users: List[Dict]) -> List[Dict]:
    """Filter potential candidates based on GoldWen criteria."""
    candidates = []
    
    for candidate in all_users:
        # Skip self
        if candidate["id"] == user["id"]:
            continue
            
        # Opposite gender (MVP requirement)
        if candidate["gender"] == user["gender"]:
            continue
            
        # Age range ±10 years
        if abs(candidate["age"] - user["age"]) > 10:
            continue
            
        candidates.append(candidate)
    
    return candidates

def generate_daily_selection(user: Dict, all_users: List[Dict]) -> List[Dict]:
    """Generate daily selection for a user."""
    print(f"\n🎯 Generating daily selection for {user['first_name']} (ID: {user['id']})")
    print(f"   Profile: {user['age']} years old, {user['gender']}, {user['location_city']}")
    print(f"   Subscription: {'Premium' if user['is_premium'] else 'Free'}")
    
    # Filter potential candidates
    candidates = filter_candidates(user, all_users)
    print(f"   Found {len(candidates)} potential candidates after filtering")
    
    # Calculate compatibility scores
    scored_candidates = []
    for candidate in candidates:
        score = calculate_compatibility(user, candidate)
        scored_candidates.append({
            "user": candidate,
            "compatibility_score": score
        })
    
    # Sort by compatibility score (descending)
    scored_candidates.sort(key=lambda x: x["compatibility_score"], reverse=True)
    
    # Apply compatibility threshold (0.6)
    threshold = 0.6
    qualified_candidates = [c for c in scored_candidates if c["compatibility_score"] >= threshold]
    
    # Take top 3-5 candidates
    max_candidates = 5
    min_candidates = 3
    
    if len(qualified_candidates) >= min_candidates:
        selection = qualified_candidates[:max_candidates]
    else:
        # If not enough qualified candidates, take best available up to max
        selection = scored_candidates[:max_candidates]
    
    print(f"   📊 Compatibility scores (threshold: {threshold}):")
    for i, candidate_data in enumerate(selection):
        candidate = candidate_data["user"]
        score = candidate_data["compatibility_score"]
        status = "✅" if score >= threshold else "⚠️"
        print(f"      {i+1}. {status} {candidate['first_name']} ({candidate['location_city']}) - {score:.3f}")
    
    # Determine max choices based on subscription
    max_choices = 3 if user["is_premium"] else 1
    print(f"   🎫 Max daily choices: {max_choices}")
    
    return selection

def simulate_user_choice(chooser: Dict, chosen: Dict, all_users: List[Dict]) -> bool:
    """Simulate a user choice and check for mutual match."""
    print(f"\n💝 {chooser['first_name']} chooses {chosen['first_name']}")
    
    # Check if chosen user would also choose the chooser
    # (In real app, this would check the database for existing choices)
    
    # For demo, let's say users choose each other if compatibility > 0.8
    compatibility = calculate_compatibility(chooser, chosen)
    is_mutual = compatibility > 0.8
    
    if is_mutual:
        print(f"   🎉 IT'S A MATCH! Both users have high compatibility ({compatibility:.3f})")
        print(f"   💬 24-hour chat window opens for {chooser['first_name']} and {chosen['first_name']}")
        return True
    else:
        print(f"   💔 No match yet. Compatibility: {compatibility:.3f}")
        return False

def demonstrate_matching_service():
    """Demonstrate the GoldWen Matching Service functionality."""
    print("🧡 GoldWen Matching Service Demo")
    print("=" * 50)
    
    print("\n📋 Sample Users:")
    for user in SAMPLE_USERS:
        premium_badge = "⭐" if user["is_premium"] else "🆓"
        print(f"   {premium_badge} {user['first_name']} ({user['age']}, {user['gender']}, {user['location_city']})")
    
    print("\n🧠 Personality Questionnaire (1-5 scale):")
    questions = [
        "Openness to Experience",
        "Conscientiousness", 
        "Extraversion",
        "Agreeableness",
        "Neuroticism",
        "Values Alignment",
        "Communication Style",
        "Lifestyle Preferences",
        "Relationship Goals",
        "Conflict Resolution"
    ]
    
    for i, question in enumerate(questions):
        print(f"   {i+1}. {question}")
    
    # Demonstrate daily selection for Sophie
    sophie = SAMPLE_USERS[0]  # Sophie
    selection = generate_daily_selection(sophie, SAMPLE_USERS)
    
    # Simulate Sophie choosing Thomas (highest compatibility)
    if selection:
        thomas = next(c["user"] for c in selection if c["user"]["first_name"] == "Thomas")
        if thomas:
            is_match = simulate_user_choice(sophie, thomas, SAMPLE_USERS)
    
    # Demonstrate daily selection for Marc
    marc = SAMPLE_USERS[1]  # Marc  
    selection_marc = generate_daily_selection(marc, SAMPLE_USERS)
    
    print("\n📊 Algorithm Summary:")
    print("   🎯 Content-based filtering using personality vectors")
    print("   📐 Cosine similarity for compatibility scoring")
    print("   🔍 Filtering: opposite gender, age ±10 years")
    print("   ⚡ Caching: 24-hour compatibility score cache")
    print("   📅 Daily ritual: 3-5 curated profiles at 12:00 PM")
    print("   💎 Premium: 3 choices/day vs 1 choice/day for free")
    
    print("\n🚀 Ready for production deployment!")
    print("   🐳 Docker containerization")
    print("   🔄 PostgreSQL + Redis stack")
    print("   📡 RESTful API for NestJS integration")
    print("   🧪 Comprehensive test suite")
    print("   📚 Complete documentation")

if __name__ == "__main__":
    demonstrate_matching_service()