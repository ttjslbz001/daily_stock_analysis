# Stock Watchlist API Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a standalone stock watchlist API for managing a global list of stocks with real-time quotes.

**Architecture:** Database-backed storage with repository/service pattern. New `StockWatchlist` model, `WatchlistRepository`, `WatchlistService`, and FastAPI endpoints following existing patterns from groups API.

**Tech Stack:** SQLAlchemy, FastAPI, Pydantic, pytest

---

### Task 1: Add StockWatchlist Model

**Files:**
- Modify: `src/storage.py` (add model after existing models)
- Test: `tests/storage/test_watchlist_model.py` (new file)

**Step 1: Write the failing test**

Create `tests/storage/test_watchlist_model.py`:

```python
# -*- coding: utf-8 -*-
"""Tests for StockWatchlist model."""

import pytest
from datetime import datetime

from src.storage import StockWatchlist


def test_watchlist_model_creation():
    """Test StockWatchlist model can be instantiated."""
    item = StockWatchlist(stock_code="600519")
    assert item.stock_code == "600519"
    assert item.added_at is None  # Set by DB default


def test_watchlist_model_repr():
    """Test StockWatchlist string representation."""
    item = StockWatchlist(stock_code="00700")
    assert "StockWatchlist" in repr(item)
    assert "00700" in repr(item)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/storage/test_watchlist_model.py -v`
Expected: FAIL with "cannot import name 'StockWatchlist'"

**Step 3: Write minimal implementation**

Add to `src/storage.py` after the `StockGroup` class (around line 450):

```python
class StockWatchlist(Base):
    """
    股票自选列表模型

    存储用户关注的股票代码
    """
    __tablename__ = 'stock_watchlist'

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(20), unique=True, nullable=False, index=True)
    added_at = Column(DateTime, default=datetime.now, nullable=False)

    def __repr__(self):
        return f"<StockWatchlist(id={self.id}, stock_code='{self.stock_code}')>"
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/storage/test_watchlist_model.py -v`
Expected: PASS (2 tests)

**Step 5: Commit**

```bash
git add src/storage.py tests/storage/test_watchlist_model.py
git commit -m "feat(storage): add StockWatchlist model"
```

---

### Task 2: Create WatchlistRepository

**Files:**
- Create: `src/repositories/watchlist_repo.py`
- Test: `tests/repositories/test_watchlist_repo.py` (new file)

**Step 1: Write the failing test**

Create `tests/repositories/test_watchlist_repo.py`:

```python
# -*- coding: utf-8 -*-
"""Tests for WatchlistRepository."""

import os
import tempfile

import pytest
from sqlalchemy import create_engine

from src.storage import DatabaseManager, Base, StockWatchlist
from src.repositories.watchlist_repo import WatchlistRepository


@pytest.fixture
def repo():
    """Create repository with temp database."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    db_url = f"sqlite:///{path}"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)

    DatabaseManager.reset_instance()
    DatabaseManager(db_url)

    yield WatchlistRepository()

    DatabaseManager.reset_instance()
    if os.path.exists(path):
        os.unlink(path)


def test_add_stock(repo):
    """Test adding a stock to watchlist."""
    item = repo.add("600519")
    assert item.stock_code == "600519"
    assert item.id is not None
    assert item.added_at is not None


def test_add_duplicate_returns_existing(repo):
    """Test that adding duplicate returns existing item."""
    item1 = repo.add("600519")
    item2 = repo.add("600519")
    assert item1.id == item2.id


def test_remove_stock(repo):
    """Test removing a stock from watchlist."""
    repo.add("600519")
    removed = repo.remove("600519")
    assert removed is True

    all_items = repo.get_all()
    assert len(all_items) == 0


def test_remove_nonexistent_returns_false(repo):
    """Test removing non-existent stock returns False."""
    removed = repo.remove("NOTEXIST")
    assert removed is False


def test_get_all(repo):
    """Test getting all watchlist items."""
    repo.add("600519")
    repo.add("00700")

    items = repo.get_all()
    assert len(items) == 2
    codes = [i.stock_code for i in items]
    assert "600519" in codes
    assert "00700" in codes


def test_get_by_code(repo):
    """Test getting item by stock code."""
    repo.add("600519")

    item = repo.get_by_code("600519")
    assert item is not None
    assert item.stock_code == "600519"

    item = repo.get_by_code("NOTEXIST")
    assert item is None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/repositories/test_watchlist_repo.py -v`
