# -*- coding: utf-8 -*-
"""
===================================
关注股票 API 端点
===================================

职责：
1. GET /api/v1/watched - 获取关注股票列表
2. POST /api/v1/watched - 添加关注股票
3. DELETE /api/v1/watched/{stock_code} - 取消关注股票
"""

import logging
from typing import List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from api.v1.schemas.watched_stocks import (
    WatchedStockResponse,
    WatchedStocksListResponse,
    AddWatchedStockRequest,
    AddWatchedStockResponse,
    RemoveWatchedStockResponse,
    BollingerBands,
    MACD,
    RSI,
)
from src.repositories.watched_stocks_repo import WatchedStocksRepository
from src.services.technical_indicators_service import TechnicalIndicatorsService

logger = logging.getLogger(__name__)

router = APIRouter()

DEFAULT_USER_ID = "default_user"


@router.get(
    "",
    response_model=WatchedStocksListResponse,
    summary="获取关注股票列表",
    description="获取当前用户的关注股票列表，包含实时价格和技术指标"
)
def get_watched_stocks():
    """
    获取关注股票列表

    返回用户关注的股票列表，包含实时价格、涨跌幅和各类技术指标（布林线、MACD、RSI）
    """
    try:
        repo = WatchedStocksRepository()
        indicator_service = TechnicalIndicatorsService()

        # 获取关注的股票
        watched = repo.list(DEFAULT_USER_ID)
        stock_codes = [ws.stock_code for ws in watched]

        if not stock_codes:
            return WatchedStocksListResponse(total=0, items=[])

        # 批量获取技术指标
        indicators = indicator_service.get_indicators(stock_codes)

        # 构建响应
        items = []
        for ws in watched:
            code = ws.stock_code
            data = indicators.get(code, {})

            # 确保所有必需字段都有值
            bollinger_data = data.get('bollinger', {})
            macd_data = data.get('macd', {})
            rsi_data = data.get('rsi', {})

            items.append(WatchedStockResponse(
                stock_code=code,
                stock_name=data.get('stock_name', ws.stock_name or code),
                current_price=data.get('price', 0.0),
                change=data.get('change'),
                change_percent=data.get('change_percent'),
                bollinger=BollingerBands(
                    upper=bollinger_data.get('upper', 0.0),
                    middle=bollinger_data.get('middle', 0.0),
                    lower=bollinger_data.get('lower', 0.0)
                ),
                macd=MACD(
                    dif=macd_data.get('dif', 0.0),
                    dea=macd_data.get('dea', 0.0),
                    bar=macd_data.get('bar', 0.0)
                ),
                rsi=RSI(
                    rsi6=rsi_data.get('rsi6', 0.0),
                    rsi12=rsi_data.get('rsi12', 0.0),
                    rsi24=rsi_data.get('rsi24', 0.0)
                ),
                updated_at=ws.updated_at or datetime.now()
            ))

        return WatchedStocksListResponse(total=len(items), items=items)

    except Exception as e:
        logger.error(f"获取关注股票列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": f"获取关注股票列表失败: {str(e)}"}
        )


@router.post(
    "",
    response_model=AddWatchedStockResponse,
    summary="添加关注股票",
    description="添加股票到关注列表"
)
def add_watched_stock(request: AddWatchedStockRequest):
    """
    添加关注股票

    将指定的股票添加到用户的关注列表中
    """
    try:
        repo = WatchedStocksRepository()

        # 检查是否已存在
        if repo.exists(DEFAULT_USER_ID, request.stock_code):
            return AddWatchedStockResponse(
                success=False,
                message="股票已在关注列表中",
                stock_code=request.stock_code
            )

        # 添加到关注列表
        success = repo.add(request.stock_code, DEFAULT_USER_ID, request.stock_name)
        if success:
            return AddWatchedStockResponse(
                success=True,
                message="添加成功",
                stock_code=request.stock_code
            )
        else:
            raise HTTPException(
                status_code=500,
                detail={"error": "internal_error", "message": "添加失败"}
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加关注股票失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": f"添加关注股票失败: {str(e)}"}
        )


@router.delete(
    "/{stock_code}",
    response_model=RemoveWatchedStockResponse,
    summary="取消关注股票",
    description="从关注列表中移除指定的股票"
)
def remove_watched_stock(stock_code: str):
    """
    取消关注股票

    从用户的关注列表中移除指定的股票
    """
    try:
        repo = WatchedStocksRepository()

        # 检查是否存在
        if not repo.exists(DEFAULT_USER_ID, stock_code):
            raise HTTPException(
                status_code=404,
                detail={"error": "not_found", "message": "股票不在关注列表中"}
            )

        # 从关注列表中移除
        success = repo.remove(stock_code, DEFAULT_USER_ID)
        if success:
            return RemoveWatchedStockResponse(
                success=True,
                message="取消关注成功",
                stock_code=stock_code
            )
        else:
            raise HTTPException(
                status_code=500,
                detail={"error": "internal_error", "message": "取消关注失败"}
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消关注股票失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": f"取消关注股票失败: {str(e)}"}
        )
