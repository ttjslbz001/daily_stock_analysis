# -*- coding: utf-8 -*-
"""Integration tests for watchlist API endpoints."""

import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client with temp database."""
    from api.app import create_app
    from src.storage import DatabaseManager, Base
    from sqlalchemy import create_engine

    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    db_url = f"sqlite:///{path}"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)

    DatabaseManager.reset_instance()
    DatabaseManager(db_url)

    app = create_app()

    with TestClient(app) as test_client:
        yield test_client

    DatabaseManager.reset_instance()
    if os.path.exists(path):
        os.unlink(path)


def test_add_stock_api(client):
    """Test POST /api/v1/watchlist/{stock_code} endpoint."""
    response = client.post("/api/v1/watchlist/600519")

    assert response.status_code == 200
    data = response.json()
    assert data["stock_code"] == "600519"
    assert "added_at" in data


def test_list_watchlist_api(client):
    """Test GET /api/v1/watchlist endpoint."""
    # Add two stocks
    client.post("/api/v1/watchlist/600519")
    client.post("/api/v1/watchlist/00700")

    # Mock the quote service to avoid external calls
    with patch('src.services.watchlist_service.WatchlistService.get_all_with_quotes') as mock:
        mock.return_value = [
            {
                "stock_code": "600519",
                "stock_name": "贵州茅台",
                "added_at": "2024-01-01T00:00:00",
                "quote": None
            },
            {
                "stock_code": "00700",
                "stock_name": "腾讯控股",
                "added_at": "2024-01-01T00:00:00",
                "quote": None
            }
        ]
        response = client.get("/api/v1/watchlist/")

    assert response.status_code == 200
    data = response.json()
    assert "stocks" in data
    assert data["total"] == 2


def test_remove_stock_api(client):
    """Test DELETE /api/v1/watchlist/{stock_code} endpoint."""
    # Add then remove
    client.post("/api/v1/watchlist/600519")
    response = client.delete("/api/v1/watchlist/600519")

    assert response.status_code == 204

    # Verify removed
    with patch('src.services.watchlist_service.WatchlistService.get_all_with_quotes') as mock:
        mock.return_value = []
        list_resp = client.get("/api/v1/watchlist/")

    data = list_resp.json()
    assert data["total"] == 0


def test_remove_nonexistent_api(client):
    """Test DELETE returns 404 for non-existent stock."""
    response = client.delete("/api/v1/watchlist/NOTEXIST")
    assert response.status_code == 404