Expected: FAIL with "cannot import name 'WatchlistRepository'"

**Step 3: Write minimal implementation**

Create `src/repositories/watchlist_repo.py`:

```python
# -*- coding: utf-8 -*-
"""Watchlist repository for database operations."""

from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError

from src.storage import DatabaseManager, StockWatchlist


class WatchlistRepository:
    """Repository for watchlist database operations."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db_manager = db_manager or DatabaseManager.get_instance()

    def add(self, stock_code: str) -> StockWatchlist:
        """Add a stock to watchlist. Returns existing if duplicate."""
        with self.db_manager.session_scope() as session:
            # Check if exists first
            stmt = select(StockWatchlist).where(StockWatchlist.stock_code == stock_code)
            existing = session.execute(stmt).scalar_one_or_none()
            if existing:
                session.expunge(existing)
                return existing

            # Create new
            item = StockWatchlist(stock_code=stock_code)
            session.add(item)
            session.flush()
            session.refresh(item)
            result = StockWatchlist(
                id=item.id,
                stock_code=item.stock_code,
                added_at=item.added_at
            )
            return result

    def remove(self, stock_code: str) -> bool:
        """Remove a stock from watchlist. Returns True if removed."""
        with self.db_manager.session_scope() as session:
            stmt = delete(StockWatchlist).where(StockWatchlist.stock_code == stock_code)
            result = session.execute(stmt)
            return result.rowcount > 0

    def get_all(self) -> List[StockWatchlist]:
        """Get all watchlist items."""
        with self.db_manager.session_scope() as session:
            stmt = select(StockWatchlist).order_by(StockWatchlist.added_at.desc())
            results = session.execute(stmt).scalars().all()
            for r in results:
                session.expunge(r)
            return list(results)

    def get_by_code(self, stock_code: str) -> Optional[StockWatchlist]:
        """Get a watchlist item by stock code."""
        with self.db_manager.session_scope() as session:
            stmt = select(StockWatchlist).where(StockWatchlist.stock_code == stock_code)
            result = session.execute(stmt).scalar_one_or_none()
            if result:
                session.expunge(result)
            return result
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/repositories/test_watchlist_repo.py -v`
Expected: PASS (6 tests)

**Step 5: Commit**

```bash
git add src/repositories/watchlist_repo.py tests/repositories/test_watchlist_repo.py
git commit -m "feat(repo): add WatchlistRepository"
```

---

### Task 3: Create WatchlistService

**Files:**
- Create: `src/services/watchlist_service.py`
- Test: `tests/services/test_watchlist_service.py` (new file)

**Step 1: Write the failing test**

Create `tests/services/test_watchlist_service.py`:

```python
# -*- coding: utf-8 -*-
"""Tests for WatchlistService."""

import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy import create_engine

from src.storage import DatabaseManager, Base
from src.services.watchlist_service import WatchlistService


@pytest.fixture
def service():
    """Create service with temp database."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    db_url = f"sqlite:///{path}"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)

    DatabaseManager.reset_instance()
    DatabaseManager(db_url)

    yield WatchlistService()

    DatabaseManager.reset_instance()
    if os.path.exists(path):
        os.unlink(path)


def test_add_stock(service):
    """Test adding a stock to watchlist."""
    item = service.add_stock("600519")
    assert item.stock_code == "600519"


def test_remove_stock(service):
    """Test removing a stock from watchlist."""
    service.add_stock("600519")
    removed = service.remove_stock("600519")
    assert removed is True


def test_remove_nonexistent(service):
    """Test removing non-existent stock."""
    removed = service.remove_stock("NOTEXIST")
    assert removed is False


def test_get_all_empty(service):
    """Test getting all from empty watchlist."""
    items = service.get_all()
    assert items == []


def test_get_all_with_items(service):
    """Test getting all watchlist items."""
    service.add_stock("600519")
    service.add_stock("00700")

    items = service.get_all()
    assert len(items) == 2
    codes = [i.stock_code for i in items]
    assert "600519" in codes
    assert "00700" in codes
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/services/test_watchlist_service.py -v`
Expected: FAIL with "cannot import name 'WatchlistService'"

**Step 3: Write minimal implementation**

Create `src/services/watchlist_service.py`:

```python
# -*- coding: utf-8 -*-
"""Watchlist service for business logic."""

import logging
from typing import List, Optional

from src.storage import DatabaseManager, StockWatchlist
from src.repositories.watchlist_repo import WatchlistRepository

logger = logging.getLogger(__name__)


class WatchlistService:
    """Service for managing stock watchlist."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.repo = WatchlistRepository(db_manager)

    def add_stock(self, stock_code: str) -> StockWatchlist:
        """
        Add a stock to the watchlist.

        Args:
            stock_code: Stock code to add

        Returns:
            StockWatchlist instance
        """
        return self.repo.add(stock_code)

    def remove_stock(self, stock_code: str) -> bool:
        """
        Remove a stock from the watchlist.

        Args:
            stock_code: Stock code to remove

        Returns:
            True if removed, False if not found
        """
        return self.repo.remove(stock_code)

    def get_all(self) -> List[StockWatchlist]:
        """
        Get all stocks in watchlist.

        Returns:
            List of StockWatchlist items
        """
        return self.repo.get_all()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/services/test_watchlist_service.py -v`
Expected: PASS (5 tests)

**Step 5: Commit**

```bash
git add src/services/watchlist_service.py tests/services/test_watchlist_service.py
git commit -m "feat(service): add WatchlistService"
```

---

### Task 4: Create API Schemas

**Files:**
- Create: `api/v1/schemas/watchlist.py`

**Step 1: Write the schemas**

Create `api/v1/schemas/watchlist.py`:

```python
# -*- coding: utf-8 -*-
"""Pydantic schemas for watchlist API."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict

from api.v1.schemas.stocks import StockQuote


class WatchlistItem(BaseModel):
    """Schema for a single watchlist item with quote."""

    model_config = ConfigDict(from_attributes=True)

    stock_code: str = Field(..., description="股票代码")
    stock_name: Optional[str] = Field(None, description="股票名称")
    added_at: datetime = Field(..., description="添加时间")
    quote: Optional[StockQuote] = Field(None, description="实时行情")


class WatchlistResponse(BaseModel):
    """Schema for watchlist list response."""

    stocks: List[WatchlistItem] = Field(..., description="自选股列表")
    total: int = Field(..., description="总数")


class AddStockResponse(BaseModel):
    """Schema for add stock response."""

    stock_code: str = Field(..., description="股票代码")
    added_at: datetime = Field(..., description="添加时间")
    message: str = Field(default="添加成功", description="消息")
```

**Step 2: Commit**

```bash
git add api/v1/schemas/watchlist.py
git commit -m "feat(schemas): add watchlist API schemas"
```

---

### Task 5: Create API Endpoints

**Files:**
- Create: `api/v1/endpoints/watchlist.py`
- Test: `tests/api/test_watchlist.py` (new file)

**Step 1: Write the failing test**

Create `tests/api/test_watchlist.py`:

```python
# -*- coding: utf-8 -*-
"""Integration tests for watchlist API endpoints."""

import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client with temp database."""
    from api.app import create_app
    from src.storage import DatabaseManager, Base
    from sqlalchemy import create_engine

    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    db_url = f"sqlite:///{path}"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)

    DatabaseManager.reset_instance()
    DatabaseManager(db_url)

    app = create_app()

    with TestClient(app) as test_client:
        yield test_client

    DatabaseManager.reset_instance()
    if os.path.exists(path):
        os.unlink(path)


def test_add_stock_api(client):
    """Test POST /api/v1/watchlist/{stock_code} endpoint."""
    response = client.post("/api/v1/watchlist/600519")

    assert response.status_code == 200
    data = response.json()
    assert data["stock_code"] == "600519"
    assert "added_at" in data


def test_list_watchlist_api(client):
    """Test GET /api/v1/watchlist endpoint."""
    # Add two stocks
    client.post("/api/v1/watchlist/600519")
    client.post("/api/v1/watchlist/00700")

    # Mock the quote service to avoid external calls
    with patch('src.services.watchlist_service.WatchlistService.get_all_with_quotes') as mock:
        mock.return_value = [
            {
                "stock_code": "600519",
                "stock_name": "贵州茅台",
                "added_at": "2024-01-01T00:00:00",
                "quote": None
            },
            {
                "stock_code": "00700",
                "stock_name": "腾讯控股",
                "added_at": "2024-01-01T00:00:00",
                "quote": None
            }
        ]
        response = client.get("/api/v1/watchlist")

    assert response.status_code == 200
    data = response.json()
    assert "stocks" in data
    assert data["total"] == 2


def test_remove_stock_api(client):
    """Test DELETE /api/v1/watchlist/{stock_code} endpoint."""
    # Add then remove
    client.post("/api/v1/watchlist/600519")
    response = client.delete("/api/v1/watchlist/600519")

    assert response.status_code == 204

    # Verify removed
    with patch('src.services.watchlist_service.WatchlistService.get_all_with_quotes') as mock:
        mock.return_value = []
        list_resp = client.get("/api/v1/watchlist")

    data = list_resp.json()
    assert data["total"] == 0


def test_remove_nonexistent_api(client):
    """Test DELETE returns 404 for non-existent stock."""
    response = client.delete("/api/v1/watchlist/NOTEXIST")
    assert response.status_code == 404
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_watchlist.py -v`
Expected: FAIL with "404 Not Found" (endpoint not registered)

