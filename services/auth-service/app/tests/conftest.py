import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.db.db import Base, get_session
from app.core.limiter import limiter

limiter.enabled = False #In tests we shouldn't use redis
SQLALCHEMY_TEST_URL = "sqlite:///:memory:"

engine = create_engine(
    "sqlite:///:memory:",
    #to be available to check in other threads
    connect_args={"check_same_thread": False},
    #to share the same db in memory
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_session():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_session] = override_get_session

@pytest.fixture(autouse=True)
def clean_db():
    yield
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
@pytest.fixture

def client():
    return TestClient(app)
@pytest.fixture
def auth_token(client):
    client.post("/auth/register", json={
        "username": "Test",
        "email": "example@example.com",
        "password": "ThisIsATest123!"
    })

    response = client.post("/auth/login", json={
        "email": "example@example.com",
        "password": "ThisIsATest123!"
    })

    return response.json()["access_token"]