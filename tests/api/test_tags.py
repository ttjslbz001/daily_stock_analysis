# -*- coding: utf-8 -*-
"""Integration tests for stock tags API endpoints."""

import os
import tempfile

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client with temp database."""
    from api.app import create_app
    from src.storage import DatabaseManager, Base
    from sqlalchemy import create_engine

    # Create temp database
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    db_url = f"sqlite:///{path}"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)

    # Reset singleton and create new instance
    DatabaseManager.reset_instance()
    db_manager = DatabaseManager(db_url)

    # Create app with test database
    app = create_app()

    with TestClient(app) as test_client:
        yield test_client

    # Cleanup
    DatabaseManager.reset_instance()
    if os.path.exists(path):
        os.unlink(path)


def test_add_tag_api(client):
    """Test POST /api/v1/stocks/{code}/tags endpoint."""
    response = client.post("/api/v1/stocks/600519/tags", json={
        "tag_name": "favorite"
    })

    assert response.status_code == 200
    data = response.json()
    assert "favorite" in data["tags"]


def test_get_stock_tags_api(client):
    """Test GET /api/v1/stocks/{code}/tags endpoint."""
    # Add tags
    client.post("/api/v1/stocks/600519/tags", json={"tag_name": "favorite"})
    client.post("/api/v1/stocks/600519/tags", json={"tag_name": "watch"})

    response = client.get("/api/v1/stocks/600519/tags")

    assert response.status_code == 200
    data = response.json()
    assert "favorite" in data["tags"]
    assert "watch" in data["tags"]


def test_remove_tag_api(client):
    """Test DELETE /api/v1/stocks/{code}/tags/{tag} endpoint."""
    # Add tag
    client.post("/api/v1/stocks/600519/tags", json={"tag_name": "favorite"})

    # Remove tag
    response = client.delete("/api/v1/stocks/600519/tags/favorite")
    assert response.status_code == 200

    # Verify removed
    get_resp = client.get("/api/v1/stocks/600519/tags")
    assert "favorite" not in get_resp.json()["tags"]


def test_get_all_tags_api(client):
    """Test GET /api/v1/tags endpoint."""
    # Add tags to different stocks
    client.post("/api/v1/stocks/600519/tags", json={"tag_name": "favorite"})
    client.post("/api/v1/stocks/000001/tags", json={"tag_name": "watch"})
    client.post("/api/v1/stocks/300750/tags", json={"tag_name": "favorite"})

    response = client.get("/api/v1/tags/")

    assert response.status_code == 200
    data = response.json()
    # Should have unique tags only
    assert "favorite" in data["tags"]
    assert "watch" in data["tags"]
    assert data["tags"].count("favorite") == 1


def test_duplicate_tag_ignored(client):
    """Test that adding duplicate tag is handled gracefully."""
    client.post("/api/v1/stocks/600519/tags", json={"tag_name": "favorite"})
    response = client.post("/api/v1/stocks/600519/tags", json={"tag_name": "favorite"})

    # Should succeed but not duplicate
    assert response.status_code == 200
    assert response.json()["tags"].count("favorite") == 1
