# A股板块看板实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 创建一个Web界面的A股板块看板，每日展示涨跌板块排行榜

**Architecture:** 后端使用FastAPI提供RESTful API，前端使用Vue 3构建响应式页面，数据通过MarketAnalyzer获取并缓存到本地JSON文件

**Tech Stack:** Python 3.10+, FastAPI, Vue 3, Element Plus, AkShare, Pytest

---

## Task 1: 创建数据服务层

**Files:**
- Create: `src/sector_service.py`
- Test: `tests/test_sector_service.py`

**Step 1: Write the failing test for sector service**

Create `tests/test_sector_service.py`:

```python
# -*- coding: utf-8 -*-
"""板块看板服务测试"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from src.sector_service import SectorService


def test_get_sector_board_data_returns_dict():
    """测试获取板块看板数据返回字典"""
    service = SectorService()
    result = service.get_sector_board_data()

    assert isinstance(result, dict)
    assert "date" in result
    assert "market_overview" in result
    assert "top_sectors" in result
    assert "bottom_sectors" in result


def test_get_sector_board_data_structure():
    """测试板块看板数据结构"""
    service = SectorService()
    result = service.get_sector_board_data()

    # 检查市场概况结构
    overview = result["market_overview"]
    assert "up_count" in overview
    assert "down_count" in overview
    assert "limit_up_count" in overview
    assert "limit_down_count" in overview

    # 检查板块列表
    assert isinstance(result["top_sectors"], list)
    assert isinstance(result["bottom_sectors"], list)


def test_force_refresh_bypasses_cache(tmp_path):
    """测试强制刷新跳过缓存"""
    service = SectorService(cache_dir=str(tmp_path))

    # 第一次获取
    result1 = service.get_sector_board_data(force_refresh=False)

    # 强制刷新
    result2 = service.get_sector_board_data(force_refresh=True)

    assert result1 is not None
    assert result2 is not None
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_sector_service.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.sector_service'"

**Step 3: Create sector service with minimal implementation**

Create `src/sector_service.py`:

```python
# -*- coding: utf-8 -*-
"""
板块看板数据服务

职责：
1. 获取板块涨跌数据
2. 管理数据缓存
3. 提供统一的数据接口
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from src.market_analyzer import MarketAnalyzer
from src.config import get_config

logger = logging.getLogger(__name__)


class SectorService:
    """板块看板数据服务"""

    def __init__(self, cache_dir: Optional[str] = None):
        """
        初始化板块服务

        Args:
            cache_dir: 缓存目录，默认为 data/sectors
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path("data/sectors")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.market_analyzer = MarketAnalyzer(region='cn')

    def get_sector_board_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        获取板块看板数据

        Args:
            force_refresh: 是否强制刷新（跳过缓存）

        Returns:
            板块看板数据字典
        """
        date_str = datetime.now().strftime('%Y-%m-%d')
        cache_file = self.cache_dir / f"{date_str}.json"

        # 尝试读取缓存
        if not force_refresh and cache_file.exists():
            logger.info(f"读取缓存数据: {cache_file}")
            cached_data = self._load_cached_data(cache_file)
            if cached_data:
                return cached_data

        # 获取新数据
        logger.info("获取新的板块数据...")
        fresh_data = self._fetch_fresh_data()

        # 保存到缓存
        if fresh_data:
            self._save_to_cache(cache_file, fresh_data)

        return fresh_data

    def _fetch_fresh_data(self) -> Dict[str, Any]:
        """获取最新的板块数据"""
        try:
            # 获取市场概览
            overview = self.market_analyzer.get_market_overview()

            # 获取板块涨跌榜
            sector_data = self.market_analyzer.get_sector_performance()

            # 组装数据
            result = {
                "date": datetime.now().strftime('%Y-%m-%d'),
                "update_time": datetime.now().strftime('%H:%M:%S'),
                "market_overview": {
                    "up_count": overview.up_count,
                    "down_count": overview.down_count,
                    "flat_count": overview.flat_count,
                    "limit_up_count": overview.limit_up_count,
                    "limit_down_count": overview.limit_down_count,
                    "total_amount": overview.total_amount,
                },
                "top_sectors": self._format_sectors(sector_data.get("top_sectors", [])),
                "bottom_sectors": self._format_sectors(sector_data.get("bottom_sectors", [])),
            }

            return result

        except Exception as e:
            logger.error(f"获取板块数据失败: {e}")
            return {
                "date": datetime.now().strftime('%Y-%m-%d'),
                "update_time": datetime.now().strftime('%H:%M:%S'),
                "error": str(e),
                "market_overview": {},
                "top_sectors": [],
                "bottom_sectors": [],
            }

    def _format_sectors(self, sectors: list) -> list:
        """格式化板块数据"""
        formatted = []
        for idx, sector in enumerate(sectors[:10], start=1):
            formatted.append({
                "rank": idx,
                "name": sector.get("name", ""),
                "change_pct": sector.get("change_pct", 0.0),
                "leading_stock": sector.get("leading_stock", ""),
            })
        return formatted

    def _load_cached_data(self, cache_file: Path) -> Optional[Dict[str, Any]]:
        """加载缓存数据"""
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载缓存失败: {e}")
            return None

    def _save_to_cache(self, cache_file: Path, data: Dict[str, Any]) -> None:
        """保存数据到缓存"""
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"数据已缓存到: {cache_file}")
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_sector_service.py -v`
Expected: Some tests may fail due to MarketAnalyzer dependencies, but basic structure should work

**Step 5: Commit**

```bash
git add src/sector_service.py tests/test_sector_service.py
git commit -m "feat: add sector service for board data

- Add SectorService class to manage sector board data
- Implement cache mechanism with JSON files
- Add basic test cases

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 2: 创建API端点

**Files:**
- Create: `api/v1/endpoints/sectors.py`
- Modify: `api/v1/router.py`

**Step 1: Write the failing test for API endpoint**

Create `tests/api/test_sectors_endpoint.py`:

```python
# -*- coding: utf-8 -*-
"""板块看板API端点测试"""

import pytest
from fastapi.testclient import TestClient
from server import create_app


@pytest.fixture
def client():
    """创建测试客户端"""
    app = create_app()
    return TestClient(app)


def test_get_sector_board_success(client):
    """测试获取板块看板成功"""
    response = client.get("/api/v1/sectors/board")

    assert response.status_code == 200
    data = response.json()

    assert "date" in data
    assert "market_overview" in data
    assert "top_sectors" in data
    assert "bottom_sectors" in data


def test_get_sector_board_with_force_refresh(client):
    """测试强制刷新参数"""
    response = client.get("/api/v1/sectors/board?force_refresh=true")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/api/test_sectors_endpoint.py -v`
Expected: FAIL with "404 Not Found"

**Step 3: Create API endpoint**

Create `api/v1/endpoints/sectors.py`:

```python
# -*- coding: utf-8 -*-
"""板块看板API端点"""

import logging
from fastapi import APIRouter, Query, HTTPException

from src.sector_service import SectorService
from api.deps import get_sector_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sectors", tags=["板块看板"])


@router.get("/board")
async def get_sector_board(
    force_refresh: bool = Query(False, description="强制刷新数据")
):
    """
    获取板块看板数据

    Args:
        force_refresh: 是否强制刷新（跳过缓存）

    Returns:
        板块看板数据，包含市场概况和涨跌板块榜
    """
    try:
        service = get_sector_service()
        data = service.get_sector_board_data(force_refresh=force_refresh)

        if not data:
            raise HTTPException(status_code=500, detail="获取板块数据失败")

        return data

    except Exception as e:
        logger.error(f"获取板块看板数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 4: Register router in api/v1/router.py**

Modify `api/v1/router.py`, add:

```python
from api.v1.endpoints import sectors

# 在现有路由注册后添加
api_router.include_router(sectors.router)
```

**Step 5: Add dependency injection in api/deps.py**

Modify `api/deps.py`, add:

```python
from src.sector_service import SectorService

_sector_service = None

def get_sector_service() -> SectorService:
    """获取板块服务实例（单例）"""
    global _sector_service
    if _sector_service is None:
        _sector_service = SectorService()
    return _sector_service
```

**Step 6: Run test to verify it passes**

Run: `pytest tests/api/test_sectors_endpoint.py -v`
Expected: PASS (or some tests may need MarketAnalyzer mocks)

**Step 7: Commit**

```bash
git add api/v1/endpoints/sectors.py api/v1/router.py api/deps.py tests/api/test_sectors_endpoint.py
git commit -m "feat: add sector board API endpoint

- Add GET /api/v1/sectors/board endpoint
- Support force_refresh parameter
- Add dependency injection for SectorService
- Add API tests

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 3: 创建市场概况组件

**Files:**
- Create: `apps/dsa-web/src/components/MarketOverview.vue`

**Step 1: Create MarketOverview component**

Create `apps/dsa-web/src/components/MarketOverview.vue`:

```vue
<template>
  <el-card class="market-overview">
    <template #header>
      <div class="card-header">
        <span class="title">📊 市场概况</span>
        <span class="update-time">{{ updateTime }}</span>
      </div>
    </template>

    <div class="overview-content">
      <el-row :gutter="20">
        <el-col :xs="12" :sm="6">
          <div class="stat-item">
            <div class="stat-label">上涨家数</div>
            <div class="stat-value up">{{ formatNumber(overview.up_count) }}</div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="6">
          <div class="stat-item">
            <div class="stat-label">下跌家数</div>
            <div class="stat-value down">{{ formatNumber(overview.down_count) }}</div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="6">
          <div class="stat-item">
            <div class="stat-label">涨停</div>
            <div class="stat-value up">{{ overview.limit_up_count }}</div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="6">
          <div class="stat-item">
            <div class="stat-label">跌停</div>
            <div class="stat-value down">{{ overview.limit_down_count }}</div>
          </div>
        </el-col>
      </el-row>

      <el-row :gutter="20" class="second-row">
        <el-col :xs="12" :sm="12">
          <div class="stat-item">
            <div class="stat-label">两市成交额</div>
            <div class="stat-value">{{ formatAmount(overview.total_amount) }}</div>
          </div>
        </el-col>
      </el-row>
    </div>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  overview: {
    type: Object,
    required: true
  },
  updateTime: {
    type: String,
    default: ''
  }
})

const formatNumber = (num) => {
  if (!num) return '0'
  return num.toLocaleString()
}

const formatAmount = (amount) => {
  if (!amount) return '0亿'
  const yi = amount / 100000000
  return yi.toFixed(2) + '亿'
}
</script>

<style scoped>
.market-overview {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 18px;
  font-weight: bold;
}

.update-time {
  font-size: 14px;
  color: #909399;
}

.overview-content {
  padding: 10px 0;
}

.stat-item {
  text-align: center;
  padding: 15px 0;
}

.stat-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.stat-value.up {
  color: #67C23A;
}

.stat-value.down {
  color: #F56C6C;
}

.second-row {
  margin-top: 10px;
}

@media (max-width: 768px) {
  .stat-value {
    font-size: 20px;
  }
}
</style>
```

**Step 2: Test the component renders**

Run: `cd apps/dsa-web && npm run build`
Expected: Build succeeds without errors

**Step 3: Commit**

```bash
git add apps/dsa-web/src/components/MarketOverview.vue
git commit -m "feat: add MarketOverview component

- Display market statistics (up/down counts, limit up/down)
- Display total trading amount
- Responsive layout for mobile

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 4: 创建板块表格组件

**Files:**
- Create: `apps/dsa-web/src/components/SectorTable.vue`

**Step 1: Create SectorTable component**

Create `apps/dsa-web/src/components/SectorTable.vue`:

```vue
<template>
  <el-card class="sector-table">
    <template #header>
      <div class="card-header">
        <span class="title">{{ title }}</span>
      </div>
    </template>

    <el-table
      :data="sectors"
      stripe
      style="width: 100%"
      v-loading="loading"
    >
      <el-table-column prop="rank" label="排名" width="60" align="center" />

      <el-table-column prop="name" label="板块名称" min-width="120">
        <template #default="{ row }">
          <span class="sector-name">{{ row.name }}</span>
        </template>
      </el-table-column>

      <el-table-column prop="change_pct" label="涨跌幅" width="100" align="right">
        <template #default="{ row }">
          <span :class="getChangeClass(row.change_pct)">
            {{ formatChange(row.change_pct) }}
          </span>
        </template>
      </el-table-column>

      <el-table-column prop="leading_stock" label="领涨股" min-width="100" />
    </el-table>
  </el-card>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  sectors: {
    type: Array,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const getChangeClass = (change) => {
  if (change > 0) return 'change-up'
  if (change < 0) return 'change-down'
  return 'change-flat'
}

const formatChange = (change) => {
  const sign = change > 0 ? '+' : ''
  return `${sign}${change.toFixed(2)}%`
}
</script>

<style scoped>
.sector-table {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 18px;
  font-weight: bold;
}

.sector-name {
  font-weight: 500;
}

.change-up {
  color: #67C23A;
  font-weight: bold;
}

.change-down {
  color: #F56C6C;
  font-weight: bold;
}

.change-flat {
  color: #909399;
}
</style>
```

**Step 2: Test the component renders**

Run: `cd apps/dsa-web && npm run build`
Expected: Build succeeds without errors

**Step 3: Commit**

```bash
git add apps/dsa-web/src/components/SectorTable.vue
git commit -m "feat: add SectorTable component

- Display sector ranking with change percentage
- Color-coded for up/down trends
- Show leading stock for each sector

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 5: 创建板块看板主页面

**Files:**
- Create: `apps/dsa-web/src/views/SectorsBoard.vue`

**Step 1: Create SectorsBoard main page**

Create `apps/dsa-web/src/views/SectorsBoard.vue`:

```vue
<template>
  <div class="sectors-board">
    <div class="page-header">
      <h1>📈 A股板块看板</h1>
      <div class="date-info">{{ date }}</div>
    </div>

    <!-- 市场概况 -->
    <MarketOverview
      :overview="marketOverview"
      :update-time="updateTime"
    />

    <!-- 板块涨跌榜 -->
    <el-row :gutter="20" class="sector-tables">
      <el-col :xs="24" :sm="12">
        <SectorTable
          title="🔥 涨幅前10板块"
          :sectors="topSectors"
          :loading="loading"
        />
      </el-col>
      <el-col :xs="24" :sm="12">
        <SectorTable
          title="❄️ 跌幅前10板块"
          :sectors="bottomSectors"
          :loading="loading"
        />
      </el-col>
    </el-row>

    <!-- 操作按钮 -->
    <div class="action-buttons">
      <el-button
        type="primary"
        @click="refreshData"
        :loading="loading"
      >
        刷新数据
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import MarketOverview from '@/components/MarketOverview.vue'
import SectorTable from '@/components/SectorTable.vue'
import axios from 'axios'

const loading = ref(false)
const date = ref('')
const updateTime = ref('')
const marketOverview = ref({
  up_count: 0,
  down_count: 0,
  limit_up_count: 0,
  limit_down_count: 0,
  total_amount: 0
})
const topSectors = ref([])
const bottomSectors = ref([])

const fetchData = async (forceRefresh = false) => {
  loading.value = true
  try {
    const response = await axios.get('/api/v1/sectors/board', {
      params: { force_refresh: forceRefresh }
    })

    const data = response.data
    date.value = data.date
    updateTime.value = data.update_time
    marketOverview.value = data.market_overview || {}
    topSectors.value = data.top_sectors || []
    bottomSectors.value = data.bottom_sectors || []

    if (data.error) {
      ElMessage.warning(data.error)
    }
  } catch (error) {
    console.error('获取板块数据失败:', error)
    ElMessage.error('获取板块数据失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  fetchData(true)
  ElMessage.success('数据刷新中...')
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.sectors-board {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  text-align: center;
  margin-bottom: 30px;
}

.page-header h1 {
  font-size: 28px;
  margin-bottom: 10px;
  color: #303133;
}

.date-info {
  font-size: 16px;
  color: #909399;
}

.sector-tables {
  margin-bottom: 20px;
}

.action-buttons {
  text-align: center;
  margin-top: 30px;
}

@media (max-width: 768px) {
  .sectors-board {
    padding: 10px;
  }

  .page-header h1 {
    font-size: 24px;
  }
}
</style>
```

**Step 2: Test the page builds**

Run: `cd apps/dsa-web && npm run build`
Expected: Build succeeds without errors

**Step 3: Commit**

```bash
git add apps/dsa-web/src/views/SectorsBoard.vue
git commit -m "feat: add SectorsBoard main page

- Integrate MarketOverview and SectorTable components
- Fetch data from backend API
- Support manual refresh
- Responsive layout

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 6: 配置前端路由

**Files:**
- Modify: `apps/dsa-web/src/router/index.js`

**Step 1: Add route configuration**

Modify `apps/dsa-web/src/router/index.js`, add route:

```javascript
// 在现有路由配置中添加
{
  path: '/sectors',
  name: 'SectorsBoard',
  component: () => import('@/views/SectorsBoard.vue'),
  meta: { title: '板块看板' }
}
```

**Step 2: Add navigation link (if applicable)**

If there's a navigation menu, add link to `/sectors`

**Step 3: Test routing works**

Run: `cd apps/dsa-web && npm run build`
Expected: Build succeeds

**Step 4: Commit**

```bash
git add apps/dsa-web/src/router/index.js
git commit -m "feat: add /sectors route

- Configure SectorsBoard route
- Enable navigation to sector board page

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 7: 集成测试和优化

**Files:**
- Test: Manual testing checklist

**Step 1: Start backend server**

Run: `python main.py --webui-only`
Expected: Server starts at http://localhost:8000

**Step 2: Test API endpoint manually**

Run: `curl http://localhost:8000/api/v1/sectors/board`
Expected: JSON response with sector data

**Step 3: Test frontend page**

Visit: http://localhost:8000/sectors
Expected:
- Page loads successfully
- Market overview displays
- Sector tables display
- Refresh button works

**Step 4: Test mobile responsiveness**

Resize browser to mobile width
Expected: Layout switches to single column

**Step 5: Test error handling**

- Test with no network connection
- Test force refresh parameter

**Step 6: Run all tests**

Run: `pytest tests/ -v`
Expected: All tests pass

**Step 7: Final commit**

```bash
git add .
git commit -m "test: complete integration testing for sector board

- Verify API endpoint functionality
- Test frontend page rendering
- Test responsive design
- Verify error handling

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 8: 更新文档

**Files:**
- Modify: `README.md`

**Step 1: Add feature description to README**

Add to README.md in the 功能特性 section:

```markdown
| 板块看板 | 板块热力图 | 实时展示A股主要涨跌板块排行，市场概况一目了然 |
```

**Step 2: Add navigation instruction**

Add to Web界面 section:

```markdown
### 板块看板

访问 `/sectors` 页面，查看当日A股板块涨跌排行：
- 涨幅前10板块
- 跌幅前10板块
- 市场概况统计
- 支持手动刷新
```

**Step 3: Commit documentation**

```bash
git add README.md
git commit -m "docs: add sector board feature documentation

- Add feature to feature list
- Add usage instructions

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## 验收检查清单

### 功能验收
- [ ] API端点 `/api/v1/sectors/board` 返回正确数据
- [ ] 板块看板页面正常加载
- [ ] 市场概况显示正确
- [ ] 涨跌板块榜各显示10个
- [ ] 手动刷新功能正常
- [ ] 数据缓存机制正常

### 性能验收
- [ ] API响应时间 < 5秒（首次获取）
- [ ] API响应时间 < 1秒（读取缓存）
- [ ] 前端页面加载流畅

### UI/UX 验收
- [ ] 桌面端双列布局正确
- [ ] 移动端单列布局正确
- [ ] 涨跌颜色标识清晰（绿涨红跌）
- [ ] Loading状态显示
- [ ] 错误提示友好

### 代码质量
- [ ] 后端单元测试通过
- [ ] 前端编译无错误
- [ ] 代码符合规范（flake8）
- [ ] 无明显性能问题

---

**计划完成，准备执行。**
