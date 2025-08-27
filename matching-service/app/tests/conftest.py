import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.core.database import Base, get_db
from app.models.user import User, PersonalityResponse
from main import app

# Test database URL (using SQLite for simplicity in tests)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def db_session():
    """Create a test database session."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client():
    """Create a test client."""
    Base.metadata.create_all(bind=engine)
    try:
        with TestClient(app) as c:
            yield c
    finally:
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    user = User(
        email="test@example.com",
        first_name="John",
        age=25,
        gender="male",
        location_city="Paris",
        location_latitude=48.8566,
        location_longitude=2.3522
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def sample_user_with_personality(db_session, sample_user):
    """Create a user with personality responses."""
    # Add personality responses (1-5 scale for 10 questions)
    responses = [
        PersonalityResponse(user_id=sample_user.id, question_id=i, response_value=(i % 5) + 1)
        for i in range(1, 11)
    ]
    for response in responses:
        db_session.add(response)
    db_session.commit()
    return sample_user