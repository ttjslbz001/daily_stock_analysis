# Stock Tags Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add free-form tagging for individual stocks, managed in the Groups page.

**Architecture:** New `StockTag` table with stock_code + tag_name. Repository/Service/API layers following existing patterns. Frontend adds inline tag editor to GroupCard component.

**Tech Stack:** SQLAlchemy, FastAPI, Pydantic, React, Zustand, Tailwind CSS

---

## Task 1: Add StockTag Model

**Files:**
- Modify: `src/storage.py`

**Step 1: Add StockTag model after StockGroup class (around line 425)**

```python
class StockTag(Base):
    """
    股票标签模型

    允许用户为股票添加自由标签（如"关注"、"突破"等）
    """
    __tablename__ = 'stock_tags'

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 股票代码
    stock_code = Column(String(10), nullable=False, index=True)

    # 标签名称
    tag_name = Column(String(50), nullable=False, index=True)

    # 时间戳
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # 索引和约束
    __table_args__ = (
        UniqueConstraint('stock_code', 'tag_name', name='uq_stock_tag'),
        Index('idx_stock_tags_code', 'stock_code'),
        Index('idx_stock_tags_name', 'tag_name'),
    )
```

**Step 2: Verify model is loaded by DatabaseManager**

The existing `DatabaseManager` uses `Base.metadata.create_all`, so the new table will be created automatically.

**Step 3: Commit**

```bash
git add src/storage.py
git commit -m "feat(models): add StockTag model for stock tagging"
```

---

## Task 2: Create StockTag Repository

**Files:**
- Create: `src/repositories/stock_tag_repo.py`

**Step 1: Create the repository file**

```python
# -*- coding: utf-8 -*-
"""Stock tag repository for database operations."""

from typing import List, Optional
from sqlalchemy import select, delete, distinct
from sqlalchemy.exc import IntegrityError

from src.storage import DatabaseManager, StockTag


class StockTagRepository:
    """Repository for stock tag database operations."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db_manager = db_manager or DatabaseManager.get_instance()

    def get_tags_for_stock(self, stock_code: str) -> List[str]:
        """Get all tag names for a stock."""
        with self.db_manager.session_scope() as session:
            stmt = select(StockTag.tag_name).where(
                StockTag.stock_code == stock_code
            ).order_by(StockTag.tag_name)
            results = session.execute(stmt).scalars().all()
            return list(results)

    def get_stocks_by_tag(self, tag_name: str) -> List[str]:
        """Get all stock codes with a specific tag."""
        with self.db_manager.session_scope() as session:
            stmt = select(StockTag.stock_code).where(
                StockTag.tag_name == tag_name
            ).order_by(StockTag.stock_code)
            results = session.execute(stmt).scalars().all()
            return list(results)

    def add_tag(self, stock_code: str, tag_name: str) -> StockTag:
        """Add a tag to a stock. Returns the created tag."""
        with self.db_manager.session_scope() as session:
            tag = StockTag(stock_code=stock_code, tag_name=tag_name)
            try:
                session.add(tag)
                session.flush()
                session.refresh(tag)
                # Return a detached copy
                return StockTag(
                    id=tag.id,
                    stock_code=tag.stock_code,
                    tag_name=tag.tag_name,
                    created_at=tag.created_at
                )
            except IntegrityError:
                session.rollback()
                # Tag already exists, return existing
                stmt = select(StockTag).where(
                    StockTag.stock_code == stock_code,
                    StockTag.tag_name == tag_name
                )
                existing = session.execute(stmt).scalar_one_or_none()
                return existing

    def remove_tag(self, stock_code: str, tag_name: str) -> bool:
        """Remove a tag from a stock. Returns True if removed."""
        with self.db_manager.session_scope() as session:
            stmt = delete(StockTag).where(
                StockTag.stock_code == stock_code,
                StockTag.tag_name == tag_name
            )
            result = session.execute(stmt)
            return result.rowcount > 0

    def get_all_tags(self) -> List[str]:
        """Get all unique tag names for autocomplete."""
        with self.db_manager.session_scope() as session:
            stmt = select(distinct(StockTag.tag_name)).order_by(StockTag.tag_name)
            results = session.execute(stmt).scalars().all()
            return list(results)
```

