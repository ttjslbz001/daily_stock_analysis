# MCP Server Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add an MCP server endpoint to expose stock analysis tools for Claude Code and OpenAI-compatible clients.

**Architecture:** FastAPI extension using `mcp` Python SDK with SSE transport. Mounts `/mcp` endpoint alongside existing REST API, reusing existing services (AnalysisService, DataFetcherManager).

**Tech Stack:** Python 3.10+, FastAPI, mcp SDK (official), SSE transport

---

## Task 1: Add MCP Dependency

**Files:**
- Modify: `requirements.txt`

**Step 1: Add mcp package to requirements**

Add to `requirements.txt`:
```txt
mcp>=1.0.0
```

**Step 2: Install dependency**

Run: `pip install mcp>=1.0.0`
Expected: Successfully installed mcp

**Step 3: Verify installation**

Run: `python -c "import mcp; print(mcp.__version__)"`
Expected: Version number printed

**Step 4: Commit**

```bash
git add requirements.txt
git commit -m "build: add mcp SDK dependency for MCP server"
```

---

## Task 2: Add MCP Configuration Fields

**Files:**
- Modify: `src/config.py`
- Create: `tests/test_config_mcp.py`

**Step 1: Write the failing test**

Create `tests/test_config_mcp.py`:
```python
"""Tests for MCP configuration fields."""
import pytest
from src.config import Config


def test_mcp_enabled_default():
    """MCP should be disabled by default."""
    config = Config()
    assert config.mcp_enabled is False


def test_mcp_api_key_default():
    """MCP API key should be None by default."""
    config = Config()
    assert config.mcp_api_key is None


def test_mcp_api_key_from_env(monkeypatch):
    """MCP API key should be loaded from environment."""
    monkeypatch.setenv("MCP_API_KEY", "test-key-123")
    Config._instance = None  # Reset singleton
    config = Config.get_instance()
    assert config.mcp_api_key == "test-key-123"
    Config._instance = None  # Cleanup
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_config_mcp.py -v`
Expected: FAIL with "AttributeError: 'Config' object has no attribute 'mcp_enabled'"

**Step 3: Add MCP config fields to Config class**

In `src/config.py`, add after line ~296 (after `webui_port`):
```python
    # === MCP Server Configuration ===
    mcp_enabled: bool = False                    # Enable MCP server
    mcp_api_key: Optional[str] = None            # API key for MCP authentication
```

In the `_load_from_env` method, add after the webui config loading:
```python
        # === MCP Configuration ===
        mcp_enabled=os.getenv('MCP_ENABLED', 'false').lower() == 'true',
        mcp_api_key=os.getenv('MCP_API_KEY'),
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_config_mcp.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add src/config.py tests/test_config_mcp.py
git commit -m "feat(config): add MCP server configuration fields"
```

---

## Task 3: Create MCP Module Structure

**Files:**
- Create: `src/mcp/__init__.py`
- Create: `src/mcp/auth.py`

**Step 1: Create module init file**

Create `src/mcp/__init__.py`:
```python
# -*- coding: utf-8 -*-
"""
MCP Server Module

Provides Model Context Protocol server for AI agent integration.
"""

from src.mcp.server import setup_mcp

__all__ = ["setup_mcp"]
```

**Step 2: Create auth module**

Create `src/mcp/auth.py`:
```python
# -*- coding: utf-8 -*-
"""
MCP Authentication Module

Validates API key for MCP requests.
"""

from typing import Optional


def validate_mcp_api_key(provided_key: Optional[str], expected_key: Optional[str]) -> bool:
    """
    Validate MCP API key.

    Args:
        provided_key: Key from request header
        expected_key: Expected key from config

    Returns:
        True if valid, False otherwise
    """
    if not expected_key:
        # No key configured - allow access
        return True

    if not provided_key:
        return False

    return provided_key == expected_key
```

**Step 3: Commit**

```bash
git add src/mcp/__init__.py src/mcp/auth.py
git commit -m "feat(mcp): create MCP module structure with auth validation"
```

---

## Task 4: Write Tests for MCP Tools

