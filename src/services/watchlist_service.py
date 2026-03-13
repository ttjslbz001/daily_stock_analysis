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

    def get_all_with_quotes(self) -> List[dict]:
        """
        Get all stocks with real-time quotes.

        Returns:
            List of dicts with stock_code, stock_name, added_at, quote
        """
        from src.services.stock_service import StockService
        from api.v1.schemas.stocks import StockQuote

        stock_service = StockService()
        items = self.get_all()

        result = []
        for item in items:
            quote_data = stock_service.get_realtime_quote(item.stock_code)
            quote = None
            stock_name = None

            if quote_data:
                stock_name = quote_data.get("stock_name")
                quote = StockQuote(
                    stock_code=quote_data.get("stock_code", item.stock_code),
                    stock_name=quote_data.get("stock_name"),
                    current_price=quote_data.get("current_price", 0.0),
                    change=quote_data.get("change"),
                    change_percent=quote_data.get("change_percent"),
                    open=quote_data.get("open"),
                    high=quote_data.get("high"),
                    low=quote_data.get("low"),
                    prev_close=quote_data.get("prev_close"),
                    volume=quote_data.get("volume"),
                    amount=quote_data.get("amount"),
                    update_time=quote_data.get("update_time")
                )

            result.append({
                "stock_code": item.stock_code,
                "stock_name": stock_name,
                "added_at": item.added_at,
                "quote": quote
            })

        return result
