# -*- coding: utf-8 -*-
"""Integration tests for stock groups API endpoints."""

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


def test_create_group_api(client):
    """Test POST /api/v1/groups endpoint."""
    response = client.post("/api/v1/groups/", json={
        "name": "科技成长",
        "description": "高增长科技股",
        "stock_codes": ["00700", "09988"]
    })

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "科技成长"
    assert data["description"] == "高增长科技股"
    assert data["stock_codes"] == ["00700", "09988"]
    assert "id" in data


def test_list_groups_api(client):
    """Test GET /api/v1/groups endpoint."""
    # Create two groups
    client.post("/api/v1/groups/", json={
        "name": "组A",
        "stock_codes": ["600519"],
        "sort_order": 2
    })
    client.post("/api/v1/groups/", json={
        "name": "组B",
        "stock_codes": ["300750"],
        "sort_order": 1
    })

    response = client.get("/api/v1/groups/")

    assert response.status_code == 200
    data = response.json()
    assert "groups" in data
    assert len(data["groups"]) == 2
    # Verify sorted by sort_order
    assert data["groups"][0]["name"] == "组B"
    assert data["groups"][1]["name"] == "组A"


def test_update_group_api(client):
    """Test PUT /api/v1/groups/{id} endpoint."""
    # Create group
    create_resp = client.post("/api/v1/groups/", json={
        "name": "测试组",
        "stock_codes": ["600519"]
    })
    group_id = create_resp.json()["id"]

    # Update group
    response = client.put(f"/api/v1/groups/{group_id}", json={
        "name": "更新组",
        "stock_codes": ["600519", "300750"]
    })

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "更新组"
    assert data["stock_codes"] == ["600519", "300750"]


def test_delete_group_api(client):
    """Test DELETE /api/v1/groups/{id} endpoint."""
    # Create group
    create_resp = client.post("/api/v1/groups/", json={
        "name": "待删除",
        "stock_codes": []
    })
    group_id = create_resp.json()["id"]

    # Delete group
    response = client.delete(f"/api/v1/groups/{group_id}")
    assert response.status_code == 204

    # Verify deleted
    list_resp = client.get("/api/v1/groups/")
    groups = list_resp.json()["groups"]
    assert len(groups) == 0


def test_batch_reorder_api(client):
    """Test POST /api/v1/groups/batch-reorder endpoint."""
    # Create groups
    resp1 = client.post("/api/v1/groups/", json={
        "name": "组1",
        "stock_codes": ["A"],
        "sort_order": 1
    })
    resp2 = client.post("/api/v1/groups/", json={
        "name": "组2",
        "stock_codes": ["B"],
        "sort_order": 2
    })

    id1 = resp1.json()["id"]
    id2 = resp2.json()["id"]

    # Reorder (swap)
    response = client.post("/api/v1/groups/batch-reorder", json={
        "orders": [
            {"id": id1, "sort_order": 2},
            {"id": id2, "sort_order": 1}
        ]
    })

    assert response.status_code == 200

    # Verify order
    list_resp = client.get("/api/v1/groups/")
    groups = list_resp.json()["groups"]
    assert groups[0]["id"] == id2
    assert groups[1]["id"] == id1


def test_duplicate_group_name_api(client):
    """Test that duplicate names return error."""
    client.post("/api/v1/groups/", json={
        "name": "重复名",
        "stock_codes": ["A"]
    })

    response = client.post("/api/v1/groups/", json={
        "name": "重复名",
        "stock_codes": ["B"]
    })

    assert response.status_code == 400
    data = response.json()
    # Error response is directly {"error": ..., "message": ...}
    assert "already exists" in data.get("message", str(data))
