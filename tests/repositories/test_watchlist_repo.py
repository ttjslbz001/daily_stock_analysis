# -*- coding: utf-8 -*-
"""Tests for WatchlistRepository."""

import os
import tempfile

import pytest
from sqlalchemy import create_engine

from src.storage import DatabaseManager, Base, StockWatchlist
from src.repositories.watchlist_repo import WatchlistRepository


@pytest.fixture
def repo():
    """Create repository with temp database."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    db_url = f"sqlite:///{path}"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)

    DatabaseManager.reset_instance()
    DatabaseManager(db_url)

    yield WatchlistRepository()

    DatabaseManager.reset_instance()
    if os.path.exists(path):
        os.unlink(path)


def test_add_stock(repo):
    """Test adding a stock to watchlist."""
    item = repo.add("600519")
    assert item.stock_code == "600519"
    assert item.id is not None
    assert item.added_at is not None


def test_add_duplicate_returns_existing(repo):
    """Test that adding duplicate returns existing item."""
    item1 = repo.add("600519")
    item2 = repo.add("600519")
    assert item1.id == item2.id


def test_remove_stock(repo):
    """Test removing a stock from watchlist."""
    repo.add("600519")
    removed = repo.remove("600519")
    assert removed is True

    all_items = repo.get_all()
    assert len(all_items) == 0


def test_remove_nonexistent_returns_false(repo):
    """Test removing non-existent stock returns False."""
    removed = repo.remove("NOTEXIST")
    assert removed is False


def test_get_all(repo):
    """Test getting all watchlist items."""
    repo.add("600519")
    repo.add("00700")

    items = repo.get_all()
    assert len(items) == 2
    codes = [i.stock_code for i in items]
    assert "600519" in codes
    assert "00700" in codes


def test_get_by_code(repo):
    """Test getting item by stock code."""
    repo.add("600519")

    item = repo.get_by_code("600519")
    assert item is not None
    assert item.stock_code == "600519"

    item = repo.get_by_code("NOTEXIST")
    assert item is None
