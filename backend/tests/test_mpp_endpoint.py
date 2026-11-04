import os
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.models import sample as _sample_models  # noqa: F401 ensure models are registered (do not rebind `app`)

# Create a new SQLite in-memory database for testing.
# StaticPool keeps one connection, so the tables created below are the ones the app sees.
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
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


def test_import_text_with_documented_line_format():
    # Format documented in the README: lines like "V:..V I:..A P:..W"
    client.delete("/api/samples", headers=auth_headers())
    text = "V:20.2V I:0.10A P:2.1W\nV:17.0V I:1.50A\n"
    r = client.post(
        "/api/import/text",
        content=text,
        headers={**auth_headers(), "Content-Type": "text/plain"},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data) == 2
    assert data[1]["P"] == 25.5  # computed V * I when P is missing


def test_import_csv_file_keeps_measurement_times():
    client.delete("/api/samples", headers=auth_headers())
    csv = b"t;V;I\n2026-01-01T10:00:00;20.0;0.5\n2026-01-01T10:00:01;18.0;1.0\n"
    r = client.post(
        "/api/import/file",
        files={"file": ("readings.csv", csv, "text/csv")},
        headers=auth_headers(),
    )
    assert r.status_code == 200, r.text
    # Filtering by the measurement time must find both rows
    r2 = client.get("/api/samples", params={"from": "2026-01-01T09:59:59", "to": "2026-01-01T10:00:02"})
    assert r2.status_code == 200, r2.text
    assert len(r2.json()) == 2
