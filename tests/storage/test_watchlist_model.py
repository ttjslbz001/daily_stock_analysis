# -*- coding: utf-8 -*-
"""Tests for StockWatchlist model."""

import pytest
from datetime import datetime

from src.storage import StockWatchlist


def test_watchlist_model_creation():
    """Test StockWatchlist model can be instantiated."""
    item = StockWatchlist(stock_code="600519")
    assert item.stock_code == "600519"
    assert item.added_at is None  # Set by DB default


def test_watchlist_model_repr():
    """Test StockWatchlist string representation."""
    item = StockWatchlist(stock_code="00700")
    assert "StockWatchlist" in repr(item)
    assert "00700" in repr(item)
