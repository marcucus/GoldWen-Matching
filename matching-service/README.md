# GoldWen Matching Service

A Python-based microservice for the GoldWen dating app that implements content-based matching algorithms. This service is part of the GoldWen MVP and provides personality-based compatibility scoring and daily profile selections.

## Features

- **Content-Based Matching**: Uses personality questionnaire responses to calculate compatibility scores
- **Daily Selection Algorithm**: Generates 3-5 highly compatible profiles per user per day
- **Compatibility Scoring**: Cosine similarity-based scoring between personality vectors
- **Premium Support**: Different selection limits for free (1 choice) vs premium (3 choices) users
- **Caching**: Intelligent caching of compatibility scores to improve performance
- **RESTful API**: FastAPI-based endpoints for integration with the main NestJS backend

## Architecture

The service follows a clean architecture pattern:

```
app/
├── api/           # FastAPI routes and endpoints
├── core/          # Configuration and database setup
├── models/        # SQLAlchemy database models
├── schemas/       # Pydantic request/response models
├── services/      # Business logic and matching algorithms
└── tests/         # Unit and integration tests
```

## Technology Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Caching**: Redis (for future optimization)
- **Containerization**: Docker & Docker Compose
- **Testing**: pytest
- **Migrations**: Alembic

## Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository and navigate to the matching service directory:
```bash
cd matching-service
```

2. Copy the environment file:
```bash
cp .env.example .env
```

3. Start the services:
```bash
docker-compose up --build
```

This will start:
- Matching service on `http://localhost:8000`
- PostgreSQL database on `localhost:5432`
- Redis on `localhost:6379`

### Manual Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Set up PostgreSQL database and update the `DATABASE_URL` in `.env`

3. Run database migrations:
```bash
alembic upgrade head
```

4. Start the service:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API Documentation

Once the service is running, you can access:
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Key Endpoints

#### User Management
- `POST /api/v1/users/` - Create a new user
- `GET /api/v1/users/{user_id}` - Get user details
- `POST /api/v1/users/{user_id}/personality` - Submit personality questionnaire
- `PUT /api/v1/users/{user_id}/premium` - Update premium status

#### Matching
- `GET /api/v1/matching/daily-selection/{user_id}` - Get daily profile selection
- `POST /api/v1/matching/generate-selection/{user_id}` - Force generate new selection
- `POST /api/v1/matching/compatibility-score` - Calculate compatibility between two users
- `POST /api/v1/matching/user-choice/{user_id}` - Record user choice and check for matches

## Matching Algorithm

The service implements a content-based filtering algorithm:

1. **Personality Vectors**: Each user has a 10-dimensional vector from personality questionnaire responses (1-5 scale)
2. **Compatibility Scoring**: Uses cosine similarity to measure compatibility between personality vectors
3. **Daily Selection**: 
   - Filters potential candidates (opposite gender, age range, location)
   - Calculates compatibility scores for all candidates
   - Returns top 3-5 matches above the compatibility threshold (0.6)
4. **Caching**: Compatibility scores are cached for 24 hours to improve performance

### Matching Criteria

- **Gender Filtering**: Currently supports opposite-gender matching for MVP
- **Age Range**: ±10 years from user's age
- **Location**: Basic city-based filtering (can be enhanced with geospatial queries)
- **Exclusions**: Automatically excludes previously chosen users and recent selections
- **Threshold**: Minimum compatibility score of 0.6 for inclusion in daily selection

## Database Schema

### Users Table
- Basic user information (email, name, age, gender, location)
- Premium subscription status
- Activity status

### Personality Responses Table
- 10 personality question responses per user
- 1-5 scale values for each question

### Daily Selections Table
- Stores generated daily selections with compatibility scores
- Tracks ranking and selection dates

### User Choices Table
- Records user choices and mutual matches
- Tracks choice dates and match status

### Compatibility Cache Table
- Caches compatibility scores between user pairs
- Improves performance for repeated calculations

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest app/tests/test_matching_service.py -v
```

## Integration with Main Backend

This service is designed to be consumed by the main NestJS API:

1. **User Creation**: Main API creates users in the matching service when they complete onboarding
2. **Personality Sync**: Personality questionnaire responses are sent to the matching service
3. **Daily Selections**: Main API requests daily selections for the "daily ritual" feature
4. **Choice Recording**: User choices are recorded through the matching service
5. **Match Notifications**: Main API can query for new matches to send notifications

## Configuration

Key configuration options in `.env`:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/goldwen_db
REDIS_URL=redis://localhost:6379/0

# Matching Algorithm
MAX_DAILY_PROFILES=5          # Maximum profiles in daily selection
MIN_DAILY_PROFILES=3          # Minimum profiles to attempt
COMPATIBILITY_THRESHOLD=0.6   # Minimum compatibility score
PERSONALITY_QUESTIONS_COUNT=10 # Number of personality questions
```

## Future Enhancements (V2)

- **Collaborative Filtering**: Learn from user choices to improve recommendations
- **Machine Learning Models**: Advanced ML models for better compatibility prediction
- **Geospatial Queries**: Precise distance-based location filtering
- **Real-time Updates**: WebSocket support for real-time match notifications
- **A/B Testing**: Framework for testing different matching algorithms

## Contributing

1. Follow the existing code structure and patterns
2. Add tests for new features
3. Update documentation for API changes
4. Use type hints throughout the codebase
5. Follow FastAPI best practices

## License

This project is part of the GoldWen dating app MVP.