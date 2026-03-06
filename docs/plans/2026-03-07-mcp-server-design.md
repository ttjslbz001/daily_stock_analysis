# MCP Server Design Document

> Enable AI agents (Claude Code, OpenAI-compatible clients) to interact with Daily Stock Analysis API via Model Context Protocol (MCP).

## Overview

### Problem
Users want to use AI agents like Claude Code to interact with the stock analysis system programmatically, but currently only REST API and web UI are available.

### Solution
Build an MCP server as a FastAPI extension that exposes core analysis and stock data tools via HTTP/SSE transport.

### Goals
- Allow Claude Code CLI to analyze stocks, get quotes, search stocks
- Support OpenAI-compatible clients
- Single-server deployment (no separate process)
- Simple API key authentication

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI App (port 8000)                       │
├─────────────────────────────────────────────────────────────────┤
│  Existing REST API              │  NEW: MCP Server               │
│  ─────────────────              │  ───────────────               │
│  /api/v1/analysis/*             │  /mcp (SSE endpoint)           │
│  /api/v1/stocks/*               │                                │
│  /api/v1/history/*              │  Tools exposed:                │
│  /api/v1/agent/*                │  • analyze_stock               │
│  /api/v1/backtest/*             │  • get_realtime_quote          │
│  /api/v1/system/*               │  • search_stocks               │
│  /api/v1/auth/*                 │  • get_market_indices          │
├─────────────────────────────────┴────────────────────────────────┤
│  Shared: Services, Config, Storage, DataFetcher                  │
└─────────────────────────────────────────────────────────────────┘
```

## MCP Tools

### 1. analyze_stock

Trigger AI-powered stock analysis.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| stock_code | string | Yes | Stock code (e.g., "600519", "AAPL") |
| report_type | string | No | "simple" (default) or "full" |
| force_refresh | boolean | No | Force re-fetch data (default: false) |

**Returns:** Analysis result with sentiment score, trend prediction, operation advice.

### 2. get_realtime_quote

Get real-time stock price and metrics.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| stock_code | string | Yes | Stock code |

**Returns:** Price, change %, volume ratio, turnover rate, PE/PB, market cap.

### 3. search_stocks

Search stocks by keyword or code.

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| keyword | string | Yes | Search keyword |
| limit | integer | No | Max results (default: 10) |

**Returns:** List of matching stocks with code, name, market.

### 4. get_market_indices

Get current market index data.

**Parameters:** None

**Returns:** 上证指数, 深证成指, 创业板指, 纳斯达克, 道琼斯, etc.

## Authentication

- **Environment Variable:** `MCP_API_KEY`
- **Header:** `X-MCP-Key: <your-key>`
- **Response:** 401 Unauthorized if missing or invalid

```bash
# .env configuration
MCP_ENABLED=true
MCP_API_KEY=your-secure-key-here
```

## Data Flow

```
Claude Code / OpenAI Client
        │
        │  POST /mcp (SSE)
        │  Headers: X-MCP-Key: <api_key>
        ▼
┌───────────────────────┐
│   MCP SSE Endpoint    │
│   /mcp                │
├───────────────────────┤
│ 1. Validate API key   │
│ 2. Parse MCP request  │
│ 3. Route to tool      │
│ 4. Execute tool       │
│ 5. Return MCP response│
└───────────────────────┘
        │
        ▼
┌───────────────────────┐
│   Tool Implementation │
├───────────────────────┤
│ analyze_stock:        │
│   → AnalysisService   │
│ get_realtime_quote:   │
│   → DataFetcherManager│
│ search_stocks:        │
│   → DataFetcherManager│
│ get_market_indices:   │
│   → DataFetcherManager│
└───────────────────────┘
```

## File Structure

```
src/mcp/
├── __init__.py           # Module init, exports
├── server.py             # FastMCP server setup, SSE endpoint
├── auth.py               # API key validation middleware
└── tools/
    ├── __init__.py       # Tool registry
    ├── analysis.py       # analyze_stock tool implementation
    └── stocks.py         # get_quote, search, indices tools
```

**Modifications to existing files:**
- `api/app.py` - Add `setup_mcp(app)` call
- `requirements.txt` - Add `mcp>=1.0.0`
- `src/config.py` - Add `mcp_enabled`, `mcp_api_key` fields

## Error Handling

| Scenario | HTTP Status | MCP Error Code | Message |
|----------|-------------|----------------|---------|
| Invalid API key | 401 | Unauthorized | "Invalid MCP API key" |
| Missing API key | 401 | Unauthorized | "MCP API key required" |
| Invalid stock code | 200 | InvalidParams | "Invalid stock code format" |
| Stock not found | 200 | InternalError | "Stock {code} not found" |
| Analysis failed | 200 | InternalError | "Analysis failed: {reason}" |

## Testing

### Unit Tests
```bash
pytest tests/test_mcp_tools.py
```

### Integration Test (curl)
```bash
curl -X POST http://localhost:8000/mcp \
  -H "X-MCP-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "get_realtime_quote", "arguments": {"stock_code": "600519"}}, "id": 1}'
```

### Claude Code Integration Test
Add to Claude Code MCP config:
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

## Dependencies

```txt
mcp>=1.0.0              # Official MCP Python SDK
```

## Configuration

```bash
# .env
MCP_ENABLED=true                    # Enable/disable MCP server
MCP_API_KEY=                        # API key for authentication
```

## Security Considerations

1. **API Key:** Use a strong, random key (32+ characters)
2. **HTTPS:** Recommended for production (behind reverse proxy)
3. **Rate Limiting:** Inherits existing bot rate limits
4. **Scope:** Only exposes read-only + analysis operations (no config modification)

## Future Enhancements (Out of Scope)

- WebSocket transport support
- More granular tool permissions
- Tool result caching
- Streaming analysis results
