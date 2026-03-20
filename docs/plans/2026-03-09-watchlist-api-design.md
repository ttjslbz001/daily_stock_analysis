# Stock Watchlist API Design

**Date:** 2026-03-09
**Status:** Approved

## Overview

Add a standalone stock watchlist API that allows users to manage a global list of stocks (independent of groups).

## Requirements

- Standalone watchlist (not tied to groups)
- Global watchlist (shared for all users)
- Operations:
  - Add single stock
  - Remove single stock
  - List all stocks with real-time quotes

## Data Model

### Database Schema

```sql
CREATE TABLE stock_watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code VARCHAR(20) UNIQUE NOT NULL,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Python Model

Location: `src/storage.py`

```python
class StockWatchlist(Base):
    __tablename__ = 'stock_watchlist'

    id: int
    stock_code: str  # unique
    added_at: datetime
```

## API Design

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/watchlist` | Get all stocks with real-time quotes |
| `POST` | `/api/v1/watchlist/{stock_code}` | Add stock to watchlist |
| `DELETE` | `/api/v1/watchlist/{stock_code}` | Remove stock from watchlist |

### Schemas

Location: `api/v1/schemas/watchlist.py`

```python
class WatchlistItem(BaseModel):
    stock_code: str
    stock_name: Optional[str]
    added_at: datetime
    quote: Optional[StockQuote]

class WatchlistResponse(BaseModel):
    stocks: List[WatchlistItem]
    total: int
```

### Error Handling

- `409 Conflict` - Stock already in watchlist (on add)
- `404 Not Found` - Stock not in watchlist (on delete)
- `500 Internal Error` - Database or quote fetch failure

## Architecture

### File Structure

```
src/
├── storage.py                    # Add StockWatchlist model
├── repositories/
│   └── watchlist_repo.py         # New: WatchlistRepository
├── services/
│   └── watchlist_service.py      # New: WatchlistService
api/v1/
├── endpoints/
│   └── watchlist.py              # New: API endpoints
├── schemas/
│   └── watchlist.py              # New: Request/Response schemas
└── router.py                     # Register watchlist router
```

### Service Layer

Location: `src/services/watchlist_service.py`

```python
class WatchlistService:
    def __init__(self):
        self.repo = WatchlistRepository()
        self.stock_service = StockService()

    def add_stock(self, stock_code: str) -> StockWatchlist
    def remove_stock(self, stock_code: str) -> bool
    def get_all_with_quotes(self) -> List[WatchlistItem]
```

### Key Behaviors

1. **Add stock**: Insert into database, return created item
2. **Get watchlist**: Fetch all stocks, then get real-time quotes using `StockService.get_realtime_quote()`
3. **Remove stock**: Delete from database, return success/failure
