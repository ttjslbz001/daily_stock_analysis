# Tushare Data Provider Technical Documentation

> This document details the architecture, API integration, data processing pipeline, and configuration of the Tushare data provider.

## 📑 Table of Contents

- [Overview](#overview)
- [Architecture Design](#architecture-design)
- [API Capabilities](#api-capabilities)
- [Data Processing Pipeline](#data-processing-pipeline)
- [Rate Limiting & Retry](#rate-limiting--retry)
- [Priority System](#priority-system)
- [Real-time Quote System](#real-time-quote-system)
- [Caching Mechanism](#caching-mechanism)
- [Configuration](#configuration)
- [Error Handling](#error-handling)
- [Database Storage](#database-storage)
- [Best Practices](#best-practices)

---

## Overview

### What is Tushare

[Tushare](https://tushare.pro) is an open financial data interface providing historical and real-time data for stocks, funds, futures, and foreign exchange. This system integrates Tushare Pro API through the `TushareFetcher` class as one of the optional data sources in the multi-source strategy.

### Features

| Feature | Description |
|---------|-------------|
| **Data Quality** | High-quality, standardized financial data |
| **API Stability** | Officially maintained, stable and reliable |
| **Coverage** | A-shares, ETFs, indices, funds, etc. |
| **Authentication** | Requires Token (free tier available) |
| **Quota Limits** | Free tier: 80 requests/min, 500 requests/day |

### Position in System

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Source Priority Order               │
├─────────────────────────────────────────────────────────────┤
│  Priority -1: TushareFetcher  ◄── Highest when Token set   │
│  Priority  0: EfinanceFetcher                              │
│  Priority  1: AkshareFetcher                               │
│  Priority  2: PytdxFetcher / TushareFetcher (no Token)     │
│  Priority  3: BaostockFetcher                              │
│  Priority  4: YfinanceFetcher  ◄── US stocks only          │
└─────────────────────────────────────────────────────────────┘
```

---

## Architecture Design

### Class Structure

```
BaseFetcher (Abstract Base Class)
    │
    ├── name: str              # Data source name
    ├── priority: int          # Priority level
    │
    ├── get_daily_data()       # Get daily data (unified entry)
    ├── _fetch_raw_data()      # Fetch raw data [abstract]
    ├── _normalize_data()      # Normalize data [abstract]
    ├── _clean_data()          # Data cleaning
    ├── _calculate_indicators() # Calculate technical indicators
    │
    └── get_realtime_quote()   # Get real-time quote
    └── get_stock_name()       # Get stock name
    └── get_stock_list()       # Get stock list
    └── get_main_indices()     # Get major indices
    └── get_market_stats()     # Get market statistics

        ▲
        │ Inherits
        │
TushareFetcher
    │
    ├── _api: object           # Tushare API instance
    ├── _call_count: int       # Current minute call count
    ├── _minute_start: float   # Count period start time
    ├── _stock_name_cache: dict # Stock name cache
    │
    ├── _init_api()            # Initialize API
    ├── _patch_api_endpoint()  # Patch API endpoint
    ├── _determine_priority()  # Dynamic priority
    ├── _check_rate_limit()    # Rate limit check
    ├── _convert_stock_code()  # Code format conversion
    └── ...                    # Other method implementations
```

### File Location

```
data_provider/
├── __init__.py
├── base.py                    # Base class and manager
├── tushare_fetcher.py         # Tushare implementation ←── Core of this doc
├── realtime_types.py          # Real-time quote type definitions
└── ...                        # Other data sources
```

---

## API Capabilities

### Supported Tushare Interfaces

| Interface | Method | Purpose | Return Fields |
|-----------|--------|---------|---------------|
| `daily()` | Daily data | A-share historical quotes | ts_code, trade_date, open, high, low, close, pre_close, change, pct_chg, vol, amount |
| `fund_daily()` | Fund daily | ETF historical quotes | Same as daily |
| `stock_basic()` | Stock basics | Stock basic info | ts_code, name, industry, area, market |
| `fund_basic()` | Fund basics | ETF basic info | ts_code, name |
| `quotation()` | Pro realtime | Real-time quotes (2000+ points) | price, pct_chg, vol, amount, pe, pb, total_mv, turnover_ratio |
| `get_realtime_quotes()` | Legacy realtime | Real-time quotes (free) | price, pre_close, volume, amount, name |
| `index_daily()` | Index daily | Major indices history | close, pre_close, change, pct_chg, open, high, low, vol, amount |
| `trade_cal()` | Trade calendar | Trading day query | cal_date, is_open |

### Supported Stock Types

#### A-Share Stocks

| Market Type | Code Prefix | Tushare Format | Example |
|-------------|-------------|----------------|---------|
| Shanghai Main | 600xxx, 601xxx, 603xxx | XXXXXX.SH | 600519.SH |
| STAR Market | 688xxx | XXXXXX.SH | 688981.SH |
| Shenzhen Main | 000xxx | XXXXXX.SZ | 000001.SZ |
| SME Board | 002xxx | XXXXXX.SZ | 002594.SZ |
| ChiNext | 300xxx | XXXXXX.SZ | 300750.SZ |

#### ETF Funds

| Market | Code Prefix | Tushare Format | Example |
|--------|-------------|----------------|---------|
| Shanghai ETF | 51xxxx, 52xxxx, 56xxxx, 58xxxx | XXXXXX.SH | 510050.SH |
| Shenzhen ETF | 15xxxx, 16xxxx, 18xxxx | XXXXXX.SZ | 159919.SZ |

#### Major Indices

| Index Name | Tushare Code |
|------------|--------------|
| Shanghai Composite | 000001.SH |
| Shenzhen Component | 399001.SZ |
| ChiNext Index | 399006.SZ |
| STAR 50 | 000688.SH |
| SSE 50 | 000016.SH |
| CSI 300 | 000300.SH |

#### Unsupported Types

- **US Stocks**: e.g., AAPL, TSLA (use YfinanceFetcher)
- **HK Stocks**: Not currently supported (use AkshareFetcher)

### Code Format Conversion Logic

```python
# Location: tushare_fetcher.py:252-289

def _convert_stock_code(self, stock_code: str) -> str:
    """
    Input format conversion rules:

    '600519'     → '600519.SH'  # Shanghai stocks
    '000001'     → '000001.SZ'  # Shenzhen stocks
    '510050'     → '510050.SH'  # Shanghai ETF
    '159919'     → '159919.SZ'  # Shenzhen ETF
    '600519.SH'  → '600519.SH'  # Already has suffix, return as-is
    """
    code = stock_code.strip()

    # Already has suffix
    if '.' in code:
        return code.upper()

    # ETF detection
    if code.startswith(('51', '52', '56', '58')) and len(code) == 6:
        return f"{code}.SH"  # Shanghai ETF
    if code.startswith(('15', '16', '18')) and len(code) == 6:
        return f"{code}.SZ"  # Shenzhen ETF

    # Regular stocks
    if code.startswith(('600', '601', '603', '688')):
        return f"{code}.SH"  # Shanghai
    elif code.startswith(('000', '002', '300')):
        return f"{code}.SZ"  # Shenzhen
    else:
        return f"{code}.SZ"  # Default to Shenzhen
```

---

## Data Processing Pipeline

### Complete Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       Tushare Data Processing Pipeline                  │
└─────────────────────────────────────────────────────────────────────────┘

    User Request
        │
        ▼
┌───────────────────┐
│  get_daily_data() │  ─── Unified Entry (BaseFetcher)
│   (BaseFetcher)   │
└─────────┬─────────┘
          │
          ▼
┌───────────────────────────────────────────────────────────────────────┐
│ Step 1: Rate Limit Check                                              │
│         _check_rate_limit()                                           │
│                                                                       │
│   • Check call count in current minute                                │
│   • Sleep until next minute if count >= 80                            │
│   • Increment call counter                                            │
└───────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────────────────────────────────────────────────┐
│ Step 2: Stock Code Conversion                                         │
│         _convert_stock_code()                                         │
│                                                                       │
│   600519 → 600519.SH                                                  │
│   159919 → 159919.SZ                                                  │
└───────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────────────────────────────────────────────────┐
│ Step 3: Call Tushare API                                              │
│         _fetch_raw_data()                                             │
│                                                                       │
│   • ETF: api.fund_daily(ts_code, start_date, end_date)               │
│   • Stock: api.daily(ts_code, start_date, end_date)                  │
│   • Auto retry 3 times (exponential backoff)                          │
└───────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────────────────────────────────────────────────┐
│ Step 4: Data Normalization                                            │
│         _normalize_data()                                             │
│                                                                       │
│   Column Mapping:                                                     │
│     trade_date → date                                                 │
│     vol → volume                                                      │
│                                                                       │
│   Unit Conversion:                                                    │
│     volume: lots → shares (×100)                                      │
│     amount: 1000 RMB → RMB (×1000)                                    │
│                                                                       │
│   Date Format:                                                        │
│     YYYYMMDD → YYYY-MM-DD                                             │
└───────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────────────────────────────────────────────────┐
│ Step 5: Data Cleaning                                                 │
│         _clean_data() (BaseFetcher)                                   │
│                                                                       │
│   • Convert date column to datetime type                              │
│   • Convert numeric column types                                      │
│   • Drop null rows                                                    │
│   • Sort by date ascending                                            │
└───────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────────────────────────────────────────────────┐
│ Step 6: Technical Indicator Calculation                               │
│         _calculate_indicators() (BaseFetcher)                         │
│                                                                       │
│   MA5  = close.rolling(5).mean()                                      │
│   MA10 = close.rolling(10).mean()                                     │
│   MA20 = close.rolling(20).mean()                                     │
│   Volume_Ratio = volume / avg_volume_5.shift(1)                       │
└───────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────────────────────────────────────────────────┐
│ Output: Standardized DataFrame                                        │
│                                                                       │
│   code | date | open | high | low | close | volume | amount | pct_chg│
│   ma5 | ma10 | ma20 | volume_ratio | data_source                    │
└───────────────────────────────────────────────────────────────────────┘
```

### Raw Data vs Standardized Data

```
Raw Tushare Data (daily API response):
┌───────────┬────────────┬──────┬──────┬───────┬───────┬────────┬─────────┬─────────┐
│ ts_code   │ trade_date │ open │ high │ low   │ close │ pre_cl │ pct_chg │ vol     │ amount  │
├───────────┼────────────┼──────┼──────┼───────┼───────┼────────┼─────────┼─────────┤
│ 600519.SH │ 20240315   │ 1750 │ 1780 │ 1745  │ 1775  │ 1730   │ 2.60    │ 25000   │ 450000  │
│           │            │      │      │       │       │        │         │ (lots)  │ (1000RMB)│
└───────────┴────────────┴──────┴──────┴───────┴───────┴────────┴─────────┴─────────┘
                                        │
                                        ▼ _normalize_data()

Standardized Data:
┌────────┬────────────┬──────┬──────┬───────┬───────┬──────────┬───────────┬─────────┐
│ code   │ date       │ open │ high │ low   │ close │ pct_chg  │ volume    │ amount   │
├────────┼────────────┼──────┼──────┼───────┼───────┼──────────┼───────────┼─────────┤
│ 600519 │ 2024-03-15 │ 1750 │ 1780 │ 1745  │ 1775  │ 2.60     │ 2500000   │ 450000000│
│        │            │      │      │       │       │          │ (shares)  │ (RMB)    │
└────────┴────────────┴──────┴──────┴───────┴───────┴──────────┴───────────┴─────────┘
```

---

## Rate Limiting & Retry

### Rate Limiting Mechanism

```python
# Location: tushare_fetcher.py:210-250

class TushareFetcher:
    def __init__(self, rate_limit_per_minute: int = 80):
        """
        Free tier quota:
        - Max 80 requests per minute
        - Max 500 requests per day
        """
        self.rate_limit_per_minute = rate_limit_per_minute
        self._call_count = 0           # Current minute call count
        self._minute_start = None      # Current count period start time

    def _check_rate_limit(self):
        """
        Flow Control State Machine:

        ┌─────────────┐    60s     ┌─────────────┐
        │   COUNTING  │ ─────────► │    RESET    │
        │  count < 80 │            │  count = 0  │
        └──────┬──────┘            └──────┬──────┘
               │                          ▲
               │ count >= 80              │
               ▼                          │
        ┌─────────────┐                   │
        │  SLEEPING   │ ──────────────────┘
        │ sleep(60-t) │
        └─────────────┘
        """
        current_time = time.time()

        # Reset counter every minute
        if self._minute_start is None:
            self._minute_start = current_time
            self._call_count = 0
        elif current_time - self._minute_start >= 60:
            self._minute_start = current_time
            self._call_count = 0

        # Sleep if limit exceeded
        if self._call_count >= self.rate_limit_per_minute:
            elapsed = current_time - self._minute_start
            sleep_time = max(0, 60 - elapsed) + 1  # +1s buffer
            logger.warning(f"Rate limit triggered, sleeping {sleep_time:.1f}s...")
            time.sleep(sleep_time)
            self._minute_start = time.time()
            self._call_count = 0

        self._call_count += 1
```

### Retry Mechanism

```python
# Location: tushare_fetcher.py:291-296

@retry(
    stop=stop_after_attempt(3),                          # Max 3 attempts
    wait=wait_exponential(multiplier=1, min=2, max=30), # Exponential backoff: 2s → 4s → 8s
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str):
    ...

# Retry Timeline:
# Attempt 1 ──► Fail ──► Wait 2s
# Attempt 2 ──► Fail ──► Wait 4s
# Attempt 3 ──► Fail ──► Raise DataFetchError
```

### API Endpoint Patch

Tushare SDK v1.4.x uses `api.waditu.com/dataapi` endpoint by default, which may return 503 errors. The system fixes this via Monkey Patch:

```python
# Location: tushare_fetcher.py:144-178

def _patch_api_endpoint(self, token: str):
    """
    Fix Tushare SDK endpoint issue

    Original SDK behavior:
      POST http://api.waditu.com/dataapi/{api_name}  ← May return 503

    Patched behavior:
      POST http://api.tushare.pro  ← Official stable endpoint
    """
    TUSHARE_API_URL = "http://api.tushare.pro"

    def patched_query(self_api, api_name, fields='', **kwargs):
        req_params = {
            'api_name': api_name,
            'token': token,
            'params': kwargs,
            'fields': fields,
        }
        res = requests.post(TUSHARE_API_URL, json=req_params, timeout=30)
        # ... handle response ...

    self._api.query = types.MethodType(patched_query, self._api)
```

---

## Priority System

### Dynamic Priority Assignment

```python
# Location: tushare_fetcher.py:180-199

def _determine_priority(self) -> int:
    """
    Priority Logic:

    ┌─────────────────────────────────────────────────────────┐
    │                    Token Status                         │
    ├─────────────────────────────────────────────────────────┤
    │                                                         │
    │   TUSHARE_TOKEN configured AND API initialized?        │
    │                      │                                  │
    │           ┌──────────┴──────────┐                      │
    │           ▼                     ▼                      │
    │         [YES]                  [NO]                    │
    │           │                     │                      │
    │           ▼                     ▼                      │
    │   Priority: -1           Priority: 2                   │
    │   (Highest)              (Default)                     │
    │                                                         │
    └─────────────────────────────────────────────────────────┘
    """
    config = get_config()

    if config.tushare_token and self._api is not None:
        logger.info("✅ TUSHARE_TOKEN configured, priority upgraded to -1 (highest)")
        return -1

    return 2
```

### Real-time Quote Priority Auto-injection

```python
# Location: src/config.py:943-970

@classmethod
def _resolve_realtime_source_priority(cls) -> str:
    """
    When TUSHARE_TOKEN is configured but REALTIME_SOURCE_PRIORITY is not
    explicitly set, automatically prepend 'tushare' to the priority list.
    """
    explicit = os.getenv('REALTIME_SOURCE_PRIORITY')
    if explicit:
        return explicit  # Respect user's explicit config

    if os.getenv('TUSHARE_TOKEN'):
        # Token configured, auto-inject tushare to first position
        return f'tushare,tencent,akshare_sina,efinance,akshare_em'

    return 'tencent,akshare_sina,efinance,akshare_em'  # Default
```

---

## Real-time Quote System

### Dual-Interface Strategy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       Real-time Quote Strategy                          │
└─────────────────────────────────────────────────────────────────────────┘

    get_realtime_quote(stock_code)
              │
              ▼
    ┌─────────────────────────────────────┐
    │ Step 1: Try Pro Interface           │
    │         api.quotation()             │
    │                                     │
    │   Requires: 2000+ Tushare points    │
    │   Returns: Full data (price, PE...) │
    └──────────────────┬──────────────────┘
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
          [Success]           [Fail]
             │                   │
             ▼                   ▼
          Return result  ┌─────────────────────────────────────┐
                         │ Step 2: Fallback to Legacy         │
                         │         ts.get_realtime_quotes()   │
                         │                                     │
                         │   Requires: Free available         │
                         │   Returns: Basic data (price, vol) │
                         └──────────────────┬──────────────────┘
                                            │
                                  ┌─────────┴─────────┐
                                  ▼                   ▼
                               [Success]           [Fail]
                                  │                   │
                                  ▼                   ▼
                               Return result      Return None
```

### Interface Comparison

| Feature | Pro Interface (`quotation`) | Legacy Interface (`get_realtime_quotes`) |
|---------|----------------------------|------------------------------------------|
| **Points Required** | 2000+ | Free |
| **Latest Price** | ✅ | ✅ |
| **Change %** | ✅ | ✅ |
| **Volume/Amount** | ✅ | ✅ |
| **Volume Ratio** | ✅ | ❌ |
| **Turnover Rate** | ✅ | ❌ |
| **PE/PB** | ✅ | ❌ |
| **Market Cap** | ✅ | ❌ |
| **Stability** | High | Lower |

### Unified Data Structure

```python
# Location: data_provider/realtime_types.py:106-176

@dataclass
class UnifiedRealtimeQuote:
    """Unified real-time quote data structure"""

    # Identity
    code: str                                    # Stock code
    name: str = ""                               # Stock name
    source: RealtimeSource = RealtimeSource.TUSHARE

    # Core Price (Pro + Legacy)
    price: Optional[float] = None               # Latest price
    change_pct: Optional[float] = None          # Change %
    change_amount: Optional[float] = None       # Change amount

    # Volume Indicators
    volume: Optional[int] = None                # Volume (lots)
    amount: Optional[float] = None              # Amount (RMB)
    volume_ratio: Optional[float] = None        # Volume ratio (Pro)
    turnover_rate: Optional[float] = None       # Turnover rate (Pro)

    # Price Range
    open_price: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    pre_close: Optional[float] = None

    # Valuation Indicators (Pro)
    pe_ratio: Optional[float] = None            # P/E ratio
    pb_ratio: Optional[float] = None            # P/B ratio
    total_mv: Optional[float] = None            # Total market cap
```

---

## Caching Mechanism

### Stock Name Cache

```python
# Location: tushare_fetcher.py:404-456

class TushareFetcher:
    def get_stock_name(self, stock_code: str) -> Optional[str]:
        """
        In-memory cache strategy:

        ┌─────────────────────────────────────────────────────────┐
        │                                                         │
        │   1. Check _stock_name_cache (in-memory dict)          │
        │              │                                          │
        │      ┌───────┴───────┐                                 │
        │      ▼               ▼                                 │
        │   [Hit]           [Miss]                               │
        │      │               │                                 │
        │      ▼               ▼                                 │
        │   Return         Call API                             │
        │   cached value   stock_basic()                        │
        │                  or fund_basic()                      │
        │                       │                               │
        │                       ▼                               │
        │                   Cache result                        │
        │                   Return name                         │
        │                                                         │
        └─────────────────────────────────────────────────────────┘
        """
        # Check cache
        if hasattr(self, '_stock_name_cache') and stock_code in self._stock_name_cache:
            return self._stock_name_cache[stock_code]

        # Initialize cache
        if not hasattr(self, '_stock_name_cache'):
            self._stock_name_cache = {}

        # Call API
        ts_code = self._convert_stock_code(stock_code)
        if _is_etf_code(stock_code):
            df = self._api.fund_basic(ts_code=ts_code, fields='ts_code,name')
        else:
            df = self._api.stock_basic(ts_code=ts_code, fields='ts_code,name')

        # Cache and return
        if df is not None and not df.empty:
            name = df.iloc[0]['name']
            self._stock_name_cache[stock_code] = name
            return name

        return None
```

### Global Cache Configuration

```python
# Location: src/config.py

realtime_cache_ttl: int = 600  # Real-time quote cache: 10 minutes
```

---

## Configuration

### Environment Variables

```bash
# .env file configuration

# Tushare API Token (required)
TUSHARE_TOKEN=your_token_here

# Rate limit (optional, default: 80)
TUSHARE_RATE_LIMIT_PER_MINUTE=80

# Priority override (optional)
TUSHARE_PRIORITY=-1

# Real-time quote source priority (optional)
# When TUSHARE_TOKEN is configured, system auto-injects tushare
REALTIME_SOURCE_PRIORITY=tushare,tencent,akshare_sina,efinance
```

### Getting Tushare Token

1. Visit [Tushare Pro](https://tushare.pro)
2. Register and login
3. Go to "User Center" → "API Token"
4. Copy Token to `.env` file

### Config Class Integration

```python
# Location: src/config.py

@dataclass
class Config:
    # Tushare Token
    tushare_token: Optional[str] = None  # Read from TUSHARE_TOKEN env var

    # Rate Limit
    tushare_rate_limit_per_minute: int = 80  # Free tier quota

    # Real-time priority
    realtime_source_priority: str = "tencent,akshare_sina,efinance,akshare_em"
    # When TUSHARE_TOKEN is configured, becomes:
    # "tushare,tencent,akshare_sina,efinance,akshare_em"
```

---

## Error Handling

### Exception Hierarchy

```python
# Location: data_provider/base.py:96-108

class DataFetchError(Exception):
    """Base exception for data fetching"""
    pass

class RateLimitError(DataFetchError):
    """API rate limit exceeded"""
    pass

class DataSourceUnavailableError(DataFetchError):
    """Data source unavailable"""
    pass
```

### Error Detection Logic

```python
# Location: tushare_fetcher.py:351-359

def _fetch_raw_data(self, ...):
    try:
        # ... API call ...
    except Exception as e:
        error_msg = str(e).lower()

        # Detect quota exceeded
        if any(keyword in error_msg for keyword in ['quota', '配额', 'limit', '权限']):
            logger.warning(f"Tushare quota may be exceeded: {e}")
            raise RateLimitError(f"Tushare quota exceeded: {e}") from e

        raise DataFetchError(f"Tushare fetch failed: {e}") from e
```

### Failover

When Tushare fails, the system automatically switches to the next data source:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       Failover Flow                                     │
└─────────────────────────────────────────────────────────────────────────┘

[TushareFetcher] Try to fetch data
        │
        ▼
    ┌───────┐
    │Success│
    └───┬───┘
        │
   ┌────┴────┐
   ▼         ▼
 [Yes]      [No]
   │         │
   ▼         ▼
 Return    Log error
 result    │
           ▼
    Switch to next data source
    (EfinanceFetcher)
           │
           ▼
        ┌───────┐
        │Success│
        └───┬───┘
           ...
           │
           ▼
    All sources failed
           │
           ▼
    Raise DataFetchError
```

---

## Database Storage

### Table Structure

```sql
-- Stock daily data table
CREATE TABLE stock_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(10) NOT NULL,           -- Stock code
    date DATE NOT NULL,                  -- Trading date
    open FLOAT,                          -- Open price
    high FLOAT,                          -- High price
    low FLOAT,                           -- Low price
    close FLOAT,                         -- Close price
    volume FLOAT,                        -- Volume (shares)
    amount FLOAT,                        -- Amount (RMB)
    pct_chg FLOAT,                       -- Change %
    ma5 FLOAT,                           -- 5-day MA
    ma10 FLOAT,                          -- 10-day MA
    ma20 FLOAT,                          -- 20-day MA
    volume_ratio FLOAT,                  -- Volume ratio
    data_source VARCHAR(50),             -- Data source
    created_at DATETIME,                 -- Created time
    updated_at DATETIME,                 -- Updated time
    CONSTRAINT uix_code_date UNIQUE (code, date)
);

CREATE INDEX ix_code_date ON stock_daily(code, date);
CREATE INDEX ix_stock_daily_code ON stock_daily(code);
CREATE INDEX ix_stock_daily_date ON stock_daily(date);
```

### ORM Model

```python
# Location: src/storage.py:62-131

class StockDaily(Base):
    """Stock daily data model"""
    __tablename__ = 'stock_daily'

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    # OHLC data
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)

    # Trading data
    volume = Column(Float)    # Volume (shares)
    amount = Column(Float)    # Amount (RMB)
    pct_chg = Column(Float)   # Change %

    # Technical indicators
    ma5 = Column(Float)
    ma10 = Column(Float)
    ma20 = Column(Float)
    volume_ratio = Column(Float)

    # Data source
    data_source = Column(String(50))

    # Timestamps
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        UniqueConstraint('code', 'date', name='uix_code_date'),
        Index('ix_code_date', 'code', 'date'),
    )
```

---

## Best Practices

### 1. Token Configuration

```bash
# Recommended: Configure Tushare Token for production
TUSHARE_TOKEN=your_token_here

# Reasons:
# - Upgrades priority to highest (-1)
# - Higher quality financial data
# - Access to more API interfaces
```

### 2. Rate Limit Management

```python
# For batch fetching, control concurrency

# Not recommended: Large concurrent requests
for code in stock_codes:
    fetcher.get_daily_data(code)  # May trigger rate limit

# Recommended: Batch fetching with delays
import time
for i, code in enumerate(stock_codes):
    fetcher.get_daily_data(code)
    if i % 70 == 0:  # Pause every 70 requests
        time.sleep(60)
```

### 3. Error Handling

```python
from data_provider.base import DataFetchError, RateLimitError

try:
    df, source = manager.get_daily_data('600519')
except RateLimitError:
    logger.warning("Tushare quota exhausted, using other sources")
    # System will auto-switch to next data source
except DataFetchError as e:
    logger.error(f"All data sources failed: {e}")
```

### 4. Cache Utilization

```python
# Leverage stock name cache
fetcher = TushareFetcher()

# First call requests API
name1 = fetcher.get_stock_name('600519')  # API call

# Subsequent calls use cache
name2 = fetcher.get_stock_name('600519')  # Cache hit
```

### 5. Real-time Quote Priority

```bash
# Recommended: For Tushare users
REALTIME_SOURCE_PRIORITY=tushare,tencent,akshare_sina

# Reasons:
# - tushare: Most complete data (requires points)
# - tencent: Stable, has volume ratio/turnover rate
# - akshare_sina: Basic quotes stable
```

---

## References

- [Tushare Pro Official Documentation](https://tushare.pro/document/2)
- [Tushare Points Rules](https://tushare.pro/document/1)
- [Project README](../README.md)
- [Full Configuration Guide](./full-guide_EN.md)
