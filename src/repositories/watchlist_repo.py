# -*- coding: utf-8 -*-
"""Watchlist repository for database operations."""

from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError

from src.storage import DatabaseManager, StockWatchlist


class WatchlistRepository:
    """Repository for watchlist database operations."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db_manager = db_manager or DatabaseManager.get_instance()

    def add(self, stock_code: str) -> StockWatchlist:
        """Add a stock to watchlist. Returns existing if duplicate."""
        with self.db_manager.session_scope() as session:
            # Check if exists first
            stmt = select(StockWatchlist).where(StockWatchlist.stock_code == stock_code)
            existing = session.execute(stmt).scalar_one_or_none()
            if existing:
                session.expunge(existing)
                return existing

            # Create new
            item = StockWatchlist(stock_code=stock_code)
            session.add(item)
            session.flush()
            session.refresh(item)
            result = StockWatchlist(
                id=item.id,
                stock_code=item.stock_code,
                added_at=item.added_at
            )
            return result

    def remove(self, stock_code: str) -> bool:
        """Remove a stock from watchlist. Returns True if removed."""
        with self.db_manager.session_scope() as session:
            stmt = delete(StockWatchlist).where(StockWatchlist.stock_code == stock_code)
            result = session.execute(stmt)
            return result.rowcount > 0

    def get_all(self) -> List[StockWatchlist]:
        """Get all watchlist items."""
        with self.db_manager.session_scope() as session:
            stmt = select(StockWatchlist).order_by(StockWatchlist.added_at.desc())
            results = session.execute(stmt).scalars().all()
            for r in results:
                session.expunge(r)
            return list(results)

    def get_by_code(self, stock_code: str) -> Optional[StockWatchlist]:
        """Get a watchlist item by stock code."""
        with self.db_manager.session_scope() as session:
            stmt = select(StockWatchlist).where(StockWatchlist.stock_code == stock_code)
            result = session.execute(stmt).scalar_one_or_none()
            if result:
                session.expunge(result)
            return result
