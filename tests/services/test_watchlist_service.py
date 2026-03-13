# -*- coding: utf-8 -*-
"""Tests for WatchlistService."""

import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy import create_engine

from src.storage import DatabaseManager, Base
from src.services.watchlist_service import WatchlistService


@pytest.fixture
def service():
    """Create service with temp database."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    db_url = f"sqlite:///{path}"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)

    DatabaseManager.reset_instance()
    DatabaseManager(db_url)

    yield WatchlistService()

    DatabaseManager.reset_instance()
    if os.path.exists(path):
        os.unlink(path)


def test_add_stock(service):
    """Test adding a stock to watchlist."""
    item = service.add_stock("600519")
    assert item.stock_code == "600519"


def test_remove_stock(service):
    """Test removing a stock from watchlist."""
    service.add_stock("600519")
    removed = service.remove_stock("600519")
    assert removed is True


def test_remove_nonexistent(service):
    """Test removing non-existent stock."""
    removed = service.remove_stock("NOTEXIST")
    assert removed is False


def test_get_all_empty(service):
    """Test getting all from empty watchlist."""
    items = service.get_all()
    assert items == []


def test_get_all_with_items(service):
    """Test getting all watchlist items."""
    service.add_stock("600519")
    service.add_stock("00700")

    items = service.get_all()
    assert len(items) == 2
    codes = [i.stock_code for i in items]
    assert "600519" in codes
    assert "00700" in codes