**Step 3: Write minimal implementation**

Create `api/v1/endpoints/watchlist.py`:

```python
# -*- coding: utf-8 -*-
"""Watchlist API endpoints."""

import logging
from typing import Optional

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
        stocks = service.get_all_with_quotes()
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
```

**Step 4: Update WatchlistService to add get_all_with_quotes method**

Add to `src/services/watchlist_service.py`:

```python
def get_all_with_quotes(self) -> List[dict]:
    """
    Get all stocks with real-time quotes.

    Returns:
        List of dicts with stock_code, stock_name, added_at, quote
    """
    from src.services.stock_service import StockService

    stock_service = StockService()
    items = self.get_all()

    result = []
    for item in items:
        quote_data = stock_service.get_realtime_quote(item.stock_code)
        quote = None
        stock_name = None

        if quote_data:
            stock_name = quote_data.get("stock_name")
            from api.v1.schemas.stocks import StockQuote
            quote = StockQuote(
                stock_code=quote_data.get("stock_code", item.stock_code),
                stock_name=quote_data.get("stock_name"),
                current_price=quote_data.get("current_price", 0.0),
                change=quote_data.get("change"),
                change_percent=quote_data.get("change_percent"),
                open=quote_data.get("open"),
                high=quote_data.get("high"),
                low=quote_data.get("low"),
                prev_close=quote_data.get("prev_close"),
                volume=quote_data.get("volume"),
                amount=quote_data.get("amount"),
                update_time=quote_data.get("update_time")
            )

        result.append({
            "stock_code": item.stock_code,
            "stock_name": stock_name,
            "added_at": item.added_at,
            "quote": quote
        })

    return result
```

**Step 5: Register router in `api/v1/router.py`**

Add import and router registration:

```python
# Add to imports at top
from api.v1.endpoints import analysis, auth, history, stocks, backtest, system_config, agent, groups, watchlist

# Add after groups router (at end of file)
router.include_router(
    watchlist.router,
    prefix="/watchlist",
    tags=["Watchlist"]
)
```

**Step 6: Run test to verify it passes**

Run: `pytest tests/api/test_watchlist.py -v`
Expected: PASS (4 tests)

**Step 7: Commit**

```bash
git add api/v1/endpoints/watchlist.py api/v1/router.py src/services/watchlist_service.py tests/api/test_watchlist.py
git commit -m "feat(api): add watchlist API endpoints"
```

---

### Task 6: Final Verification

**Step 1: Run all tests**

Run: `pytest tests/ -v --tb=short`
Expected: All tests pass

**Step 2: Start server and test manually**

Run: `python -m uvicorn api.app:app --reload`

Test endpoints:
```bash
# Add stock
curl -X POST http://localhost:8000/api/v1/watchlist/600519

# List watchlist
curl http://localhost:8000/api/v1/watchlist

# Remove stock
curl -X DELETE http://localhost:8000/api/v1/watchlist/600519
```

**Step 3: Final commit (if any fixes needed)**

```bash
git add -A
git commit -m "feat(watchlist): complete watchlist API implementation"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Add StockWatchlist model | `src/storage.py`, `tests/storage/test_watchlist_model.py` |
| 2 | Create WatchlistRepository | `src/repositories/watchlist_repo.py`, `tests/repositories/test_watchlist_repo.py` |
| 3 | Create WatchlistService | `src/services/watchlist_service.py`, `tests/services/test_watchlist_service.py` |
| 4 | Create API schemas | `api/v1/schemas/watchlist.py` |
| 5 | Create API endpoints | `api/v1/endpoints/watchlist.py`, `api/v1/router.py`, `tests/api/test_watchlist.py` |
| 6 | Final verification | - |
