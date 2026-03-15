# -*- coding: utf-8 -*-
"""
===================================
关注股票数据访问层
===================================

职责：
1. 封装关注股票的数据库操作
2. 提供 CRUD 接口
"""

import logging
from typing import List, Optional
from datetime import datetime

from sqlalchemy import and_, desc, select, delete
from sqlalchemy.orm import Session

from src.storage import DatabaseManager, WatchedStock
from src.analyzer import STOCK_NAME_MAP

logger = logging.getLogger(__name__)


class WatchedStocksRepository:
    """
    关注股票数据访问层

    封装 WatchedStock 表的数据库操作
    """

    DEFAULT_USER_ID = 'default_user'

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        初始化数据访问层

        Args:
            db_manager: 数据库管理器（可选，默认使用单例）
        """
        self.db = db_manager or DatabaseManager.get_instance()

    def add(self, stock_code: str, user_id: Optional[str] = None, stock_name: Optional[str] = None) -> bool:
        """
        添加关注股票

        Args:
            stock_code: 股票代码
            user_id: 用户 ID（可选，默认使用 'default_user'）
            stock_name: 股票名称（可选，未提供时尝试从 STOCK_NAME_MAP 获取）

        Returns:
            是否添加成功
        """
        user_id = user_id or self.DEFAULT_USER_ID

        try:
            with self.db.get_session() as session:
                # 检查是否已存在
                existing = session.execute(
                    select(WatchedStock).where(
                        and_(WatchedStock.user_id == user_id, WatchedStock.stock_code == stock_code)
                    )
                ).scalar_one_or_none()

                if existing:
                    logger.warning(f"股票 {stock_code} 已在用户 {user_id} 的关注列表中")
                    return False

                # 如果未提供股票名称，尝试从 STOCK_NAME_MAP 获取
                if not stock_name:
                    stock_name = STOCK_NAME_MAP.get(stock_code)

                # 创建新记录
                watched = WatchedStock(
                    user_id=user_id,
                    stock_code=stock_code,
                    stock_name=stock_name,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                session.add(watched)
                session.commit()

                logger.info(f"成功添加关注股票: {stock_code} ({stock_name})")
                return True

        except Exception as e:
            logger.error(f"添加关注股票失败: {e}", exc_info=True)
            return False

    def remove(self, stock_code: str, user_id: Optional[str] = None) -> bool:
        """
        取消关注股票

        Args:
            stock_code: 股票代码
            user_id: 用户 ID（可选，默认使用 'default_user'）

        Returns:
            是否删除成功
        """
        user_id = user_id or self.DEFAULT_USER_ID

        try:
            with self.db.get_session() as session:
                # 检查是否存在
                existing = session.execute(
                    select(WatchedStock).where(
                        and_(WatchedStock.user_id == user_id, WatchedStock.stock_code == stock_code)
                    )
                ).scalar_one_or_none()

                if not existing:
                    logger.warning(f"股票 {stock_code} 不在用户 {user_id} 的关注列表中")
                    return False

                # 删除记录
                session.execute(
                    delete(WatchedStock).where(
                        and_(WatchedStock.user_id == user_id, WatchedStock.stock_code == stock_code)
                    )
                )
                session.commit()

                logger.info(f"成功取消关注股票: {stock_code}")
                return True

        except Exception as e:
            logger.error(f"取消关注股票失败: {e}", exc_info=True)
            return False

    def list(self, user_id: Optional[str] = None) -> List[WatchedStock]:
        """
        获取关注股票列表

        Args:
            user_id: 用户 ID（可选，默认使用 'default_user'）

        Returns:
            WatchedStock 对象列表（按创建时间倒序）
        """
        user_id = user_id or self.DEFAULT_USER_ID

        try:
            with self.db.get_session() as session:
                result = session.execute(
                    select(WatchedStock)
                    .where(WatchedStock.user_id == user_id)
                    .order_by(desc(WatchedStock.created_at))
                ).scalars().all()
                return list(result)
        except Exception as e:
            logger.error(f"获取关注股票列表失败: {e}", exc_info=True)
            return []

    def exists(self, stock_code: str, user_id: Optional[str] = None) -> bool:
        """
        检查股票是否在关注列表中

        Args:
            stock_code: 股票代码
            user_id: 用户 ID（可选，默认使用 'default_user'）

        Returns:
            是否在关注列表中
        """
        user_id = user_id or self.DEFAULT_USER_ID

        try:
            with self.db.get_session() as session:
                result = session.execute(
                    select(WatchedStock).where(
                        and_(WatchedStock.user_id == user_id, WatchedStock.stock_code == stock_code)
                    )
                ).scalar_one_or_none()
                return result is not None
        except Exception as e:
            logger.error(f"检查关注股票是否存在失败: {e}", exc_info=True)
            return False

    def get_by_code(self, stock_code: str, user_id: Optional[str] = None) -> Optional[WatchedStock]:
        """
        根据股票代码获取关注记录

        Args:
            stock_code: 股票代码
            user_id: 用户 ID（可选，默认使用 'default_user'）

        Returns:
            WatchedStock 对象，不存在时返回 None
        """
        user_id = user_id or self.DEFAULT_USER_ID

        try:
            with self.db.get_session() as session:
                return session.execute(
                    select(WatchedStock).where(
                        and_(WatchedStock.user_id == user_id, WatchedStock.stock_code == stock_code)
                    )
                ).scalar_one_or_none()
        except Exception as e:
            logger.error(f"获取关注股票记录失败: {e}", exc_info=True)
            return None