**Step 2: Commit**

```bash
git add src/repositories/stock_tag_repo.py
git commit -m "feat(repo): add StockTagRepository for tag operations"
```

---

## Task 3: Create StockTag Service

**Files:**
- Create: `src/services/stock_tag_service.py`

**Step 1: Create the service file**

```python
# -*- coding: utf-8 -*-
"""Stock tag service for business logic."""

from typing import List, Optional

from src.storage import DatabaseManager
from src.repositories.stock_tag_repo import StockTagRepository


class StockTagService:
    """Service for managing stock tags."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.repo = StockTagRepository(db_manager)

    def get_tags(self, stock_code: str) -> List[str]:
        """Get all tags for a stock."""
        return self.repo.get_tags_for_stock(stock_code)

    def add_tag(self, stock_code: str, tag_name: str):
        """Add a tag to a stock."""
        # Normalize tag name (trim and lowercase for consistency)
        normalized_tag = tag_name.strip()
        if not normalized_tag:
            raise ValueError("Tag name cannot be empty")
        return self.repo.add_tag(stock_code, normalized_tag)

    def remove_tag(self, stock_code: str, tag_name: str) -> bool:
        """Remove a tag from a stock."""
        return self.repo.remove_tag(stock_code, tag_name.strip())

    def get_all_tags(self) -> List[str]:
        """Get all unique tag names."""
        return self.repo.get_all_tags()
```

**Step 2: Commit**

```bash
git add src/services/stock_tag_service.py
git commit -m "feat(service): add StockTagService for tag business logic"
```

---

## Task 4: Create API Schemas

**Files:**
- Create: `api/v1/schemas/tags.py`

**Step 1: Create the schemas file**

```python
# -*- coding: utf-8 -*-
"""Pydantic schemas for stock tags API."""

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field, ConfigDict


class TagCreate(BaseModel):
    """Schema for adding a tag to a stock."""

    model_config = ConfigDict(populate_by_name=True)

    tag_name: str = Field(..., description="标签名称", min_length=1, max_length=50)


class TagListResponse(BaseModel):
    """Schema for tag list response."""

    tags: List[str] = Field(..., description="标签列表")


class AllTagsResponse(BaseModel):
    """Schema for all unique tags response."""

    tags: List[str] = Field(..., description="所有唯一标签")
```

**Step 2: Commit**

```bash
git add api/v1/schemas/tags.py
git commit -m "feat(schemas): add Pydantic schemas for tags API"
```

---

## Task 5: Create API Endpoints

**Files:**
- Create: `api/v1/endpoints/tags.py`
- Modify: `api/v1/router.py`

**Step 1: Create the endpoints file**

```python
# -*- coding: utf-8 -*-
"""Stock tags API endpoints."""

import logging

from fastapi import APIRouter, HTTPException

from api.v1.schemas.tags import TagCreate, TagListResponse, AllTagsResponse
from api.v1.schemas.common import ErrorResponse
from src.services.stock_tag_service import StockTagService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/",
    response_model=AllTagsResponse,
    summary="获取所有标签",
    description="获取所有唯一标签名称，用于自动完成"
)
def get_all_tags():
    """Get all unique tags."""
    try:
        service = StockTagService()
        tags = service.get_all_tags()
        return AllTagsResponse(tags=tags)
    except Exception as e:
        logger.error(f"Failed to get all tags: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": "获取标签列表失败"}
        )


@router.get(
    "/{stock_code}",
    response_model=TagListResponse,
    summary="获取股票标签",
    description="获取指定股票的所有标签"
)
def get_stock_tags(stock_code: str):
    """Get tags for a specific stock."""
    try:
        service = StockTagService()
        tags = service.get_tags(stock_code)
        return TagListResponse(tags=tags)
    except Exception as e:
        logger.error(f"Failed to get tags for {stock_code}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": "获取股票标签失败"}
        )


@router.post(
    "/{stock_code}",
    response_model=TagListResponse,
    summary="添加股票标签",
    description="为指定股票添加一个标签"
)
def add_stock_tag(stock_code: str, body: TagCreate):
    """Add a tag to a stock."""
    try:
        service = StockTagService()
        service.add_tag(stock_code, body.tag_name)
        tags = service.get_tags(stock_code)
        return TagListResponse(tags=tags)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_tag", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Failed to add tag to {stock_code}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": "添加标签失败"}
        )


@router.delete(
    "/{stock_code}/{tag_name}",
    response_model=TagListResponse,
    summary="删除股票标签",
    description="从指定股票删除一个标签"
)
def remove_stock_tag(stock_code: str, tag_name: str):
    """Remove a tag from a stock."""
    try:
        service = StockTagService()
        service.remove_tag(stock_code, tag_name)
        tags = service.get_tags(stock_code)
        return TagListResponse(tags=tags)
    except Exception as e:
        logger.error(f"Failed to remove tag from {stock_code}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "internal_error", "message": "删除标签失败"}
        )
```

