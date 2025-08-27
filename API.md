# GoldWen Matching Service API Documentation

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
Currently, the service operates without authentication as it's designed to be called by the trusted main NestJS API. In production, consider implementing:
- API Key authentication
- JWT token validation
- IP whitelist

## Health Check

### GET /health
Check service health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "goldwen-matching-service"
}
```

---

## User Management

### POST /users/
Create a new user in the matching service.

**Request Body:**
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "age": 25,
  "gender": "male",
  "location_city": "Paris",
  "location_latitude": 48.8566,
  "location_longitude": 2.3522
}
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "age": 25,
  "gender": "male",
  "location_city": "Paris",
  "location_latitude": 48.8566,
  "location_longitude": 2.3522,
  "is_premium": false,
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### GET /users/{user_id}
Get user details by ID.

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "age": 25,
  "gender": "male",
  "location_city": "Paris",
  "is_premium": false,
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### POST /users/{user_id}/personality
Submit personality questionnaire responses.

**Request Body:**
```json
{
  "responses": [
    {"question_id": 1, "response_value": 4},
    {"question_id": 2, "response_value": 3},
    {"question_id": 3, "response_value": 5},
    {"question_id": 4, "response_value": 2},
    {"question_id": 5, "response_value": 4},
    {"question_id": 6, "response_value": 3},
    {"question_id": 7, "response_value": 5},
    {"question_id": 8, "response_value": 1},
    {"question_id": 9, "response_value": 4},
    {"question_id": 10, "response_value": 3}
  ]
}
```

**Response:**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "question_id": 1,
    "response_value": 4,
    "created_at": "2024-01-15T10:30:00Z"
  },
  // ... 9 more responses
]
```

**Validation Rules:**
- Must have exactly 10 responses
- `question_id` must be between 1 and 10
- `response_value` must be between 1 and 5

### GET /users/{user_id}/personality
Get personality questionnaire responses for a user.

