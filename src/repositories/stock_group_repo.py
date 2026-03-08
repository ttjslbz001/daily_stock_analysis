# -*- coding: utf-8 -*-
"""Stock group repository for database operations."""

from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError

from src.storage import DatabaseManager, StockGroup


class StockGroupRepository:
    """Repository for stock group database operations."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db_manager = db_manager or DatabaseManager.get_instance()

    def create(self, group: StockGroup) -> StockGroup:
        """Create a new stock group."""
        with self.db_manager.session_scope() as session:
            try:
                session.add(group)
                session.flush()
                session.refresh(group)
                # Create a detached copy to return
                return StockGroup(
                    id=group.id,
                    name=group.name,
                    description=group.description,
                    stock_codes=group.stock_codes,
                    sort_order=group.sort_order,
                    created_at=group.created_at,
                    updated_at=group.updated_at
                )
            except IntegrityError as e:
                session.rollback()
                if "UNIQUE constraint failed" in str(e):
                    raise ValueError(f"Group with name '{group.name}' already exists")
                raise

    def get_by_id(self, group_id: int) -> Optional[StockGroup]:
        """Get a group by ID."""
        with self.db_manager.session_scope() as session:
            stmt = select(StockGroup).where(StockGroup.id == group_id)
            result = session.execute(stmt).scalar_one_or_none()
            if result:
                session.expunge(result)
            return result

    def get_all(self) -> List[StockGroup]:
        """Get all groups sorted by sort_order."""
        with self.db_manager.session_scope() as session:
            stmt = select(StockGroup).order_by(StockGroup.sort_order, StockGroup.id)
            results = session.execute(stmt).scalars().all()
            for r in results:
                session.expunge(r)
            return list(results)

    def update(self, group_id: int, **kwargs) -> Optional[StockGroup]:
        """Update a group."""
        with self.db_manager.session_scope() as session:
            stmt = select(StockGroup).where(StockGroup.id == group_id)
            group = session.execute(stmt).scalar_one_or_none()
            if not group:
                return None

            for key, value in kwargs.items():
                if hasattr(group, key):
                    setattr(group, key, value)

            session.flush()
            session.refresh(group)
            session.expunge(group)
            return group

    def delete(self, group_id: int) -> bool:
        """Delete a group by ID."""
        with self.db_manager.session_scope() as session:
            stmt = delete(StockGroup).where(StockGroup.id == group_id)
            result = session.execute(stmt)
            return result.rowcount > 0
