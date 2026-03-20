# Stock Profile Groups Feature Design

**Date:** 2026-03-07
**Status:** Approved
**Author:** Claude Code

## Overview

Add the ability to organize selected stocks into custom groups within a single admin user profile. This replaces the current flat `STOCK_LIST` environment variable with a database-driven group management system while maintaining backward compatibility.

## Requirements

### Functional Requirements

1. Admin user can create custom stock groups with names (e.g., "科技成长", "价值投资")
2. Admin user can add/remove stocks to/from groups
3. Admin user can manage groups via Web UI and API
4. Analysis reports show stocks grouped by these custom groups
5. Backward compatible with existing `STOCK_LIST` environment variable

### Non-Functional Requirements

1. Database-first storage in SQLite
2. RESTful API endpoints for group management
3. Intuitive Web UI with drag-and-drop reordering
4. Zero-downtime migration from existing system

## Architecture

### Data Model

**Table: `stock_groups`**

```sql
CREATE TABLE stock_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    stock_codes TEXT NOT NULL,           -- JSON array: ["600519", "300750"]
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_stock_groups_name ON stock_groups(name);
```

**Rationale:**
- `stock_codes` as JSON array provides flexibility without needing a separate junction table
- `sort_order` enables UI reordering
- `name` unique constraint prevents duplicate groups
- Minimal schema allows future extensions (color, icon, etc.)

### API Design

**Base Path:** `/api/v1/groups`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List all groups |
| POST | `/` | Create new group |
| PUT | `/{id}` | Update group |
| DELETE | `/{id}` | Delete group |
| POST | `/batch-reorder` | Reorder multiple groups |
| GET | `/{id}/stocks` | Get group's stock details with quotes |

**Request/Response Schemas:**

```python
# GroupCreate
{
    "name": str,              # Required, unique
    "description": str | None,
    "stock_codes": list[str]  # Required
}

# GroupUpdate
{
    "name": str | None,
    "description": str | None,
    "stock_codes": list[str] | None,
    "sort_order": int | None
}

# GroupResponse
{
    "id": int,
    "name": str,
    "description": str | None,
    "stock_codes": list[str],
    "sort_order": int,
    "created_at": str,
    "updated_at": str
}
```

**Authentication:**
- All endpoints protected by existing auth middleware (if `ADMIN_AUTH_ENABLED=true`)
- Same session-based authentication as other admin endpoints

### Analysis Pipeline Integration

**Current Flow:**
```
STOCK_LIST env var → parse → analyze each stock → send notification
```

**New Flow:**
```
┌─────────────────────────────────────────┐
│ 1. get_all_stock_codes()                 │
│    - Try DB groups first                 │
│    - Fallback to STOCK_LIST if empty    │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ 2. For each group:                       │
│    - Get stocks in group                 │
│    - Run analysis                        │
│    - Add group-level metadata            │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ 3. Send notification                     │
│    - Grouped format if groups exist      │
│    - Flat format if no groups            │
└─────────────────────────────────────────┘
```

**Report Format (Grouped):**
```
🎯 2026-03-07 决策仪表盘
共分析8只股票 | 分组: 3

📦 科技成长 (3只)
⚪ 腾讯控股(00700): 观望 | 评分 72
...

📦 价值投资 (3只)
🟢 茅台(600519): 买入 | 评分 85
...

📦 短线观察 (2只)
🟡 永鼎股份(600105): 观望 | 评分 48
...
```

### Web UI Design

**Page:** `/groups` (standalone page, accessible from navigation)

**Layout:**
```
┌────────────────────────────────────────────┐
│ 自选股分组                    [+ 新建分组]  │
├────────────────────────────────────────────┤
│ ┌────────────────────────────────────────┐ │
│ │ 📦 科技成长                     [编辑]  │ │
│ │ 高增长科技股                            │ │
│ │ 3只股票                                 │ │
│ │ [腾讯] [阿里] [美团]                    │ │
│ └────────────────────────────────────────┘ │
│                                            │
│ ┌────────────────────────────────────────┐ │
│ │ 📦 价值投资                     [编辑]  │ │
│ │ 长期持有价值股                          │ │
│ │ 2只股票                                 │ │
│ │ [茅台] [平安]                           │ │
│ └────────────────────────────────────────┘ │
└────────────────────────────────────────────┘
```

**Create/Edit Modal:**
```
┌─────────────────────────────────────┐
│ 新建分组                      [×]   │
├─────────────────────────────────────┤
│ 分组名称: [_____________________]   │
│ 描述(可选): [__________________]   │
│                                     │
│ 股票代码:                           │
│ ┌─────────────────────────────────┐ │
│ │ 600519 [×]  300750 [×]          │ │
│ │ 00700  [×]  AAPL    [×]         │ │
│ │ [输入股票代码添加...]            │ │
│ └─────────────────────────────────┘ │
│                                     │
│        [取消]         [保存]        │
└─────────────────────────────────────┘
```

