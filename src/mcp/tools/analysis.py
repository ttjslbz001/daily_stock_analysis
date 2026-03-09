# -*- coding: utf-8 -*-
"""
MCP Analysis Tools

Provides stock analysis tool for MCP server.
"""

import logging
import re
from typing import Dict, Any

from src.enums import ReportType
from src.services.task_service import get_task_service
from data_provider.base import canonical_stock_code

logger = logging.getLogger(__name__)


def validate_stock_code(code: str) -> bool:
    """Validate stock code format."""
    if not code:
        return False
    code = code.upper().strip()

    # A股: 6位数字
    is_a_stock = re.match(r'^\d{6}$', code)
    # 港股: HK + 5位数字
    is_hk_stock = re.match(r'^HK\d{5}$', code)
    # 美股: 1-5个字母
    is_us_stock = re.match(r'^[A-Z]{1,5}(\.[A-Z]{1,2})?$', code)

    return bool(is_a_stock or is_hk_stock or is_us_stock)


async def analyze_stock(
    stock_code: str,
    report_type: str = "simple",
    force_refresh: bool = False  # noqa: ARG001 - kept for API compatibility
) -> Dict[str, Any]:
    """
    Analyze a stock using AI.

    Args:
        stock_code: Stock code to analyze
        report_type: "simple" or "full"
        force_refresh: Force re-fetch data (currently not used)

    Returns:
        Analysis result with success status and data/error
    """
    # Validate stock code
    if not validate_stock_code(stock_code):
        return {
            "success": False,
            "error": f"Invalid stock code format: {stock_code}"
        }

    try:
        code = canonical_stock_code(stock_code)
        service = get_task_service()

        result = service.submit_analysis(
            code=code,
            report_type=ReportType.from_str(report_type),
            query_source="mcp"
        )

        if result.get("success"):
            return {
                "success": True,
                "task_id": result.get("task_id"),
                "stock_code": code,
                "message": f"Analysis submitted for {code}"
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Analysis failed")
            }

    except Exception as e:
        logger.error(f"analyze_stock failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }
