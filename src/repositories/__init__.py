# -*- coding: utf-8 -*-
"""
===================================
数据访问层模块初始化
===================================

职责：
1. 导出所有 Repository 类
2. 导出基础 Repository 类
"""

from src.repositories.analysis_repo import AnalysisRepository
from src.repositories.backtest_repo import BacktestRepository
from src.repositories.stock_repo import StockRepository
from src.repositories.watched_stocks_repo import WatchedStocksRepository
from src.repositories.watchlist_repo import WatchlistRepository
from src.repositories.base import BaseRepository

__all__ = [
    "AnalysisRepository",
    "BacktestRepository",
    "StockRepository",
    "WatchedStocksRepository",
    "WatchlistRepository",
    "BaseRepository",
]
