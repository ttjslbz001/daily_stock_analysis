# Stock Tags Feature Design

**Date:** 2026-03-09
**Status:** Approved

## Overview

Add the ability to tag individual stocks with free-form tags (e.g., "favorite", "watch", "breakout"). Tags are global per stock and managed directly in the Groups page.

## Requirements

- Tag individual stocks (not groups)
- Free-form tags - users can create any tag on-the-fly
- Manage tags in the Groups page within group cards
- Tags are global - same stock has same tags across all groups

## Data Model

### StockTag Table

```python
class StockTag(Base):
    """Stock tags for individual stocks."""
    __tablename__ = 'stock_tags'

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), nullable=False, index=True)
    tag_name = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('stock_code', 'tag_name', name='uq_stock_tag'),
        Index('idx_stock_tags_code', 'stock_code'),
        Index('idx_stock_tags_name', 'tag_name'),
    )
```

## Backend

### Repository (`src/repositories/stock_tag_repo.py`)

```python
class StockTagRepository:
    def get_tags_for_stock(self, stock_code: str) -> List[str]
    def get_stocks_by_tag(self, tag_name: str) -> List[str]
    def add_tag(self, stock_code: str, tag_name: str) -> StockTag
    def remove_tag(self, stock_code: str, tag_name: str) -> bool
    def get_all_tags(self) -> List[str]  # For autocomplete
```

### Service (`src/services/stock_tag_service.py`)

```python
class StockTagService:
    def get_tags(self, stock_code: str) -> List[str]
    def add_tag(self, stock_code: str, tag_name: str) -> StockTag
    def remove_tag(self, stock_code: str, tag_name: str) -> bool
    def get_all_tags(self) -> List[str]
```

### API Endpoints

```
GET    /api/v1/stocks/{code}/tags       -> Get tags for a stock
POST   /api/v1/stocks/{code}/tags       -> Add tag { "tagName": "favorite" }
DELETE /api/v1/stocks/{code}/tags/{tag} -> Remove tag
GET    /api/v1/tags                     -> Get all unique tags (for autocomplete)
```

## Frontend

### API (`apps/dsa-web/src/api/tags.ts`)

```typescript
export const tagsApi = {
  getStockTags: (code: string) => Promise<string[]>
  addTag: (code: string, tagName: string) => Promise<void>
  removeTag: (code: string, tagName: string) => Promise<void>
  getAllTags: () => Promise<string[]>  // For autocomplete
}
```

### Store (`apps/dsa-web/src/stores/tagsStore.ts`)

```typescript
interface TagsState {
  stockTags: Map<string, string[]>  // code -> tags
  allTags: string[]
  fetchStockTags: (code: string) => Promise<void>
  addTag: (code: string, tag: string) => Promise<void>
  removeTag: (code: string, tag: string) => Promise<void>
}
```

### UI Components

**GroupCard enhancement:**
- Click stock code to expand inline tag editor
- Show existing tags with × to remove
- Input field to add new tag (with autocomplete from `allTags`)
- Small visual indicator if stock has tags (dot or checkmark)

**New component:**
- `apps/dsa-web/src/components/stocks/StockTagEditor.tsx` - Reusable tag editor

## Files to Create

| File | Purpose |
|------|---------|
| `src/repositories/stock_tag_repo.py` | Repository layer |
| `src/services/stock_tag_service.py` | Business logic |
| `apps/dsa-web/src/api/tags.ts` | Frontend API |
| `apps/dsa-web/src/stores/tagsStore.ts` | State management |
| `apps/dsa-web/src/components/stocks/StockTagEditor.tsx` | Tag editor component |

## Files to Modify

| File | Change |
|------|--------|
| `src/storage.py` | Add `StockTag` model |
| `src/webui_frontend.py` | Add tag API endpoints |
| `apps/dsa-web/src/components/groups/GroupCard.tsx` | Integrate tag editor |
| `apps/dsa-web/src/api/index.ts` | Export tags API |

## Database Migration

Automatic via SQLAlchemy `create_all` (existing pattern in this project).
