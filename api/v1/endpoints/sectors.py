# -*- coding: utf-8 -*-
"""板块看板API端点"""

import logging
from fastapi import APIRouter, Query, HTTPException

from src.sector_service import SectorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sectors", tags=["板块看板"])


@router.get("/board")
async def get_sector_board(
    force_refresh: bool = Query(False, description="强制刷新数据")
):
    """
    获取板块看板数据

    Args:
        force_refresh: 是否强制刷新（跳过缓存）

    Returns:
        板块看板数据，包含市场概况和涨跌板块榜
    """
    try:
        service = SectorService()
        data = service.get_sector_board_data(force_refresh=force_refresh)

        if not data:
            raise HTTPException(status_code=500, detail="获取板块数据失败")

        return data

    except Exception as e:
        logger.error(f"获取板块看板数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