**Step 2: Register router in `api/v1/router.py`**

Add import at top:
```python
from api.v1.endpoints import analysis, auth, history, stocks, backtest, system_config, agent, groups, tags
```

Add router registration after groups router (around line 65):
```python
router.include_router(
    tags.router,
    prefix="/stocks",
    tags=["StockTags"]
)
```

**Step 3: Commit**

```bash
git add api/v1/endpoints/tags.py api/v1/router.py
git commit -m "feat(api): add stock tags REST API endpoints"
```

---

## Task 6: Create Frontend Tags API

**Files:**
- Create: `apps/dsa-web/src/api/tags.ts`
- Modify: `apps/dsa-web/src/api/index.ts`

**Step 1: Create the API file**

```typescript
import apiClient from './index';
import { toCamelCase } from './utils';

export interface TagListResponse {
  tags: string[];
}

export interface AddTagRequest {
  tagName: string;
}

export const tagsApi = {
  // Get all unique tags (for autocomplete)
  getAllTags: async (): Promise<string[]> => {
    const response = await apiClient.get('/api/v1/stocks/tags');
    return toCamelCase(response.data).tags;
  },

  // Get tags for a specific stock
  getStockTags: async (code: string): Promise<string[]> => {
    const response = await apiClient.get(`/api/v1/stocks/${code}`);
    return toCamelCase(response.data).tags;
  },

  // Add a tag to a stock
  addTag: async (code: string, tagName: string): Promise<string[]> => {
    const response = await apiClient.post(`/api/v1/stocks/${code}`, { tag_name: tagName });
    return toCamelCase(response.data).tags;
  },

  // Remove a tag from a stock
  removeTag: async (code: string, tagName: string): Promise<string[]> => {
    const response = await apiClient.delete(`/api/v1/stocks/${code}/${encodeURIComponent(tagName)}`);
    return toCamelCase(response.data).tags;
  },
};
```

**Step 2: Export from `apps/dsa-web/src/api/index.ts`**

Add to the file:
```typescript
export * from './tags';
```

**Step 3: Commit**

```bash
git add apps/dsa-web/src/api/tags.ts apps/dsa-web/src/api/index.ts
git commit -m "feat(frontend): add tags API client"
```

---

## Task 7: Create Tags Store

**Files:**
- Create: `apps/dsa-web/src/stores/tagsStore.ts`

**Step 1: Create the store file**

```typescript
import { create } from 'zustand';
import { tagsApi } from '../api/tags';

interface TagsState {
  // Stock code -> tags mapping
  stockTags: Record<string, string[]>;
  // All unique tags for autocomplete
  allTags: string[];
  loading: boolean;
  error: string | null;

  // Actions
  fetchStockTags: (code: string) => Promise<void>;
  fetchAllTags: () => Promise<void>;
  addTag: (code: string, tag: string) => Promise<void>;
  removeTag: (code: string, tag: string) => Promise<void>;
}

export const useTagsStore = create<TagsState>((set, get) => ({
  stockTags: {},
  allTags: [],
  loading: false,
  error: null,

  fetchStockTags: async (code: string) => {
    try {
      const tags = await tagsApi.getStockTags(code);
      set(state => ({
        stockTags: { ...state.stockTags, [code]: tags },
      }));
    } catch (error: any) {
      set({ error: error.message });
    }
  },

  fetchAllTags: async () => {
    try {
      const tags = await tagsApi.getAllTags();
      set({ allTags: tags });
    } catch (error: any) {
      set({ error: error.message });
    }
  },

  addTag: async (code: string, tag: string) => {
    try {
      const tags = await tagsApi.addTag(code, tag);
      set(state => ({
        stockTags: { ...state.stockTags, [code]: tags },
        // Add to allTags if new
        allTags: state.allTags.includes(tag)
          ? state.allTags
          : [...state.allTags, tag].sort(),
      }));
    } catch (error: any) {
      set({ error: error.message });
      throw error;
    }
  },

  removeTag: async (code: string, tag: string) => {
    try {
      const tags = await tagsApi.removeTag(code, tag);
      set(state => ({
        stockTags: { ...state.stockTags, [code]: tags },
      }));
    } catch (error: any) {
      set({ error: error.message });
      throw error;
    }
  },
}));
```

