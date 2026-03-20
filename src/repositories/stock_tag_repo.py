# -*- coding: utf-8 -*-
"""Stock tag repository for database operations."""

from typing import List, Optional
from sqlalchemy import select, delete, distinct
from sqlalchemy.exc import IntegrityError

from src.storage import DatabaseManager, StockTag


class StockTagRepository:
    """Repository for stock tag database operations."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db_manager = db_manager or DatabaseManager.get_instance()

    def get_tags_for_stock(self, stock_code: str) -> List[str]:
        """Get all tag names for a stock."""
        with self.db_manager.session_scope() as session:
            stmt = select(StockTag.tag_name).where(
                StockTag.stock_code == stock_code
            ).order_by(StockTag.tag_name)
            results = session.execute(stmt).scalars().all()
            return list(results)

    def get_stocks_by_tag(self, tag_name: str) -> List[str]:
        """Get all stock codes with a specific tag."""
        with self.db_manager.session_scope() as session:
            stmt = select(StockTag.stock_code).where(
                StockTag.tag_name == tag_name
            ).order_by(StockTag.stock_code)
            results = session.execute(stmt).scalars().all()
            return list(results)

    def add_tag(self, stock_code: str, tag_name: str) -> StockTag:
        """Add a tag to a stock. Returns the created tag."""
        with self.db_manager.session_scope() as session:
            tag = StockTag(stock_code=stock_code, tag_name=tag_name)
            try:
                session.add(tag)
                session.flush()
                session.refresh(tag)
                # Return a detached copy
                return StockTag(
                    id=tag.id,
                    stock_code=tag.stock_code,
                    tag_name=tag.tag_name,
                    created_at=tag.created_at
                )
            except IntegrityError:
                session.rollback()
                # Tag already exists, return existing
                stmt = select(StockTag).where(
                    StockTag.stock_code == stock_code,
                    StockTag.tag_name == tag_name
                )
                existing = session.execute(stmt).scalar_one_or_none()
                return existing

    def remove_tag(self, stock_code: str, tag_name: str) -> bool:
        """Remove a tag from a stock. Returns True if removed."""
        with self.db_manager.session_scope() as session:
            stmt = delete(StockTag).where(
                StockTag.stock_code == stock_code,
                StockTag.tag_name == tag_name
            )
            result = session.execute(stmt)
            return result.rowcount > 0

    def get_all_tags(self) -> List[str]:
        """Get all unique tag names for autocomplete."""
        with self.db_manager.session_scope() as session:
            stmt = select(distinct(StockTag.tag_name)).order_by(StockTag.tag_name)
            results = session.execute(stmt).scalars().all()
            return list(results)
