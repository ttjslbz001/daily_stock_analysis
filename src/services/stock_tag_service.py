# -*- coding: utf-8 -*-
"""Stock tag service for business logic."""

from typing import List, Optional

from src.storage import DatabaseManager
from src.repositories.stock_tag_repo import StockTagRepository


class StockTagService:
    """Service for managing stock tags."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.repo = StockTagRepository(db_manager)

    def get_tags(self, stock_code: str) -> List[str]:
        """Get all tags for a stock."""
        return self.repo.get_tags_for_stock(stock_code)

    def add_tag(self, stock_code: str, tag_name: str):
        """Add a tag to a stock."""
        # Normalize tag name (trim and lowercase for consistency)
        normalized_tag = tag_name.strip()
        if not normalized_tag:
            raise ValueError("Tag name cannot be empty")
        return self.repo.add_tag(stock_code, normalized_tag)

    def remove_tag(self, stock_code: str, tag_name: str) -> bool:
        """Remove a tag from a stock."""
        return self.repo.remove_tag(stock_code, tag_name.strip())

    def get_all_tags(self) -> List[str]:
        """Get all unique tag names."""
        return self.repo.get_all_tags()
