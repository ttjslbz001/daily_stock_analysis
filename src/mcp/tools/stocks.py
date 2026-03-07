# -*- coding: utf-8 -*-
"""
MCP Stock Data Tools

Provides stock data tools for MCP server.
"""

import logging
from typing import Dict, Any, List, Optional

from data_provider.base import DataFetcherManager, canonical_stock_code

logger = logging.getLogger(__name__)


async def get_realtime_quote(stock_code: str) -> Dict[str, Any]:
    """
    Get real-time stock quote.

    Args:
        stock_code: Stock code

    Returns:
        Quote data with price, change, volume metrics
    """
    try:
        code = canonical_stock_code(stock_code)
        manager = DataFetcherManager()
        quote = manager.get_realtime_quote(code)

        if quote is None:
            return {
                "success": False,
                "error": f"Stock {stock_code} not found"
            }

        return {
            "success": True,
            "code": quote.code,
            "name": quote.name,
            "price": quote.price,
            "change_pct": quote.change_pct,
            "volume": quote.volume,
            "amount": quote.amount,
            "volume_ratio": quote.volume_ratio,
            "turnover_rate": quote.turnover_rate,
            "pe_ratio": quote.pe_ratio,
            "pb_ratio": quote.pb_ratio,
            "total_mv": quote.total_mv,
        }

    except Exception as e:
        logger.error(f"get_realtime_quote failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def search_stocks(keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search stocks by keyword.

    Args:
        keyword: Search keyword
        limit: Max results

    Returns:
        List of matching stocks
    """
    try:
        manager = DataFetcherManager()
        results = manager.search_stocks(keyword, limit=limit)

        return [
            {
                "code": r.get("code"),
                "name": r.get("name"),
                "market": r.get("market", ""),
            }
            for r in results
        ]

    except Exception as e:
        logger.error(f"search_stocks failed: {e}")
        return []


async def get_market_indices(region: str = "cn") -> List[Dict[str, Any]]:
    """
    Get market index data.

    Args:
        region: "cn", "us", or "both"

    Returns:
        List of market indices
    """
    try:
        manager = DataFetcherManager()
        indices = manager.get_main_indices(region=region)

        return [
            {
                "code": idx.get("code"),
                "name": idx.get("name"),
                "price": idx.get("price"),
                "change_pct": idx.get("change_pct"),
            }
            for idx in indices
        ]

    except Exception as e:
        logger.error(f"get_market_indices failed: {e}")
        return []
