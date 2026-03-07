# MCP Server Integration

> Enable AI agents (Claude Code, OpenAI-compatible clients) to interact with Daily Stock Analysis API via Model Context Protocol (MCP).

## Overview

The MCP (Model Context Protocol) server allows AI agents to programmatically access stock analysis capabilities through a standardized protocol. This enables:

- **Claude Code CLI** integration for stock analysis directly in your terminal
- **OpenAI-compatible clients** to use stock analysis tools
- **Single-server deployment** - runs alongside the existing FastAPI application

## Quick Start

### 1. Enable MCP Server

Add to your `.env` file:

```bash
# === MCP Server Configuration ===
MCP_ENABLED=true
MCP_API_KEY=your-secure-api-key-here
```

> **Important:** Use a strong, random key (32+ characters) in production.

### 2. Start the Server

```bash
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000
```

### 3. Configure Claude Code

Add to your Claude Code MCP configuration (`~/.claude/mcp_config.json`):

```json
{
  "mcpServers": {
    "stock-analysis": {
      "url": "http://localhost:8000/mcp",
      "headers": {
        "X-MCP-Key": "your-secure-api-key-here"
      }
    }
  }
}
```

### 4. Use in Claude Code

```
> What's the current price of 茅台 (600519)?
> Analyze stock 600519 and give me a recommendation
> Search for stocks containing "新能源"
> What are today's market indices?
```

## Available Tools

### 1. analyze_stock

Trigger AI-powered stock analysis.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| stock_code | string | Yes | Stock code (e.g., "600519", "AAPL", "HK00700") |
| report_type | string | No | "simple" (default) or "full" |

**Example:**
```json
{
  "name": "analyze_stock",
  "arguments": {
    "stock_code": "600519",
    "report_type": "simple"
  }
}
```

**Returns:**
```json
{
  "success": true,
  "task_id": "600519_20260307_213252_297905",
  "stock_code": "600519",
  "message": "Analysis submitted for 600519"
}
```

### 2. get_realtime_quote

Get real-time stock price and metrics.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| stock_code | string | Yes | Stock code |

**Example:**
```json
{
  "name": "get_realtime_quote",
  "arguments": {
    "stock_code": "600519"
  }
}
```

**Returns:**
```json
{
  "success": true,
  "code": "600519",
  "name": "贵州茅台",
  "price": 1402.0,
  "change_pct": 0.21,
  "volume": 2915400,
  "volume_ratio": 0.76,
  "turnover_rate": 0.23,
  "pe_ratio": 19.5,
  "pb_ratio": 7.73,
  "total_mv": 1755683000000
}
```

### 3. search_stocks

Search stocks by keyword or code.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| keyword | string | Yes | Search keyword |
| limit | integer | No | Max results (default: 10) |

**Example:**
```json
{
  "name": "search_stocks",
  "arguments": {
    "keyword": "茅台",
    "limit": 5
  }
}
```

**Returns:**
```json
[
  {"code": "600519", "name": "贵州茅台", "market": "SH"}
]
```

### 4. get_market_indices

Get current market index data.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| region | string | No | "cn" (default), "us", or "both" |

**Example:**
```json
{
  "name": "get_market_indices",
  "arguments": {
    "region": "cn"
  }
}
```

**Returns:**
```json
[
  {"code": "sh000001", "name": "上证指数", "price": 3372.55, "change_pct": 0.38},
  {"code": "sz399001", "name": "深证成指", "price": 10851.65, "change_pct": 0.59},
  {"code": "sz399006", "name": "创业板指", "price": 2241.82, "change_pct": 0.82}
]
```

## Authentication

All MCP requests require API key authentication via the `X-MCP-Key` header.

```bash
# Example curl request
curl -X GET "http://localhost:8000/mcp" \
  -H "X-MCP-Key: your-api-key"
```

**Error Responses:**
- `401 Unauthorized` - Missing or invalid API key

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI App (port 8000)                       │
├─────────────────────────────────────────────────────────────────┤
│  Existing REST API              │  MCP Server                    │
│  ─────────────────              │  ───────────────               │
│  /api/v1/analysis/*             │  /mcp (SSE endpoint)           │
│  /api/v1/stocks/*               │                                │
│  /api/v1/history/*              │  Tools exposed:                │
│  /api/v1/agent/*                │  - analyze_stock               │
│  /api/v1/backtest/*             │  - get_realtime_quote          │
│  /api/v1/system/*               │  - search_stocks               │
│  /api/v1/auth/*                 │  - get_market_indices          │
├─────────────────────────────────┴────────────────────────────────┤
│  Shared: Services, Config, Storage, DataFetcher                  │
└─────────────────────────────────────────────────────────────────┘
```

## Testing

### Using MCP Client (Python)

```python
import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

async def test_mcp():
    url = "http://localhost:8000/mcp"
    headers = {"X-MCP-Key": "your-api-key"}

    async with sse_client(url, headers=headers) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {[t.name for t in tools.tools]}")

            # Get real-time quote
            result = await session.call_tool("get_realtime_quote", {
                "stock_code": "600519"
            })
            print(result.content[0].text)

asyncio.run(test_mcp())
```

### Using curl (SSE endpoint)

```bash
# SSE connection test
curl -N -H "X-MCP-Key: your-api-key" \
  "http://localhost:8000/mcp"
```

## Security Considerations

1. **API Key:** Use a strong, random key (32+ characters) in production
2. **HTTPS:** Recommended for production (deploy behind reverse proxy with TLS)
3. **Rate Limiting:** Inherits existing bot rate limits
4. **Scope:** Only exposes read-only + analysis operations (no config modification)

## Configuration Reference

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `MCP_ENABLED` | `false` | Enable/disable MCP server |
| `MCP_API_KEY` | - | API key for authentication (required when enabled) |

## File Structure

```
src/mcp/
├── __init__.py           # Module init, exports setup_mcp
├── server.py             # FastMCP server setup, SSE endpoint
├── auth.py               # API key validation
└── tools/
    ├── __init__.py       # Tool registry
    ├── analysis.py       # analyze_stock tool
    └── stocks.py         # get_quote, search, indices tools
```

## Troubleshooting

### MCP endpoint returns 404

Ensure `MCP_ENABLED=true` is set in your `.env` file and the server was restarted.

### Authentication fails with valid key

Check that the `X-MCP-Key` header is being sent correctly. The key is case-sensitive.

### Tool execution fails

Check server logs for detailed error messages:
```bash
tail -f logs/app.log
```

## Future Enhancements

- WebSocket transport support
- More granular tool permissions
- Tool result caching
- Streaming analysis results
