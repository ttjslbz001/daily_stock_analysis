# -*- coding: utf-8 -*-
"""Stock group service for business logic."""

import os
import logging
from typing import List, Optional, Dict, Any
import json

from src.storage import DatabaseManager, StockGroup
from src.repositories.stock_group_repo import StockGroupRepository

logger = logging.getLogger(__name__)


class StockGroupService:
    """Service for managing stock groups."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.repo = StockGroupRepository(db_manager)

    def create_group(
        self,
        name: str,
        stock_codes: List[str] = None,
        description: Optional[str] = None,
        sort_order: int = 0
    ) -> StockGroup:
        """
        Create a new stock group.

        Args:
            name: Group name (must be unique)
            stock_codes: List of stock codes
            description: Optional description
            sort_order: Sort order for UI (default 0)

        Returns:
            Created StockGroup instance

        Raises:
            ValueError: If group name already exists
        """
        if stock_codes is None:
            stock_codes = []

        # Create group
        group = StockGroup(
            name=name,
            description=description,
            sort_order=sort_order
        )
        group.set_stock_codes(stock_codes)

        return self.repo.create(group)

    def get_all_groups(self) -> List[StockGroup]:
        """Get all groups sorted by sort_order."""
        return self.repo.get_all()

    def get_group_by_id(self, group_id: int) -> Optional[StockGroup]:
        """Get a specific group by ID."""
        return self.repo.get_by_id(group_id)

    def update_group(
        self,
        group_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        stock_codes: Optional[List[str]] = None,
        sort_order: Optional[int] = None
    ) -> Optional[StockGroup]:
        """
        Update an existing group.

        Args:
            group_id: Group ID to update
            name: New name (optional)
            description: New description (optional)
            stock_codes: New stock codes list (optional)
            sort_order: New sort order (optional)

        Returns:
            Updated StockGroup or None if not found
        """
        updates = {}

        if name is not None:
            updates['name'] = name
        if description is not None:
            updates['description'] = description
        if stock_codes is not None:
            updates['stock_codes'] = json.dumps(stock_codes, ensure_ascii=False)
        if sort_order is not None:
            updates['sort_order'] = sort_order

        if not updates:
            return self.repo.get_by_id(group_id)

        return self.repo.update(group_id, **updates)

    def delete_group(self, group_id: int) -> bool:
        """
        Delete a group by ID.

        Returns:
            True if deleted, False if not found
        """
        return self.repo.delete(group_id)

    def batch_reorder(self, orders: List[Dict[str, int]]) -> bool:
        """
        Update sort orders for multiple groups.

        Args:
            orders: List of {id, sort_order} dicts

        Returns:
            True if successful
        """
        for item in orders:
            group_id = item.get('id')
            new_sort_order = item.get('sort_order')
            if group_id is not None and new_sort_order is not None:
                self.repo.update(group_id, sort_order=new_sort_order)
        return True

    def get_all_stock_codes(self) -> List[str]:
        """
        Get all stock codes from groups, with fallback to STOCK_LIST env var.

        Priority:
        1. Database groups (if not empty)
        2. STOCK_LIST environment variable

        Returns:
            List of unique stock codes (order preserved)
        """
        # Try database groups first
        groups = self.get_all_groups()

        if groups:
            codes = []
            seen = set()
            for group in groups:
                for code in group.get_stock_codes():
                    if code not in seen:
                        codes.append(code)
                        seen.add(code)
            return codes

        # Fallback to environment variable
        stock_list = os.getenv("STOCK_LIST", "")
        return [c.strip() for c in stock_list.split(",") if c.strip()]
