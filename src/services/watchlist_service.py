# -*- coding: utf-8 -*-
"""Watchlist service for business logic."""

import logging
from typing import List, Optional

from src.storage import DatabaseManager, StockWatchlist
from src.repositories.watchlist_repo import WatchlistRepository

logger = logging.getLogger(__name__)


class WatchlistService:
    """Service for managing stock watchlist."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.repo = WatchlistRepository(db_manager)

    def add_stock(self, stock_code: str) -> StockWatchlist:
        """
        Add a stock to the watchlist.

        Args:
            stock_code: Stock code to add

        Returns:
            StockWatchlist instance
        """
        return self.repo.add(stock_code)

    def remove_stock(self, stock_code: str) -> bool:
        """
        Remove a stock from the watchlist.

        Args:
            stock_code: Stock code to remove

        Returns:
            True if removed, False if not found
        """
        return self.repo.remove(stock_code)

    def get_all(self) -> List[StockWatchlist]:
        """
        Get all stocks in watchlist.

        Returns:
            List of StockWatchlist items
        """
        return self.repo.get_all()
