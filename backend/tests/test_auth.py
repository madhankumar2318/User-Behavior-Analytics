"""
Unit Tests for Authentication
"""

import pytest
import json
import sqlite3
from app import app, create_table
from user_manager import user_manager


def _delete_user_by_username(username):
    """Helper: remove a user by username so tests can re-create them cleanly."""
    try:
        conn = sqlite3.connect("database.db")
        conn.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        conn.close()
    except Exception:
        pass  # Table may not exist yet; that's fine


@pytest.fixture
def client():
    """Create test client"""
    app.config["TESTING"] = True
    create_table()

    with app.test_client() as client:
        yield client


@pytest.fixture
def auth_headers(client):
    """Get authentication headers for testing"""
    username = "testuser"
    email = "test@example.com"

    # Clean up any leftover user from a previous run
    _delete_user_by_username(username)

    # Create test user
    user_manager.create_user(
        username=username,
        email=email,
        password="TestPass123!",
        role="Admin",
    )

    # Login
    response = client.post(
        "/auth/login", json={"username": username, "password": "TestPass123!"}
    )

    data = json.loads(response.data)
    token = data["token"]

    yield {"Authorization": token}

    # Teardown — remove user created by this fixture
    _delete_user_by_username(username)


def test_login_success(client):
    """Test successful login"""
    username = "logintest"
    _delete_user_by_username(username)

    user_manager.create_user(
        username=username,
        email="login@example.com",
        password="Password123!",
        role="Viewer",
    )

    response = client.post(
        "/auth/login", json={"username": username, "password": "Password123!"}
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert "token" in data
    assert "user" in data

    # Cleanup
    _delete_user_by_username(username)


def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = client.post(
        "/auth/login", json={"username": "nonexistent", "password": "wrongpass"}
    )

    assert response.status_code == 401
    data = json.loads(response.data)
    assert "error" in data


def test_protected_route_without_token(client):
    """Test accessing protected route without token"""
    response = client.get("/get-logs")
    assert response.status_code == 401


def test_protected_route_with_token(client, auth_headers):
    """Test accessing protected route with valid token"""
    response = client.get("/get-logs", headers=auth_headers)
    assert response.status_code == 200


def test_health_endpoint(client):
    """Test the /health endpoint returns ok"""
    response = client.get("/health")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "ok"
    assert "ml_ready" in data
    assert "timestamp" in data
