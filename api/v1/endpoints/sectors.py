# -*- coding: utf-8 -*-
"""板块看板API端点"""

import logging
import time
from typing import Dict, List, Any

from fastapi import APIRouter, Query, HTTPException

from src.sector_service import SectorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sectors", tags=["板块看板"])

# Tracked sectors with representative ETF/index codes for performance calc
TRACKED_SECTORS: List[Dict[str, str]] = [
    {"name": "国有银行", "code": "BK0596"},
    {"name": "半导体", "code": "BK1036"},
    {"name": "半导体设备", "code": "BK1080"},
    {"name": "AI应用", "code": "BK1144"},
    {"name": "AI算力", "code": "BK1146"},
]

# Simple in-memory cache for tracked sectors (TTL 30 min)
_tracked_cache: Dict[str, Any] = {"data": None, "ts": 0, "ttl": 1800}


@router.get("/board")
async def get_sector_board(
    force_refresh: bool = Query(False, description="强制刷新数据")
):
    """获取板块看板数据"""
    try:
        service = SectorService()
        data = service.get_sector_board_data(force_refresh=force_refresh)

        if not data:
            raise HTTPException(status_code=500, detail="获取板块数据失败")

        return data

    except Exception as e:
        logger.error(f"获取板块看板数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tracked")
async def get_tracked_sectors(
    force_refresh: bool = Query(False, description="强制刷新数据")
):
    """
    Get performance data for tracked A-share sectors.

    Returns 1-week, 1-month, and 6-month change percentages
    for predefined sectors (banks, semiconductor, AI, etc.).
    """
    now = time.time()
    if not force_refresh and _tracked_cache["data"] and (now - _tracked_cache["ts"]) < _tracked_cache["ttl"]:
        return _tracked_cache["data"]

    try:
        import akshare as ak
        import pandas as pd
        from datetime import datetime, timedelta

        results = []
        today = datetime.now()
        periods = {
            "1w": today - timedelta(weeks=1),
            "1m": today - timedelta(days=30),
            "6m": today - timedelta(days=180),
        }

        for sector in TRACKED_SECTORS:
            sector_result: Dict[str, Any] = {
                "name": sector["name"],
                "code": sector["code"],
                "change_1w": None,
                "change_1m": None,
                "change_6m": None,
                "current": None,
            }

            try:
                df = ak.stock_board_industry_hist_em(
                    symbol=sector["name"],
                    period="日k",
                    start_date=(today - timedelta(days=200)).strftime("%Y%m%d"),
                    end_date=today.strftime("%Y%m%d"),
                    adjust="",
                )

                if df is not None and not df.empty:
                    df["日期"] = pd.to_datetime(df["日期"])
                    df = df.sort_values("日期").reset_index(drop=True)

                    latest_close = float(df.iloc[-1]["收盘"])
                    sector_result["current"] = latest_close

                    for period_key, start_dt in periods.items():
                        past_df = df[df["日期"] <= start_dt]
                        if not past_df.empty:
                            base_close = float(past_df.iloc[-1]["收盘"])
                            if base_close > 0:
                                pct = round((latest_close - base_close) / base_close * 100, 2)
                                sector_result[f"change_{period_key}"] = pct

            except Exception as e:
                logger.warning(f"Failed to fetch sector {sector['name']}: {e}")

            results.append(sector_result)

        response = {
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "sectors": results,
        }
        _tracked_cache["data"] = response
        _tracked_cache["ts"] = now
        return response

    except Exception as e:
        logger.error(f"获取关注板块数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
