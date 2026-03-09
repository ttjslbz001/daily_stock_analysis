# -*- coding: utf-8 -*-
"""
MCP Server Implementation

Provides SSE-based MCP server for AI agent integration.
"""

import logging
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent

from src.config import get_config
from src.mcp.auth import validate_mcp_api_key
from src.mcp.tools import (
    analyze_stock,
    get_realtime_quote,
    search_stocks,
    get_market_indices,
)

logger = logging.getLogger(__name__)

# MCP Server instance
_mcp_server: Optional[Server] = None


def create_mcp_server() -> Server:
    """Create and configure MCP server with tools."""
    server = Server("daily-stock-analysis")

    @server.list_tools()
    async def list_tools():
        """Return available MCP tools."""
        return [
            Tool(
                name="analyze_stock",
                description="Analyze a stock using AI. Returns sentiment score, trend prediction, and operation advice.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "stock_code": {
                            "type": "string",
                            "description": "Stock code (e.g., '600519', 'AAPL', 'HK00700')"
                        },
                        "report_type": {
                            "type": "string",
                            "enum": ["simple", "full"],
                            "default": "simple",
                            "description": "Report detail level"
                        },
                        "force_refresh": {
                            "type": "boolean",
                            "default": False,
                            "description": "Force re-fetch data"
                        }
                    },
                    "required": ["stock_code"]
                }
            ),
            Tool(
                name="get_realtime_quote",
                description="Get real-time stock price and metrics.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "stock_code": {
                            "type": "string",
                            "description": "Stock code"
                        }
                    },
                    "required": ["stock_code"]
                }
            ),
            Tool(
                name="search_stocks",
                description="Search stocks by keyword or code.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "keyword": {
                            "type": "string",
                            "description": "Search keyword"
                        },
                        "limit": {
                            "type": "integer",
                            "default": 10,
                            "description": "Max results"
                        }
                    },
                    "required": ["keyword"]
                }
            ),
            Tool(
                name="get_market_indices",
                description="Get current market index data (上证指数, 深证成指, etc.).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "region": {
                            "type": "string",
                            "enum": ["cn", "us", "both"],
                            "default": "cn",
                            "description": "Market region"
                        }
                    }
                }
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        """Execute MCP tool."""
        try:
            if name == "analyze_stock":
                result = await analyze_stock(**arguments)
            elif name == "get_realtime_quote":
                result = await get_realtime_quote(**arguments)
            elif name == "search_stocks":
                result = await search_stocks(**arguments)
            elif name == "get_market_indices":
                result = await get_market_indices(**arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")

            return [TextContent(type="text", text=str(result))]

        except Exception as e:
            logger.error(f"Tool {name} failed: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    return server


def setup_mcp(app: FastAPI) -> None:
    """
    Setup MCP server on FastAPI app.

    Adds /mcp SSE endpoint for MCP protocol.

    Args:
        app: FastAPI application instance
    """
    config = get_config()

    if not config.mcp_enabled:
        logger.info("MCP server disabled")
        return

    global _mcp_server
    _mcp_server = create_mcp_server()
    sse = SseServerTransport("/mcp")

    @app.get("/mcp")
    async def handle_mcp_sse(request: Request):
        """Handle MCP SSE connection (GET for receiving events)."""
        # Validate API key
        provided_key = request.headers.get("X-MCP-Key")
        if not validate_mcp_api_key(provided_key, config.mcp_api_key):
            raise HTTPException(status_code=401, detail="Invalid MCP API key")

        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send,
        ) as (reader, writer):
            await _mcp_server.run(
                reader,
                writer,
                _mcp_server.create_initialization_options(),
            )

    @app.post("/mcp")
    async def handle_mcp_post(request: Request):
        """Handle MCP POST requests (for sending messages to server)."""
        # Validate API key
        provided_key = request.headers.get("X-MCP-Key")
        if not validate_mcp_api_key(provided_key, config.mcp_api_key):
            raise HTTPException(status_code=401, detail="Invalid MCP API key")

        # Use SseServerTransport's handle_post_message for POST requests
        await sse.handle_post_message(request.scope, request.receive, request._send)

    logger.info("MCP server initialized at /mcp")
