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
import math
from typing import List, Optional
from datetime import datetime

from sqlalchemy import and_, desc, select, delete
from sqlalchemy.orm import Session

from src.storage import DatabaseManager, WatchedStock
from src.analyzer import STOCK_NAME_MAP

logger = logging.getLogger(__name__)


def _sanitize_float(v) -> Optional[float]:
    """Convert NaN/Inf to None for SQLite compatibility."""
    if v is None:
        return None
    try:
        f = float(v)
        if math.isfinite(f):
            return f
    except (TypeError, ValueError):
        pass
    return None


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

    def add(
        self,
        stock_code: str,
        user_id: Optional[str] = None,
        stock_name: Optional[str] = None,
        market: Optional[str] = None,
    ) -> bool:
        """
        Add a stock to the watch list.

        Args:
            stock_code: Stock code
            user_id: User ID (defaults to 'default_user')
            stock_name: Display name (auto-resolved from STOCK_NAME_MAP if not given)
            market: Market identifier — CN, HK, or US (auto-detected if not given)
        """
        user_id = user_id or self.DEFAULT_USER_ID

        try:
            with self.db.get_session() as session:
                existing = session.execute(
                    select(WatchedStock).where(
                        and_(WatchedStock.user_id == user_id, WatchedStock.stock_code == stock_code)
                    )
                ).scalar_one_or_none()

                if existing:
                    logger.warning(f"Stock {stock_code} already watched by {user_id}")
                    return False

                if not stock_name:
                    stock_name = STOCK_NAME_MAP.get(stock_code)

                # Auto-detect market from code if not provided
                if not market:
                    try:
                        from data_provider.base import detect_market
                        market = detect_market(stock_code)
                    except Exception:
                        market = None

                watched = WatchedStock(
                    user_id=user_id,
                    stock_code=stock_code,
                    stock_name=stock_name,
                    market=market,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                session.add(watched)
                session.commit()

                logger.info(f"Added watched stock: {stock_code} ({stock_name}) market={market}")
                return True

        except Exception as e:
            logger.error(f"Failed to add watched stock: {e}", exc_info=True)
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
            Note: Returns a list of WatchedStock objects with all attributes loaded
        """
        user_id = user_id or self.DEFAULT_USER_ID

        try:
            with self.db.get_session() as session:
                result = session.execute(
                    select(WatchedStock)
                    .where(WatchedStock.user_id == user_id)
                    .order_by(desc(WatchedStock.created_at))
                ).scalars().all()
                # Convert to list and ensure all attributes are loaded
                # This prevents DetachedInstanceError when accessing attributes later
                return [
                    WatchedStock(
                        id=stock.id,
                        user_id=stock.user_id,
                        stock_code=stock.stock_code,
                        stock_name=stock.stock_name,
                        market=stock.market,
                        cached_price=stock.cached_price,
                        cached_change=stock.cached_change,
                        cached_change_percent=stock.cached_change_percent,
                        cached_bollinger_upper=stock.cached_bollinger_upper,
                        cached_bollinger_middle=stock.cached_bollinger_middle,
                        cached_bollinger_lower=stock.cached_bollinger_lower,
                        cached_macd_dif=stock.cached_macd_dif,
                        cached_macd_dea=stock.cached_macd_dea,
                        cached_macd_bar=stock.cached_macd_bar,
                        cached_rsi6=stock.cached_rsi6,
                        cached_rsi12=stock.cached_rsi12,
                        cached_rsi24=stock.cached_rsi24,
                        cached_kdj_k=stock.cached_kdj_k,
                        cached_kdj_d=stock.cached_kdj_d,
                        cached_kdj_j=stock.cached_kdj_j,
                        cached_volume=stock.cached_volume,
                        cached_year_high=stock.cached_year_high,
                        cached_year_low=stock.cached_year_low,
                        indicators_cached_at=stock.indicators_cached_at,
                        created_at=stock.created_at,
                        updated_at=stock.updated_at,
                    )
                    for stock in result
                ]
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

    def update_stock_name(self, stock_code: str, stock_name: str, user_id: Optional[str] = None) -> bool:
        """Update the stored display name for a watched stock."""
        user_id = user_id or self.DEFAULT_USER_ID
        try:
            with self.db.get_session() as session:
                watched = session.execute(
                    select(WatchedStock).where(
                        and_(WatchedStock.user_id == user_id, WatchedStock.stock_code == stock_code)
                    )
                ).scalar_one_or_none()
                if watched:
                    watched.stock_name = stock_name
                    session.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"update_stock_name failed: {e}", exc_info=True)
            return False

    def update_cached_indicators(
        self,
        stock_code: str,
        indicators: dict,
        user_id: Optional[str] = None
    ) -> bool:
        """
        更新缓存的指标数据

        Args:
            stock_code: 股票代码
            indicators: 指标数据字典
            user_id: 用户 ID（可选，默认使用 'default_user'）

        Returns:
            是否更新成功
        """
        user_id = user_id or self.DEFAULT_USER_ID

        try:
            with self.db.get_session() as session:
                watched = session.execute(
                    select(WatchedStock).where(
                        and_(WatchedStock.user_id == user_id, WatchedStock.stock_code == stock_code)
                    )
                ).scalar_one_or_none()

                if not watched:
                    logger.warning(f"股票 {stock_code} 不在关注列表中")
                    return False

                # Sanitize floats (NaN/Inf -> None) for SQLite compatibility
                def _f(key): return _sanitize_float(indicators.get(key))
                def _fd(d, key): return _sanitize_float(d.get(key)) if isinstance(d, dict) else None

                bollinger = indicators.get('bollinger', {}) or {}
                macd = indicators.get('macd', {}) or {}
                rsi = indicators.get('rsi', {}) or {}
                kdj = indicators.get('kdj', {}) or {}

                # 更新缓存的指标
                watched.cached_price = _f('price')
                watched.cached_change = _f('change')
                watched.cached_change_percent = _f('change_percent')

                watched.cached_bollinger_upper = _fd(bollinger, 'upper')
                watched.cached_bollinger_middle = _fd(bollinger, 'middle')
                watched.cached_bollinger_lower = _fd(bollinger, 'lower')

                watched.cached_macd_dif = _fd(macd, 'dif')
                watched.cached_macd_dea = _fd(macd, 'dea')
                watched.cached_macd_bar = _fd(macd, 'bar')

                watched.cached_rsi6 = _fd(rsi, 'rsi6')
                watched.cached_rsi12 = _fd(rsi, 'rsi12')
                watched.cached_rsi24 = _fd(rsi, 'rsi24')

                watched.cached_kdj_k = _fd(kdj, 'k')
                watched.cached_kdj_d = _fd(kdj, 'd')
                watched.cached_kdj_j = _fd(kdj, 'j')

                watched.cached_volume = _f('volume')
                watched.cached_year_high = _f('year_high')
                watched.cached_year_low = _f('year_low')

                # 更新股票名称（如果接口返回了）
                if indicators.get('stock_name'):
                    watched.stock_name = indicators.get('stock_name')

                watched.indicators_cached_at = datetime.now()
                watched.updated_at = datetime.now()

                session.commit()
                return True

        except Exception as e:
            logger.error(f"更新缓存指标失败 [{stock_code}]: {e}", exc_info=True)
            return False
