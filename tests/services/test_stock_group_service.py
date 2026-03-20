# -*- coding: utf-8 -*-
"""Unit tests for StockGroupService."""

import os
import tempfile

import pytest


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    from src.storage import DatabaseManager, Base
    from sqlalchemy import create_engine

    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    # Create engine and tables directly
    db_url = f"sqlite:///{path}"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)

    # Reset singleton and create new instance
    DatabaseManager.reset_instance()
    db_manager = DatabaseManager(db_url)

    yield db_manager

    # Cleanup
    DatabaseManager.reset_instance()
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def group_service(temp_db):
    """Create service instance for testing."""
    from src.services.stock_group_service import StockGroupService
    return StockGroupService(db_manager=temp_db)


def test_create_group(group_service):
    """Test creating a new stock group."""
    group = group_service.create_group(
        name="科技成长",
        description="高增长科技股",
        stock_codes=["00700", "09988"]
    )

    assert group.id is not None
    assert group.name == "科技成长"
    assert group.description == "高增长科技股"
    assert group.get_stock_codes() == ["00700", "09988"]


def test_create_duplicate_group(group_service):
    """Test that duplicate group names are rejected."""
    group_service.create_group(name="测试组", stock_codes=["600519"])

    with pytest.raises(ValueError, match="already exists"):
        group_service.create_group(name="测试组", stock_codes=["300750"])


def test_get_all_groups(group_service):
    """Test retrieving all groups sorted by sort_order."""
    group_service.create_group(name="组B", stock_codes=["600519"], sort_order=2)
    group_service.create_group(name="组A", stock_codes=["300750"], sort_order=1)

    groups = group_service.get_all_groups()

    assert len(groups) == 2
    assert groups[0].name == "组A"  # sort_order=1 comes first
    assert groups[1].name == "组B"


def test_update_group(group_service):
    """Test updating a group."""
    group = group_service.create_group(name="测试组", stock_codes=["600519"])
    updated = group_service.update_group(group.id, name="更新组", stock_codes=["600519", "300750"])

    assert updated.name == "更新组"
    assert updated.get_stock_codes() == ["600519", "300750"]


def test_delete_group(group_service):
    """Test deleting a group."""
    group = group_service.create_group(name="待删除", stock_codes=[])
    group_service.delete_group(group.id)

    groups = group_service.get_all_groups()
    assert len(groups) == 0


def test_get_all_stock_codes_with_groups(group_service):
    """Test getting all stock codes from groups (with deduplication)."""
    group_service.create_group(name="组1", stock_codes=["600519", "300750"])
    group_service.create_group(name="组2", stock_codes=["600519", "00700"])  # 600519 duplicate

    codes = group_service.get_all_stock_codes()

    assert codes == ["600519", "300750", "00700"]  # Deduplicated, order preserved


def test_get_all_stock_codes_fallback_to_env(temp_db, monkeypatch):
    """Test fallback to STOCK_LIST env var when no groups exist."""
    from src.services.stock_group_service import StockGroupService

    monkeypatch.setenv("STOCK_LIST", "AAPL,TSLA,GOOGL")

    # Create fresh service with no groups
    service = StockGroupService(db_manager=temp_db)
    codes = service.get_all_stock_codes()

    assert codes == ["AAPL", "TSLA", "GOOGL"]
