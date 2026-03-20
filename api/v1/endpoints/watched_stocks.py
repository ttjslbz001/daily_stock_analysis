# -*- coding: utf-8 -*-
"""
===================================
关注股票 API 端点
===================================

职责：
1. GET /api/v1/watched - 获取关注股票列表（仅基本信息）
2. GET /api/v1/watched/full - 获取关注股票完整列表（含指标）
3. GET /api/v1/watched/{stock_code}/indicators - 获取单只股票指标
4. POST /api/v1/watched - 添加关注股票
5. DELETE /api/v1/watched/{stock_code} - 取消关注股票
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta

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
    KDJ,
)
from src.repositories.watched_stocks_repo import WatchedStocksRepository
from src.services.technical_indicators_service import TechnicalIndicatorsService

logger = logging.getLogger(__name__)

router = APIRouter()

DEFAULT_USER_ID = "default_user"
CACHE_DURATION_HOURS = 12  # 缓存有效期：12小时


def _is_cache_valid(watched_stock) -> bool:
    """检查缓存是否有效（12小时内）"""
    if not watched_stock.indicators_cached_at:
        return False
    return watched_stock.indicators_cached_at > datetime.now() - timedelta(hours=CACHE_DURATION_HOURS)


def _build_response_from_cache(watched_stock) -> WatchedStockResponse:
    """从缓存构建响应"""
    return WatchedStockResponse(
        stock_code=watched_stock.stock_code,
        stock_name=watched_stock.stock_name or watched_stock.stock_code,
        market=getattr(watched_stock, 'market', None),
        current_price=watched_stock.cached_price or 0.0,
        change=watched_stock.cached_change,
        change_percent=watched_stock.cached_change_percent,
        day_high=getattr(watched_stock, 'cached_day_high', None),
        day_low=getattr(watched_stock, 'cached_day_low', None),
        year_high=watched_stock.cached_year_high,
        year_low=watched_stock.cached_year_low,
        bollinger=BollingerBands(
            upper=watched_stock.cached_bollinger_upper or 0.0,
            middle=watched_stock.cached_bollinger_middle or 0.0,
            lower=watched_stock.cached_bollinger_lower or 0.0
        ),
        macd=MACD(
            dif=watched_stock.cached_macd_dif or 0.0,
            dea=watched_stock.cached_macd_dea or 0.0,
            bar=watched_stock.cached_macd_bar or 0.0
        ),
        rsi=RSI(
            rsi6=watched_stock.cached_rsi6 or 0.0,
            rsi12=watched_stock.cached_rsi12 or 0.0,
            rsi24=watched_stock.cached_rsi24 or 0.0
        ),
        kdj=KDJ(
            k=watched_stock.cached_kdj_k or 0.0,
            d=watched_stock.cached_kdj_d or 0.0,
            j=watched_stock.cached_kdj_j or 0.0
        ),
        volume=watched_stock.cached_volume or 0.0,
        updated_at=watched_stock.indicators_cached_at or datetime.now()
    )


@router.get(
    "",
    response_model=WatchedStocksListResponse,
    summary="获取关注股票列表（轻量）",
    description="获取当前用户的关注股票列表，仅包含基本信息，不包含技术指标"
)
def get_watched_stocks():
    """
    获取关注股票列表（轻量版，快速返回）

    返回用户关注的股票列表，仅包含代码和名称，不包含价格和指标
    前端应单独调用 /{stock_code}/indicators 获取每只股票的详细数据
    """
    try:
        repo = WatchedStocksRepository()
        watched = repo.list(DEFAULT_USER_ID)

        if not watched:
            return WatchedStocksListResponse(total=0, items=[])

        # 返回基本信息，不获取指标
        items = []
        for ws in watched:
            items.append(WatchedStockResponse(
                stock_code=ws.stock_code,
                stock_name=ws.stock_name or ws.stock_code,
                market=getattr(ws, 'market', None),
                current_price=0.0,
                change=None,
                change_percent=None,
                day_high=None,
                day_low=None,
                year_high=None,
                year_low=None,
                bollinger=BollingerBands(upper=0.0, middle=0.0, lower=0.0),
                macd=MACD(dif=0.0, dea=0.0, bar=0.0),
                rsi=RSI(rsi6=0.0, rsi12=0.0, rsi24=0.0),
                kdj=KDJ(k=0.0, d=0.0, j=0.0),
                volume=0.0,
                updated_at=ws.updated_at or datetime.now()
            ))

        return WatchedStocksListResponse(total=len(items), items=items)

    except Exception as e:
        logger.error(f"获取关注股票列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": f"获取关注股票列表失败: {str(e)}"}
        )


@router.get(
    "/{stock_code}/indicators",
    response_model=WatchedStockResponse,
    summary="获取单只股票的技术指标",
    description="获取指定股票的实时价格和技术指标（支持12小时缓存）"
)
def get_stock_indicators(
    stock_code: str,
    force_refresh: bool = Query(False, description="强制刷新，忽略缓存")
):
    """
    获取单只股票的技术指标

    返回指定股票的实时价格、涨跌幅和技术指标
    如果缓存有效（12小时内）且 force_refresh=False，直接返回缓存数据
    """
    try:
        repo = WatchedStocksRepository()

        # 获取股票信息
        watched_stock = repo.get_by_code(stock_code, DEFAULT_USER_ID)
        if not watched_stock:
            raise HTTPException(
                status_code=404,
                detail={"error": "not_found", "message": "股票不在关注列表中"}
            )

        # 检查缓存是否有效
        if not force_refresh and _is_cache_valid(watched_stock):
            logger.debug(f"使用缓存数据: {stock_code}")
            return _build_response_from_cache(watched_stock)

        # 获取新的技术指标
        logger.info(f"获取新鲜指标: {stock_code}")
        indicator_service = TechnicalIndicatorsService()
        indicators = indicator_service.get_indicators([stock_code])
        data = indicators.get(stock_code, {})

        bollinger_data = data.get('bollinger', {})
        macd_data = data.get('macd', {})
        rsi_data = data.get('rsi', {})
        kdj_data = data.get('kdj', {})

        # 更新缓存
        cache_data = {
            'price': data.get('price', 0.0),
            'change': data.get('change'),
            'change_percent': data.get('change_percent'),
            'stock_name': data.get('stock_name'),
            'bollinger': bollinger_data,
            'macd': macd_data,
            'rsi': rsi_data,
            'kdj': kdj_data,
            'volume': data.get('volume'),
            'day_high': data.get('day_high'),
            'day_low': data.get('day_low'),
            'year_high': data.get('year_high'),
            'year_low': data.get('year_low'),
        }
        repo.update_cached_indicators(stock_code, cache_data, DEFAULT_USER_ID)

        # Update stored stock_name if we got a better one from the data source
        resolved_name = data.get('stock_name') or watched_stock.stock_name or stock_code
        if resolved_name and resolved_name != stock_code and watched_stock.stock_name in (None, '', stock_code):
            try:
                repo.update_stock_name(stock_code, resolved_name, DEFAULT_USER_ID)
            except Exception:
                pass

        return WatchedStockResponse(
            stock_code=stock_code,
            stock_name=resolved_name,
            market=getattr(watched_stock, 'market', None),
            current_price=data.get('price', 0.0),
            change=data.get('change'),
            change_percent=data.get('change_percent'),
            day_high=data.get('day_high'),
            day_low=data.get('day_low'),
            year_high=data.get('year_high'),
            year_low=data.get('year_low'),
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
            kdj=KDJ(
                k=kdj_data.get('k', 0.0),
                d=kdj_data.get('d', 0.0),
                j=kdj_data.get('j', 0.0)
            ),
            volume=data.get('volume', 0.0),
            updated_at=datetime.now()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取股票指标失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": f"获取股票指标失败: {str(e)}"}
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

    将指定的股票添加到用户的关注列表中。
    如果未提供股票名称，自动从数据源解析。
    """
    try:
        repo = WatchedStocksRepository()

        if repo.exists(request.stock_code, DEFAULT_USER_ID):
            return AddWatchedStockResponse(
                success=False,
                message="股票已在关注列表中",
                stock_code=request.stock_code
            )

        # Auto-resolve stock name if not provided
        stock_name = request.stock_name
        if not stock_name:
            try:
                from data_provider.base import DataFetcherManager
                manager = DataFetcherManager()
                stock_name = manager.get_stock_name(request.stock_code) or None
            except Exception as e:
                logger.warning(f"Auto-resolve stock name failed for {request.stock_code}: {e}")

        success = repo.add(request.stock_code, DEFAULT_USER_ID, stock_name)
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
        if not repo.exists(stock_code, DEFAULT_USER_ID):
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
