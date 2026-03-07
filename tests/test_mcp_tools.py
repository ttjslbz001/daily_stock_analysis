# -*- coding: utf-8 -*-
"""Tests for MCP tools."""
import pytest
from unittest.mock import Mock, patch, AsyncMock


class TestAnalyzeStockTool:
    """Tests for analyze_stock MCP tool."""

    @pytest.mark.asyncio
    async def test_analyze_stock_valid_code(self):
        """Should return analysis result for valid stock code."""
        from src.mcp.tools.analysis import analyze_stock

        with patch("src.mcp.tools.analysis.get_task_service") as mock_service:
            mock_service.return_value.submit_analysis.return_value = {
                "success": True,
                "task_id": "test-task-id",
                "result": {"sentiment_score": 75}
            }

            result = await analyze_stock(stock_code="600519")
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_analyze_stock_invalid_code(self):
        """Should return error for invalid stock code."""
        from src.mcp.tools.analysis import analyze_stock

        result = await analyze_stock(stock_code="invalid")
        assert result["success"] is False
        assert "Invalid stock code" in result["error"]


class TestStocksTools:
    """Tests for stock-related MCP tools."""

    @pytest.mark.asyncio
    async def test_get_realtime_quote_valid(self):
        """Should return quote data for valid stock."""
        from src.mcp.tools.stocks import get_realtime_quote

        with patch("src.mcp.tools.stocks.DataFetcherManager") as mock_manager:
            mock_instance = Mock()
            mock_quote = Mock()
            mock_quote.code = "600519"
            mock_quote.name = "贵州茅台"
            mock_quote.price = 1850.0
            mock_quote.change_pct = 1.5
            mock_instance.get_realtime_quote.return_value = mock_quote
            mock_manager.return_value = mock_instance

            result = await get_realtime_quote(stock_code="600519")
            assert result["code"] == "600519"
            assert result["price"] == 1850.0

    @pytest.mark.asyncio
    async def test_get_market_indices(self):
        """Should return market index data."""
        from src.mcp.tools.stocks import get_market_indices

        with patch("src.mcp.tools.stocks.DataFetcherManager") as mock_manager:
            mock_instance = Mock()
            mock_instance.get_main_indices.return_value = [
                {"code": "000001", "name": "上证指数", "price": 3000.0}
            ]
            mock_manager.return_value = mock_instance

            result = await get_market_indices()
            assert len(result) > 0
