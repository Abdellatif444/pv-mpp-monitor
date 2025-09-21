import os
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import app.models.sample  # noqa: F401 ensure models are registered

# Create a new SQLite in-memory database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the tables in the test database
Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# Ensure token is set for write endpoints
os.environ["API_TOKEN"] = "devtoken"


def auth_headers():
    return {"Authorization": f"Bearer {os.environ['API_TOKEN']}"}


def test_mpp_flow():
    # Create some samples
    payload = [
        {"V": 0.0, "I": 5.0},
        {"V": 5.0, "I": 4.0},
        {"V": 10.0, "I": 3.0},  # P = 30 (MPP)
        {"V": 15.0, "I": 1.0},
    ]
    r = client.post("/api/samples", json=payload, headers=auth_headers())
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data) == 4

    # Query MPP
    r2 = client.get("/api/mpp")
    assert r2.status_code == 200, r2.text
    mpp = r2.json()
    assert mpp["Pmp"] == 30.0
    assert mpp["Vmp"] == 10.0
    assert mpp["Imp"] == 3.0