**Features:**
- Drag-and-drop to reorder groups
- Stock code input with auto-complete and name preview
- Inline validation (duplicate codes, invalid codes)
- Responsive design for mobile devices

## Backward Compatibility

### Environment Variable Support

**Priority Order:**
1. Database groups (if not empty)
2. `STOCK_LIST` environment variable (fallback)

**Code Example:**
```python
def get_all_stock_codes() -> list[str]:
    """Get stock codes from DB groups or env var."""
    # Try database first
    groups = StockGroupService().get_all_groups()
    if groups:
        codes = []
        for group in groups:
            codes.extend(group.stock_codes)
        return list(dict.fromkeys(codes))  # Remove duplicates, preserve order

    # Fallback to environment variable
    stock_list = os.getenv("STOCK_LIST", "")
    return [c.strip() for c in stock_list.split(",") if c.strip()]
```

**New Environment Variable:**
- `STOCK_GROUPS_ENABLED=true` (default: true) - Toggle the feature on/off

### Migration Strategy

1. **Database Migration:**
   - Automatic table creation on first run with new version
   - No manual intervention required

2. **Optional Migration Command:**
   ```bash
   python main.py --migrate-stock-list
   ```
   - Reads `STOCK_LIST` env var
   - Creates a default group named "默认分组" containing all stocks
   - Useful for users who want to migrate existing setup

3. **Notification Format:**
   - Detects if groups exist in database
   - If groups: use grouped format
   - If no groups: use flat list format (same as current)

## Implementation Plan

### Phase 1: Backend (Estimated: 4-6 hours)

1. **Database Layer** (`src/models/stock_group.py`, `src/services/stock_group_service.py`)
   - Create SQLAlchemy model
   - Implement CRUD operations
   - Add migration script

2. **API Layer** (`api/v1/endpoints/groups.py`, `api/v1/schemas/groups.py`)
   - Implement REST endpoints
   - Add request/response schemas
   - Update router

3. **Analysis Integration** (`src/services/stock_service.py`, `src/core/pipeline.py`)
   - Add `get_all_stock_codes()` function
   - Update analysis pipeline to support grouped output
   - Update notification formatters

### Phase 2: Frontend (Estimated: 6-8 hours)

1. **Components** (`apps/dsa-web/src/components/`)
   - GroupList component
   - GroupCard component
   - CreateEditGroupModal component
   - StockCodeInput component

2. **Pages** (`apps/dsa-web/src/pages/`)
   - GroupsPage component
   - Add route to router

3. **API Integration** (`apps/dsa-web/src/api/`)
   - Add groups API client
   - Add state management (React Query or Context)

### Phase 3: Testing & Documentation (Estimated: 2-3 hours)

1. **Testing**
   - Unit tests for services
   - API integration tests
   - Frontend component tests

2. **Documentation**
   - Update README.md
   - Update full-guide.md
   - Add API documentation

## Testing Strategy

### Unit Tests

```python
# tests/services/test_stock_group_service.py
def test_create_group():
    service = StockGroupService()
    group = service.create_group(
        name="科技成长",
        stock_codes=["00700", "09988"]
    )
    assert group.id is not None
    assert group.name == "科技成长"

def test_get_all_stock_codes_fallback():
    # When DB is empty, should return STOCK_LIST env var
    os.environ["STOCK_LIST"] = "600519,300750"
    codes = get_all_stock_codes()
    assert codes == ["600519", "300750"]
```

### Integration Tests

```python
# tests/api/test_groups.py
def test_create_group_api(client):
    response = client.post("/api/v1/groups", json={
        "name": "测试分组",
        "stock_codes": ["600519"]
    })
    assert response.status_code == 200
    assert response.json()["name"] == "测试分组"
```

### Manual Testing Checklist

- [ ] Create group via UI
- [ ] Edit group (add/remove stocks)
- [ ] Delete group
- [ ] Reorder groups via drag-and-drop
- [ ] Run analysis with groups enabled
- [ ] Run analysis with no groups (fallback to env var)
- [ ] Verify grouped report format
- [ ] Test migration command

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing STOCK_LIST workflow | High | Keep fallback support, make migration optional |
| Database migration failures | Medium | Add rollback script, test on clean DB |
| Performance with many groups | Low | Add pagination to API if needed |
| UI complexity | Medium | Keep design simple, follow existing patterns |

## Future Enhancements

1. **Group Colors/Icons** - Allow custom colors and icons for groups
2. **Group-level Alerts** - Different notification settings per group
3. **Group Sharing** - Export/import groups as JSON
4. **Smart Groups** - Auto-group by sector, market cap, etc.
5. **Group Analytics** - Performance metrics per group

## Conclusion

This design provides a clean, database-driven approach to stock group management while maintaining full backward compatibility. The implementation is divided into clear phases with minimal risk to existing functionality.
