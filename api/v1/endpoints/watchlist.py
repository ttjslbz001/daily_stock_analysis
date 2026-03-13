# -*- coding: utf-8 -*-
"""Watchlist API endpoints."""

import logging

from fastapi import APIRouter, HTTPException, status

from api.v1.schemas.watchlist import (
    WatchlistItem,
    WatchlistResponse,
    AddStockResponse
)
from api.v1.schemas.common import ErrorResponse
from src.services.watchlist_service import WatchlistService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=WatchlistResponse,
    summary="获取自选股列表",
    description="获取所有自选股及其实时行情"
)
def list_watchlist():
    """List all watchlist stocks with quotes."""
    try:
        service = WatchlistService()
        stocks_data = service.get_all_with_quotes()

        # Convert dicts to WatchlistItem objects
        stocks = [WatchlistItem(**item) for item in stocks_data]

        return WatchlistResponse(
            stocks=stocks,
            total=len(stocks)
        )
    except Exception as e:
        logger.error(f"Failed to list watchlist: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": "获取自选股列表失败"}
        )


@router.post(
    "/{stock_code}",
    response_model=AddStockResponse,
    status_code=status.HTTP_200_OK,
    summary="添加自选股",
    description="添加股票到自选股列表"
)
def add_stock(stock_code: str):
    """Add a stock to watchlist."""
    try:
        service = WatchlistService()
        item = service.add_stock(stock_code)
        return AddStockResponse(
            stock_code=item.stock_code,
            added_at=item.added_at,
            message="添加成功"
        )
    except Exception as e:
        logger.error(f"Failed to add stock: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": "添加自选股失败"}
        )


@router.delete(
    "/{stock_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "股票不在自选股中", "model": ErrorResponse}
    },
    summary="删除自选股",
    description="从自选股列表中删除股票"
)
def remove_stock(stock_code: str):
    """Remove a stock from watchlist."""
    try:
        service = WatchlistService()
        removed = service.remove_stock(stock_code)

        if not removed:
            raise HTTPException(
                status_code=404,
                detail={"error": "not_found", "message": f"股票 {stock_code} 不在自选股中"}
            )

        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove stock: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": "删除自选股失败"}
        )