**Step 2: Commit**

```bash
git add apps/dsa-web/src/stores/tagsStore.ts
git commit -m "feat(frontend): add Zustand store for tags"
```

---

## Task 8: Create StockTagEditor Component

**Files:**
- Create: `apps/dsa-web/src/components/stocks/StockTagEditor.tsx`

**Step 1: Create the component directory if needed**

```bash
mkdir -p apps/dsa-web/src/components/stocks
```

**Step 2: Create the component file**

```typescript
import React, { useState, useEffect, useRef } from 'react';
import { useTagsStore } from '../../stores/tagsStore';

interface Props {
  stockCode: string;
  onClose?: () => void;
}

export const StockTagEditor: React.FC<Props> = ({ stockCode, onClose }) => {
  const { stockTags, allTags, fetchStockTags, fetchAllTags, addTag, removeTag } = useTagsStore();
  const [newTag, setNewTag] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const tags = stockTags[stockCode] || [];

  useEffect(() => {
    fetchStockTags(stockCode);
    if (allTags.length === 0) {
      fetchAllTags();
    }
  }, [stockCode]);

  // Filter suggestions based on input
  const suggestions = newTag.trim()
    ? allTags.filter(t =>
        t.toLowerCase().includes(newTag.toLowerCase()) &&
        !tags.includes(t)
      )
    : allTags.filter(t => !tags.includes(t));

  const handleAddTag = async (tag?: string) => {
    const tagToAdd = tag || newTag.trim();
    if (!tagToAdd) return;

    try {
      await addTag(stockCode, tagToAdd);
      setNewTag('');
      setShowSuggestions(false);
    } catch (e) {
      console.error('Failed to add tag:', e);
    }
  };

  const handleRemoveTag = async (tag: string) => {
    try {
      await removeTag(stockCode, tag);
    } catch (e) {
      console.error('Failed to remove tag:', e);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
      onClose?.();
    }
  };

  return (
    <div className="mt-2 p-2 bg-gray-900 rounded border border-gray-600">
      <div className="text-xs text-gray-400 mb-2">标签管理: {stockCode}</div>

      {/* Existing tags */}
      <div className="flex flex-wrap gap-1 mb-2">
        {tags.map(tag => (
          <span
            key={tag}
            className="inline-flex items-center px-2 py-0.5 bg-cyan-900/50 text-cyan-300 rounded text-xs"
          >
            {tag}
            <button
              onClick={() => handleRemoveTag(tag)}
              className="ml-1 text-cyan-400 hover:text-red-400"
            >
              ×
            </button>
          </span>
        ))}
        {tags.length === 0 && (
          <span className="text-xs text-gray-500">暂无标签</span>
        )}
      </div>

      {/* Add new tag */}
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={newTag}
          onChange={e => {
            setNewTag(e.target.value);
            setShowSuggestions(true);
          }}
          onFocus={() => setShowSuggestions(true)}
          onKeyDown={handleKeyDown}
          placeholder="添加标签..."
          className="w-full px-2 py-1 bg-gray-800 border border-gray-600 rounded text-sm text-white placeholder-gray-500 focus:outline-none focus:border-cyan-500"
        />

        {/* Autocomplete suggestions */}
        {showSuggestions && suggestions.length > 0 && (
          <div className="absolute z-10 w-full mt-1 bg-gray-800 border border-gray-600 rounded shadow-lg max-h-32 overflow-y-auto">
            {suggestions.slice(0, 5).map(tag => (
              <button
                key={tag}
                onClick={() => handleAddTag(tag)}
                className="w-full px-2 py-1 text-left text-sm text-white hover:bg-gray-700"
              >
                {tag}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex justify-end mt-2">
        <button
          onClick={onClose}
          className="text-xs text-gray-400 hover:text-white"
        >
          完成
        </button>
      </div>
    </div>
  );
};
```

