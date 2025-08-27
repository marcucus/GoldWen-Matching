# GoldWen Matching Service

🧡 A sophisticated matching microservice for the GoldWen dating app MVP, implementing content-based personality matching algorithms.

## Overview

This repository contains the **Matching Service** for GoldWen - a revolutionary dating app that focuses on quality over quantity. The service implements a content-based filtering algorithm that uses personality questionnaire responses to generate highly compatible daily profile selections.

### Key Features

- **🧠 Content-Based Matching**: Advanced personality-based compatibility scoring using cosine similarity
- **📅 Daily Ritual**: Curated selection of 3-5 profiles per day to combat dating app fatigue  
- **⭐ Premium Support**: Flexible choice limits (1 for free users, 3 for premium)
- **🚀 High Performance**: Intelligent caching and optimized database queries
- **🔧 Microservice Architecture**: Clean, scalable FastAPI-based service
- **🐳 Docker Ready**: Complete containerization with Docker Compose
- **✅ Comprehensive Testing**: Full test coverage with pytest
- **🔒 GDPR Compliant**: Built-in data privacy and user deletion features

## Architecture

```
GoldWen Ecosystem
├── Mobile App (React Native) 
├── Main API (NestJS/TypeScript) 
└── Matching Service (Python/FastAPI) ← This Repository
    ├── PostgreSQL (User data & preferences)
    └── Redis (Caching layer)
```

The matching service integrates seamlessly with the main NestJS API through RESTful endpoints, providing:
- Daily profile selections based on personality compatibility
- Real-time compatibility scoring between users
- Match tracking and mutual choice detection
- Premium feature support for enhanced user experience

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL (if running without Docker)

### Using Docker (Recommended)

1. **Clone and navigate to the matching service**:
```bash
git clone <repository-url>
cd GoldWen-Matching/matching-service
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start the complete stack**:
```bash
docker-compose up --build
```

This launches:
- 🔥 **Matching Service**: http://localhost:8000
- 🗄️ **PostgreSQL**: localhost:5432  
- ⚡ **Redis**: localhost:6379
- 📚 **API Docs**: http://localhost:8000/docs

### Manual Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start development server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 📊 Matching Algorithm

### Content-Based Filtering (MVP)

The service implements a sophisticated personality-based matching algorithm:

1. **📝 Personality Vectors**: 10-dimensional vectors from questionnaire responses (1-5 scale)
2. **🔢 Compatibility Scoring**: Cosine similarity between personality vectors  
3. **🎯 Smart Filtering**: Age range (±10 years), opposite gender, location-based
4. **⚡ Performance Optimization**: 24-hour compatibility score caching
5. **🛡️ Quality Control**: Minimum compatibility threshold of 0.6

### Daily Selection Process

```python
# Simplified algorithm flow
def generate_daily_selection(user_id):
    1. Get user personality profile
    2. Filter potential candidates (age, gender, location)
    3. Exclude recent selections and choices  
    4. Calculate compatibility scores
    5. Rank by compatibility (>0.6 threshold)
    6. Return top 3-5 candidates
    7. Cache results for performance
```

### Future Enhancements (V2)
- 🤖 **Machine Learning Models**: Advanced neural networks for better predictions
- 👥 **Collaborative Filtering**: Learn from user behavior patterns
- 🌍 **Geospatial Queries**: Precise location-based matching
- 📊 **A/B Testing**: Framework for algorithm optimization

## 🛠️ API Reference

### Core Endpoints

#### Matching Operations
```http
GET    /api/v1/matching/daily-selection/{user_id}     # Get daily profile selection
POST   /api/v1/matching/generate-selection/{user_id}  # Force generate new selection  
POST   /api/v1/matching/compatibility-score           # Calculate user compatibility
POST   /api/v1/matching/user-choice/{user_id}         # Record choice & check matches
```

#### User Management
```http
POST   /api/v1/users/                           # Create user profile
POST   /api/v1/users/{user_id}/personality      # Submit personality questionnaire
PUT    /api/v1/users/{user_id}/premium          # Update subscription status
DELETE /api/v1/users/{user_id}                  # GDPR-compliant deletion
```

### Example API Usage

```python
# Submit personality questionnaire
POST /api/v1/users/123/personality
{
  "responses": [
    {"question_id": 1, "response_value": 4},
    {"question_id": 2, "response_value": 3},
    // ... 8 more responses
  ]
}

# Get daily selection
GET /api/v1/matching/daily-selection/123
{
  "user_id": 123,
  "selection_date": "2024-01-15T12:00:00Z",
  "candidates": [
    {
      "user_id": 456,
      "first_name": "Alice", 
      "age": 28,
      "location_city": "Paris",
      "compatibility_score": 0.87,
      "rank_position": 1
    }
  ],
  "max_choices_allowed": 1
}
```

## 🧪 Testing

Comprehensive test suite covering all functionality:

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test categories
pytest app/tests/test_matching_service.py -v
pytest app/tests/test_api.py -v
```

### Test Coverage
- ✅ Compatibility scoring algorithms
- ✅ Daily selection generation  
- ✅ API endpoint functionality
- ✅ Database operations
- ✅ Error handling and edge cases

## 🔧 Configuration

Key environment variables:

```bash
# Core Settings
DEBUG=True
DATABASE_URL=postgresql://user:pass@localhost:5432/goldwen_db
REDIS_URL=redis://localhost:6379/0

# Algorithm Tuning
MAX_DAILY_PROFILES=5          # Maximum profiles per selection
MIN_DAILY_PROFILES=3          # Minimum profiles to attempt  
COMPATIBILITY_THRESHOLD=0.6   # Minimum compatibility score
PERSONALITY_QUESTIONS_COUNT=10 # Number of personality questions
```

## 🔄 Integration Guide

### For Main NestJS API

1. **User Onboarding**: Forward user creation and personality data
2. **Daily Ritual**: Request daily selections at 12:00 PM user local time
3. **Choice Handling**: Forward user choices and retrieve match status
4. **Premium Features**: Sync subscription status for choice limits

```typescript
// Example NestJS integration
async getDailySelection(userId: number) {
  const response = await this.httpService.get(
    `${MATCHING_SERVICE_URL}/api/v1/matching/daily-selection/${userId}`
  );
  return response.data;
}
```

## 📚 Documentation

- **API Documentation**: Available at `/docs` when running
- **Database Schema**: See `app/models/user.py` for complete schema  
- **Algorithm Details**: Documented in `app/services/matching_service.py`
- **Integration Examples**: Check `app/tests/` for usage patterns

## 🤝 Contributing

1. **Follow Clean Architecture**: Maintain separation of concerns
2. **Add Tests**: All new features require comprehensive tests
3. **Type Hints**: Use type hints throughout the codebase
4. **Documentation**: Update API docs for any endpoint changes  
5. **Performance**: Consider caching and optimization for new features

## 📄 License

Part of the GoldWen dating app MVP - focusing on meaningful connections over endless swiping.

---

**"Designed to be uninstalled"** - GoldWen's mission is helping users find lasting relationships, not endless engagement.