**Response:**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "question_id": 1,
    "response_value": 4,
    "created_at": "2024-01-15T10:30:00Z"
  },
  // ... 9 more responses
]
```

### PUT /users/{user_id}/premium
Update user's premium subscription status.

**Request Body:**
```json
{
  "is_premium": true
}
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "is_premium": true,
  // ... other user fields
}
```

### DELETE /users/{user_id}
Delete a user and all associated data (GDPR compliance).

**Response:**
```json
{
  "message": "User 1 deleted successfully"
}
```

---

## Matching Operations

### GET /matching/daily-selection/{user_id}
Get daily selection of profiles for a user.

**Response:**
```json
{
  "user_id": 1,
  "selection_date": "2024-01-15T12:00:00Z",
  "candidates": [
    {
      "user_id": 2,
      "first_name": "Alice",
      "age": 26,
      "location_city": "Lyon",
      "compatibility_score": 0.87,
      "rank_position": 1
    },
    {
      "user_id": 3,
      "first_name": "Sophie",
      "age": 24,
      "location_city": "Marseille",
      "compatibility_score": 0.82,
      "rank_position": 2
    },
    {
      "user_id": 4,
      "first_name": "Emma",
      "age": 28,
      "location_city": "Nice",
      "compatibility_score": 0.78,
      "rank_position": 3
    }
  ],
  "max_choices_allowed": 1
}
```

**Notes:**
- Returns 3-5 candidates (if available)
- Candidates are ranked by compatibility score
- `max_choices_allowed` is 1 for free users, 3 for premium users
- If no selection exists for today, generates a new one automatically

### POST /matching/generate-selection/{user_id}
Force generate a new daily selection for a user.

**Response:**
Same as GET daily-selection endpoint.

**Use Cases:**
- Testing new algorithm versions
- Manual triggers for special events
- Recovery from errors

### POST /matching/compatibility-score
Calculate compatibility score between two users.

**Request Body:**
```json
{
  "user1_id": 1,
  "user2_id": 2
}
```

**Response:**
```json
{
  "user1_id": 1,
  "user2_id": 2,
  "compatibility_score": 0.87,
  "calculated_at": "2024-01-15T14:30:00Z"
}
```

**Notes:**
- Score ranges from 0.0 to 1.0
- Results are cached for 24 hours
- Requires both users to have completed personality questionnaires

### POST /matching/user-choice/{user_id}
Record a user's choice and check for mutual matches.

**Request Body:**
```json
{
  "chosen_user_id": 2
}
```

**Response:**
```json
{
  "id": 1,
  "user_id": 1,
  "chosen_user_id": 2,
  "choice_date": "2024-01-15T15:45:00Z",
  "is_match": true
}
```

**Business Rules:**
- Free users: 1 choice per day
- Premium users: 3 choices per day
- `is_match` is true only if both users chose each other
- Returns 429 error if daily limit exceeded

### GET /matching/user-choices/{user_id}
Get user's choice history.

**Query Parameters:**
- `limit` (optional): Number of results to return (default: 20)

**Response:**
```json
[
  {
    "id": 1,
    "user_id": 1,
    "chosen_user_id": 2,
    "choice_date": "2024-01-15T15:45:00Z",
    "is_match": true
  },
  {
    "id": 2,
    "user_id": 1,
    "chosen_user_id": 3,
    "choice_date": "2024-01-14T16:30:00Z",
    "is_match": false
  }
]
```

### POST /matching/matching-candidates
Get matching candidates with custom filtering.

**Request Body:**
```json
{
  "user_id": 1,
  "exclude_user_ids": [2, 3],
  "max_results": 5
}
```

**Response:**
```json
{
  "user_id": 1,
  "candidates": [
    {
      "user_id": 4,
      "first_name": "Emma",
      "age": 28,
      "location_city": "Nice",
      "compatibility_score": 0.78,
      "rank_position": 1
    }
  ],
  "generated_at": "2024-01-15T16:00:00Z"
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Personality questionnaire must have exactly 10 responses"
}
```

### 404 Not Found
```json
{
  "detail": "User not found"
}
```

### 429 Too Many Requests
```json
{
  "detail": "Daily choice limit exceeded. You can make 1 choices per day."
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Matching Algorithm Details

### Personality Questions (1-10)
The personality questionnaire consists of 10 questions, each rated on a 1-5 scale:

1. **Openness to Experience**: How open are you to new experiences?
2. **Conscientiousness**: How organized and responsible are you?
3. **Extraversion**: How outgoing and energetic are you?
4. **Agreeableness**: How cooperative and trusting are you?
5. **Neuroticism**: How emotionally stable are you?
6. **Values Alignment**: How important are shared values in a relationship?
7. **Communication Style**: How do you prefer to communicate?
8. **Lifestyle Preferences**: What kind of lifestyle do you prefer?
9. **Relationship Goals**: What are you looking for in a relationship?
10. **Conflict Resolution**: How do you handle disagreements?

### Compatibility Calculation
1. **Vector Creation**: Each user's responses form a 10-dimensional vector
2. **Cosine Similarity**: Calculate the cosine similarity between vectors
3. **Score Range**: 0.0 (completely incompatible) to 1.0 (perfectly compatible)
4. **Threshold**: Minimum score of 0.6 required for daily selection inclusion

### Filtering Criteria
- **Age**: ±10 years from user's age
- **Gender**: Opposite gender (for MVP)
- **Location**: Same city or nearby (basic filtering)
- **Exclusions**: Recent selections, previous choices, inactive users
- **Activity**: Only active users who completed personality questionnaire

---

## Rate Limits

- **Daily Selection**: Once per user per day (automatic generation)
- **User Choices**: 1 per day (free), 3 per day (premium)
- **Compatibility Calculation**: No limit (cached for performance)
- **User Management**: No limit (trusted internal API)

---

## Caching Strategy

- **Compatibility Scores**: 24-hour cache
- **Daily Selections**: Generated once per day at 12:00 PM
- **User Data**: No caching (real-time updates required)

---

## Performance Metrics

- **Response Time**: < 200ms for cached operations, < 1s for calculations
- **Throughput**: 1000+ requests per minute
- **Availability**: 99.5% uptime target
- **Cache Hit Rate**: > 80% for compatibility scores

---

## Development & Testing

### Interactive API Documentation
When running in development mode, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Testing Endpoints
Use the provided Docker Compose setup to test the complete system:

```bash
cd matching-service
docker-compose up --build
```

### Sample Test Flow
1. Create two users with POST /users/
2. Submit personality questionnaires for both
3. Request daily selection for first user
4. Record choice for one of the candidates
5. Check if it creates a match