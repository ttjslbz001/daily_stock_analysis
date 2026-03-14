# -*- coding: utf-8 -*-
"""
板块看板数据服务

职责：
1. 获取板块涨跌数据
2. 管理数据缓存
3. 提供统一的数据接口
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from src.market_analyzer import MarketAnalyzer

logger = logging.getLogger(__name__)


class SectorService:
    """板块看板数据服务"""

    def __init__(self, cache_dir: Optional[str] = None):
        """
        初始化板块服务

        Args:
            cache_dir: 缓存目录，默认为 data/sectors
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path("data/sectors")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.market_analyzer = MarketAnalyzer(region='cn')

    def get_sector_board_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        获取板块看板数据

        Args:
            force_refresh: 是否强制刷新（跳过缓存）

        Returns:
            板块看板数据字典
        """
        date_str = datetime.now().strftime('%Y-%m-%d')
        cache_file = self.cache_dir / f"{date_str}.json"

        # 尝试读取缓存
        if not force_refresh and cache_file.exists():
            logger.info(f"读取缓存数据: {cache_file}")
            cached_data = self._load_cached_data(cache_file)
            if cached_data:
                return cached_data

        # 获取新数据
        logger.info("获取新的板块数据...")
        fresh_data = self._fetch_fresh_data()

        # 保存到缓存
        if fresh_data:
            self._save_to_cache(cache_file, fresh_data)

        return fresh_data

    def _fetch_fresh_data(self) -> Dict[str, Any]:
        """获取最新的板块数据"""
        try:
            # 获取市场概览
            overview = self.market_analyzer.get_market_overview()

            # 组装数据
            result = {
                "date": datetime.now().strftime('%Y-%m-%d'),
                "update_time": datetime.now().strftime('%H:%M:%S'),
                "market_overview": {
                    "up_count": overview.up_count,
                    "down_count": overview.down_count,
                    "flat_count": overview.flat_count,
                    "limit_up_count": overview.limit_up_count,
                    "limit_down_count": overview.limit_down_count,
                    "total_amount": overview.total_amount,
                },
                "top_sectors": self._format_sectors(overview.top_sectors),
                "bottom_sectors": self._format_sectors(overview.bottom_sectors),
            }

            return result

        except Exception as e:
            logger.error(f"获取板块数据失败: {e}")
            return {
                "date": datetime.now().strftime('%Y-%m-%d'),
                "update_time": datetime.now().strftime('%H:%M:%S'),
                "error": str(e),
                "market_overview": {},
                "top_sectors": [],
                "bottom_sectors": [],
            }

    def _format_sectors(self, sectors: list) -> list:
        """格式化板块数据"""
        formatted = []
        for idx, sector in enumerate(sectors[:10], start=1):
            formatted.append({
                "rank": idx,
                "name": sector.get("name", ""),
                "change_pct": sector.get("change_pct", 0.0),
                "leading_stock": sector.get("leading_stock", ""),
            })
        return formatted

    def _load_cached_data(self, cache_file: Path) -> Optional[Dict[str, Any]]:
        """加载缓存数据"""
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载缓存失败: {e}")
            return None

    def _save_to_cache(self, cache_file: Path, data: Dict[str, Any]) -> None:
        """保存数据到缓存"""
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"数据已缓存到: {cache_file}")
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