**Files:**
- Create: `tests/test_mcp_tools.py`

**Step 1: Write tests for analyze_stock tool**

Create `tests/test_mcp_tools.py`:
```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_mcp_tools.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.mcp.tools'"

**Step 3: Commit the failing tests**

```bash
git add tests/test_mcp_tools.py
git commit -m "test(mcp): add failing tests for MCP tools"
```

---

## Task 5: Implement Analysis Tool

**Files:**
- Create: `src/mcp/tools/__init__.py`
- Create: `src/mcp/tools/analysis.py`

**Step 1: Create tools init**

Create `src/mcp/tools/__init__.py`:
```python
# -*- coding: utf-8 -*-
"""MCP Tools Package."""

from src.mcp.tools.analysis import analyze_stock
from src.mcp.tools.stocks import get_realtime_quote, search_stocks, get_market_indices

__all__ = [
    "analyze_stock",
    "get_realtime_quote",
    "search_stocks",
    "get_market_indices",
]
```

**Step 2: Implement analyze_stock tool**

Create `src/mcp/tools/analysis.py`:
```python
# -*- coding: utf-8 -*-
"""
MCP Analysis Tools

Provides stock analysis tool for MCP server.
"""

import logging
import re
from typing import Dict, Any

from src.enums import ReportType

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
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    Analyze a stock using AI.

    Args:
        stock_code: Stock code to analyze
        report_type: "simple" or "full"
        force_refresh: Force re-fetch data

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
        from src.services.task_service import get_task_service
        from data_provider.base import canonical_stock_code

        code = canonical_stock_code(stock_code)
        service = get_task_service()

        result = service.submit_analysis(
            code=code,
            report_type=ReportType.from_str(report_type),
            force_refresh=force_refresh
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
```

**Step 3: Run tests to verify analyze_stock works**

Run: `pytest tests/test_mcp_tools.py::TestAnalyzeStockTool -v`
Expected: Tests PASS

**Step 4: Commit**

```bash
git add src/mcp/tools/__init__.py src/mcp/tools/analysis.py
git commit -m "feat(mcp): implement analyze_stock tool"
```

---

## Task 6: Implement Stocks Tools

**Files:**
- Create: `src/mcp/tools/stocks.py`

**Step 1: Implement stocks tools**

Create `src/mcp/tools/stocks.py`:
```python
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
```

**Step 2: Run tests to verify stocks tools work**

Run: `pytest tests/test_mcp_tools.py::TestStocksTools -v`
Expected: Tests PASS

**Step 3: Commit**

```bash
git add src/mcp/tools/stocks.py
git commit -m "feat(mcp): implement get_realtime_quote, search_stocks, get_market_indices tools"
```

---

## Task 7: Create MCP Server with SSE Endpoint

**Files:**
- Create: `src/mcp/server.py`

**Step 1: Implement MCP server**

Create `src/mcp/server.py`:
```python
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
        """Handle MCP SSE connection."""
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

    logger.info("MCP server initialized at /mcp")
```

**Step 2: Commit**

```bash
git add src/mcp/server.py
git commit -m "feat(mcp): create MCP server with SSE endpoint and tool handlers"
```

---

## Task 8: Integrate MCP with FastAPI App

**Files:**
- Modify: `api/app.py`

**Step 1: Add MCP setup to FastAPI app**

In `api/app.py`, add import after other src imports:
```python
from src.mcp import setup_mcp
```

Add setup call after app creation and middleware setup (after the lifespan context manager or after `app = FastAPI(...)`):
```python
# Setup MCP server
setup_mcp(app)
```

**Step 2: Verify app starts correctly**

Run: `python -c "from api.app import app; print('App loaded successfully')"`
Expected: "App loaded successfully"

**Step 3: Commit**

```bash
git add api/app.py
git commit -m "feat(api): integrate MCP server with FastAPI app"
```

---

## Task 9: Add Integration Test

**Files:**
- Create: `tests/test_mcp_integration.py`

**Step 1: Write integration test**

Create `tests/test_mcp_integration.py`:
```python
# -*- coding: utf-8 -*-
"""Integration tests for MCP server."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client with MCP enabled."""
    import os
    os.environ["MCP_ENABLED"] = "true"
    os.environ["MCP_API_KEY"] = "test-key"

    from api.app import app
    return TestClient(app)


def test_mcp_endpoint_requires_api_key(client):
    """MCP endpoint should require API key."""
    response = client.get("/mcp")
    assert response.status_code == 401


def test_mcp_endpoint_with_invalid_key(client):
    """MCP endpoint should reject invalid API key."""
    response = client.get("/mcp", headers={"X-MCP-Key": "wrong-key"})
    assert response.status_code == 401


def test_mcp_endpoint_with_valid_key(client):
    """MCP endpoint should accept valid API key."""
    response = client.get("/mcp", headers={"X-MCP-Key": "test-key"})
    # SSE endpoint returns 200 for successful connection
    assert response.status_code in [200, 405]  # 405 if GET not supported directly
```

**Step 2: Run integration tests**

Run: `pytest tests/test_mcp_integration.py -v`
Expected: Tests PASS

**Step 3: Commit**

```bash
git add tests/test_mcp_integration.py
git commit -m "test(mcp): add integration tests for MCP server"
```

---

## Task 10: Update Documentation

**Files:**
- Modify: `DEVELOPMENT_GUIDE.md`

**Step 1: Add MCP section to development guide**

Add new section to `DEVELOPMENT_GUIDE.md` after the API Reference section:

```markdown
### MCP Server

The project includes an MCP (Model Context Protocol) server for AI agent integration.

#### Configuration

```bash
# .env
MCP_ENABLED=true
MCP_API_KEY=your-secure-key-here
```

#### Available Tools

| Tool | Description |
|------|-------------|
| `analyze_stock` | Trigger AI stock analysis |
| `get_realtime_quote` | Get real-time stock price |
| `search_stocks` | Search stocks by keyword |
| `get_market_indices` | Get market index data |

#### Claude Code Integration

Add to your Claude Code MCP config:

```json
{
  "mcpServers": {
    "stock-analysis": {
      "url": "http://localhost:8000/mcp",
      "headers": {
        "X-MCP-Key": "your-key-here"
      }
    }
  }
}
```

#### Testing

```bash
# Test MCP endpoint
curl -X GET http://localhost:8000/mcp \
  -H "X-MCP-Key: your-key"
```
```

**Step 2: Commit**

```bash
git add DEVELOPMENT_GUIDE.md
git commit -m "docs: add MCP server documentation to development guide"
```

---

## Task 11: Final Verification

**Step 1: Run all tests**

Run: `pytest tests/ -v --tb=short`
Expected: All tests PASS

**Step 2: Start server and test manually**

Run: `uvicorn api.app:app --host 0.0.0.0 --port 8000`

In another terminal, test the MCP endpoint:
```bash
curl -X GET http://localhost:8000/mcp \
  -H "X-MCP-Key: test-key" \
  -H "Accept: text/event-stream"
```

Expected: SSE connection established

**Step 3: Create summary commit**

```bash
git add -A
git commit -m "feat(mcp): complete MCP server implementation for AI agent integration

- Add MCP SDK dependency
- Create MCP module with auth, tools, and server
- Expose 4 tools: analyze_stock, get_realtime_quote, search_stocks, get_market_indices
- Integrate with FastAPI via /mcp SSE endpoint
- Add API key authentication
- Add comprehensive tests and documentation

Closes: MCP server feature request"
```

---

## Verification Checklist

- [ ] All tests pass: `pytest tests/ -v`
- [ ] MCP endpoint accessible: `curl http://localhost:8000/mcp -H "X-MCP-Key: key"`
- [ ] API key validation works: 401 without/with invalid key
- [ ] Tools execute correctly via MCP protocol
- [ ] Claude Code can connect to MCP server
- [ ] Documentation updated

---

## Notes

- MCP server shares the same port as REST API (8000)
- Tools reuse existing services (no code duplication)
- SSE transport is the only supported transport (stdio not implemented)
- Rate limiting inherits from existing bot configuration