**Step 3: Commit**

```bash
git add apps/dsa-web/src/components/stocks/StockTagEditor.tsx
git commit -m "feat(frontend): add StockTagEditor component"
```

---

## Task 9: Update GroupCard to Integrate Tags

**Files:**
- Modify: `apps/dsa-web/src/components/groups/GroupCard.tsx`

**Step 1: Update GroupCard to show tag indicators and inline editor**

Replace the entire file content:

```typescript
import React, { useState } from 'react';
import type { StockGroup } from '../../api/groups';
import { useTagsStore } from '../../stores/tagsStore';
import { StockTagEditor } from '../stocks/StockTagEditor';

interface Props {
  group: StockGroup;
  onEdit: (group: StockGroup) => void;
  onDelete: (id: number) => void;
}

export const GroupCard: React.FC<Props> = ({ group, onEdit, onDelete }) => {
  const { stockTags, fetchStockTags } = useTagsStore();
  const [expandedStock, setExpandedStock] = useState<string | null>(null);

  // Get tags for a stock, with indicator
  const getTagIndicator = (code: string) => {
    const tags = stockTags[code];
    if (!tags) return null;
    return tags.length > 0 ? (
      <span className="ml-1 w-2 h-2 bg-cyan-500 rounded-full inline-block" title={`${tags.length} 个标签`} />
    ) : null;
  };

  const handleStockClick = (code: string) => {
    if (expandedStock === code) {
      setExpandedStock(null);
    } else {
      fetchStockTags(code);
      setExpandedStock(code);
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <div className="flex justify-between items-start mb-2">
        <div>
          <h3 className="text-lg font-semibold text-white">{group.name}</h3>
          {group.description && (
            <p className="text-sm text-gray-400">{group.description}</p>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => onEdit(group)}
            className="text-cyan-400 hover:text-cyan-300 text-sm"
          >
            编辑
          </button>
          <button
            onClick={() => onDelete(group.id)}
            className="text-red-400 hover:text-red-300 text-sm"
          >
            删除
          </button>
        </div>
      </div>

      <div className="text-sm text-gray-500 mb-3">
        {group.stockCodes.length} 只股票
      </div>

      <div className="flex flex-wrap gap-2">
        {group.stockCodes.map(code => (
          <div key={code} className="flex flex-col">
            <button
              onClick={() => handleStockClick(code)}
              className={`px-2 py-1 rounded text-xs transition-colors ${
                expandedStock === code
                  ? 'bg-cyan-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              {code}
              {getTagIndicator(code)}
            </button>
            {expandedStock === code && (
              <div className="mt-1 w-48">
                <StockTagEditor
                  stockCode={code}
                  onClose={() => setExpandedStock(null)}
                />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
```

**Step 2: Commit**

```bash
git add apps/dsa-web/src/components/groups/GroupCard.tsx
git commit -m "feat(frontend): integrate tag editor into GroupCard"
```

---

## Task 10: Add Backend Tests

**Files:**
- Create: `tests/api/test_tags.py`

**Step 1: Create the test file**

```python
# -*- coding: utf-8 -*-
"""Integration tests for stock tags API endpoints."""

import os
import tempfile

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client with temp database."""
    from api.app import create_app
    from src.storage import DatabaseManager, Base
    from sqlalchemy import create_engine

    # Create temp database
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    db_url = f"sqlite:///{path}"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)

    # Reset singleton and create new instance
    DatabaseManager.reset_instance()
    db_manager = DatabaseManager(db_url)

    # Create app with test database
    app = create_app()

    with TestClient(app) as test_client:
        yield test_client

    # Cleanup
    DatabaseManager.reset_instance()
    if os.path.exists(path):
        os.unlink(path)


def test_add_tag_api(client):
    """Test POST /api/v1/stocks/{code} endpoint."""
    response = client.post("/api/v1/stocks/600519", json={
        "tag_name": "favorite"
    })

    assert response.status_code == 200
    data = response.json()
    assert "favorite" in data["tags"]


def test_get_stock_tags_api(client):
    """Test GET /api/v1/stocks/{code} endpoint."""
    # Add tags
    client.post("/api/v1/stocks/600519", json={"tag_name": "favorite"})
    client.post("/api/v1/stocks/600519", json={"tag_name": "watch"})

    response = client.get("/api/v1/stocks/600519")

    assert response.status_code == 200
    data = response.json()
    assert "favorite" in data["tags"]
    assert "watch" in data["tags"]


def test_remove_tag_api(client):
    """Test DELETE /api/v1/stocks/{code}/{tag} endpoint."""
    # Add tag
    client.post("/api/v1/stocks/600519", json={"tag_name": "favorite"})

    # Remove tag
    response = client.delete("/api/v1/stocks/600519/favorite")
    assert response.status_code == 200

    # Verify removed
    get_resp = client.get("/api/v1/stocks/600519")
    assert "favorite" not in get_resp.json()["tags"]


def test_get_all_tags_api(client):
    """Test GET /api/v1/stocks/tags endpoint."""
    # Add tags to different stocks
    client.post("/api/v1/stocks/600519", json={"tag_name": "favorite"})
    client.post("/api/v1/stocks/000001", json={"tag_name": "watch"})
    client.post("/api/v1/stocks/300750", json={"tag_name": "favorite"})

    response = client.get("/api/v1/stocks/tags")

    assert response.status_code == 200
    data = response.json()
    # Should have unique tags only
    assert "favorite" in data["tags"]
    assert "watch" in data["tags"]
    assert data["tags"].count("favorite") == 1


def test_duplicate_tag_ignored(client):
    """Test that adding duplicate tag is handled gracefully."""
    client.post("/api/v1/stocks/600519", json={"tag_name": "favorite"})
    response = client.post("/api/v1/stocks/600519", json={"tag_name": "favorite"})

    # Should succeed but not duplicate
    assert response.status_code == 200
    assert response.json()["tags"].count("favorite") == 1
```

**Step 2: Run tests**

```bash
cd /Users/chenhaili/CodeHub/daily_stocks_analysis_repo/daily_stock_analysis
source .venv/bin/activate
pytest tests/api/test_tags.py -v
```

Expected: All tests pass.

**Step 3: Commit**

```bash
git add tests/api/test_tags.py
git commit -m "test(api): add integration tests for tags API"
```

---

## Task 11: Final Verification

**Step 1: Run all tests**

```bash
pytest tests/ -v
```

Expected: All tests pass.

**Step 2: Start the development server and test manually**

```bash
# Backend
python -m uvicorn api.app:create_app --factory --reload --port 8000

# Frontend (in another terminal)
cd apps/dsa-web && npm run dev
```

**Step 3: Test the feature**

1. Navigate to Groups page
2. Click on a stock code to expand tag editor
3. Add a new tag
4. Verify tag appears and persists
5. Remove the tag
6. Verify autocomplete shows existing tags

**Step 4: Final commit (if any fixes needed)**

```bash
git status
# Fix any issues, then commit
git add -A
git commit -m "fix: resolve any issues from final verification"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Add StockTag model | `src/storage.py` |
| 2 | Create repository | `src/repositories/stock_tag_repo.py` |
| 3 | Create service | `src/services/stock_tag_service.py` |
| 4 | Create API schemas | `api/v1/schemas/tags.py` |
| 5 | Create API endpoints | `api/v1/endpoints/tags.py`, `api/v1/router.py` |
| 6 | Create frontend API | `apps/dsa-web/src/api/tags.ts`, `index.ts` |
| 7 | Create tags store | `apps/dsa-web/src/stores/tagsStore.ts` |
| 8 | Create tag editor | `apps/dsa-web/src/components/stocks/StockTagEditor.tsx` |
| 9 | Update GroupCard | `apps/dsa-web/src/components/groups/GroupCard.tsx` |
| 10 | Add tests | `tests/api/test_tags.py` |
| 11 | Final verification | - |
