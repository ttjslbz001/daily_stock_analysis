# A股板块看板设计文档

> 创建日期：2026-03-14
> 设计者：Claude Code
> 状态：待实现

## 1. 概述

### 1.1 项目目标
创建一个独立的Web界面板块看板，每日总结A股最主要的涨跌板块，为用户提供直观的板块热点展示。

### 1.2 核心价值
- 快速了解当日市场板块轮动情况
- 识别强势板块和弱势板块
- 为投资决策提供参考

### 1.3 适用场景
- 日常市场回顾
- 板块轮动研究
- 热点题材跟踪

## 2. 功能需求

### 2.1 页面布局

#### 顶部 - 市场概况卡片
- 当日日期 + 数据更新时间
- 上涨/下跌/平盘家数统计
- 涨停/跌停家数统计
- 两市成交额

#### 左侧 - 涨幅榜卡片
- 标题：🔥 涨幅前10板块
- 列表字段：
  - 排名
  - 板块名称
  - 涨跌幅（绿色标识）
  - 领涨股

#### 右侧 - 跌幅榜卡片
- 标题：❄️ 跌幅前10板块
- 列表字段：
  - 排名
  - 板块名称
  - 涨跌幅（红色标识）
  - 领跌股

#### 底部 - 快捷操作
- 手动刷新按钮（强制获取最新数据）
- 查看大盘复盘按钮（跳转到复盘页面）

### 2.2 数据更新策略
- **缓存策略**：每日首次访问时获取数据，当日重复访问读取缓存
- **数据存储**：`data/sectors/YYYY-MM-DD.json`
- **强制刷新**：用户可手动触发刷新

### 2.3 响应式设计
- **桌面端**：双列布局（左侧涨幅榜，右侧跌幅榜）
- **移动端**：单列布局（上下排列）

## 3. 技术设计

### 3.1 后端架构

#### API 端点
- **文件**：`api/v1/endpoints/sectors.py`（新建）
- **路由**：`GET /api/v1/sectors/board`
- **参数**：
  - `force_refresh` (boolean, optional): 强制刷新数据，默认 false
- **响应格式**：
```json
{
  "date": "2026-03-14",
  "update_time": "15:30:00",
  "market_overview": {
    "up_count": 2847,
    "down_count": 1765,
    "flat_count": 156,
    "limit_up_count": 85,
    "limit_down_count": 12,
    "total_amount": 875600000000
  },
  "top_sectors": [
    {
      "rank": 1,
      "name": "互联网服务",
      "change_pct": 5.23,
      "leading_stock": "XX科技"
    }
  ],
  "bottom_sectors": [
    {
      "rank": 1,
      "name": "保险",
      "change_pct": -2.15,
      "leading_stock": "XX保险"
    }
  ]
}
```

#### 数据服务层
- **文件**：`src/sector_service.py`（新建）
- **职责**：
  1. 调用 `MarketAnalyzer` 获取板块数据
  2. 管理数据缓存（存储和读取）
  3. 检查缓存有效性（日期校验）
- **主要方法**：
  - `get_sector_board_data(force_refresh: bool) -> dict`
  - `_fetch_fresh_data() -> dict`
  - `_load_cached_data(date: str) -> Optional[dict]`
  - `_save_to_cache(date: str, data: dict)`

#### 数据源
- 复用现有 `MarketAnalyzer` 的 `get_sector_performance()` 方法
- 底层使用 `AkShareFetcher` 的板块接口

### 3.2 前端架构

#### 页面组件
- **文件**：`apps/dsa-web/src/views/SectorsBoard.vue`（新建）
- **路由**：`/sectors`
- **子组件**：
  1. `MarketOverview.vue` - 市场概况卡片
  2. `SectorTable.vue` - 板块列表表格（支持涨/跌切换）
  3. `RefreshButton.vue` - 刷新按钮组件

#### 技术栈
- Vue 3 Composition API
- Element Plus UI 组件库
- Axios 用于 API 调用

#### 状态管理
- 使用 Vue 3 reactive 管理组件状态
- 不引入全局状态管理（保持简单）

#### 样式规范
- 配色方案：
  - 涨：绿色（`#67C23A`）
  - 跌：红色（`#F56C6C`）
  - 背景色：白色/浅灰
- 响应式断点：
  - 桌面端：≥768px
  - 移动端：<768px

### 3.3 数据流程

```
用户访问 /sectors
    ↓
前端调用 GET /api/v1/sectors/board
    ↓
SectorService.get_sector_board_data()
    ↓
检查今日缓存是否存在？
    ├─ 是 → 读取 data/sectors/2026-03-14.json
    └─ 否 → MarketAnalyzer.get_sector_performance()
              ↓
          获取板块数据（AkShare）
              ↓
          保存到 data/sectors/2026-03-14.json
              ↓
          返回数据
    ↓
返回JSON给前端
    ↓
前端渲染板块看板
```

### 3.4 错误处理

#### 后端错误处理
1. **非交易日**：
   - 检测：调用 `TradingCalendar.is_trading_day()`
   - 处理：返回最近交易日数据 + 提示信息
   - 响应：
   ```json
   {
     "error": null,
     "message": "今日非交易日，显示最近交易日数据",
     "date": "2026-03-13"
   }
   ```

2. **数据获取失败**：
   - 检测：try-catch 捕获异常
   - 处理：返回错误信息
   - 响应：
   ```json
   {
     "error": "数据获取失败，请稍后重试",
     "data": null
   }
   ```

3. **网络超时**：
   - 超时时间：30秒
   - 处理：返回超时错误

#### 前端错误处理
1. **加载状态**：
   - 显示 loading 动画
   - 禁用刷新按钮

2. **错误提示**：
   - 使用 Element Plus ElMessage 显示错误
   - 提供"重试"按钮

3. **空数据处理**：
   - 显示"暂无数据"提示
   - 提供刷新按钮

## 4. 实现计划

### 4.1 开发阶段

#### 阶段1：后端API开发（预计2-3小时）
- [ ] 创建 `src/sector_service.py`
- [ ] 实现数据获取和缓存逻辑
- [ ] 创建 `api/v1/endpoints/sectors.py`
- [ ] 实现 GET `/api/v1/sectors/board` 端点
- [ ] 添加单元测试

#### 阶段2：前端页面开发（预计3-4小时）
- [ ] 创建 `SectorsBoard.vue` 主页面
- [ ] 创建 `MarketOverview.vue` 组件
- [ ] 创建 `SectorTable.vue` 组件
- [ ] 创建 `RefreshButton.vue` 组件
- [ ] 配置路由 `/sectors`
- [ ] 实现响应式布局

#### 阶段3：集成测试（预计1-2小时）
- [ ] 前后端联调
- [ ] 测试数据缓存机制
- [ ] 测试错误处理场景
- [ ] 移动端适配测试

#### 阶段4：优化和文档（预计1小时）
- [ ] 性能优化
- [ ] 代码review
- [ ] 更新用户文档
- [ ] 更新开发文档

### 4.2 依赖关系
```
阶段1（后端）
    ↓
阶段2（前端）
    ↓
阶段3（测试）
    ↓
阶段4（优化）
```

## 5. 文件清单

### 5.1 新建文件
```
api/v1/endpoints/sectors.py          # API端点
src/sector_service.py                # 数据服务
apps/dsa-web/src/views/SectorsBoard.vue          # 主页面
apps/dsa-web/src/components/MarketOverview.vue   # 市场概况组件
apps/dsa-web/src/components/SectorTable.vue      # 板块表格组件
apps/dsa-web/src/components/RefreshButton.vue    # 刷新按钮组件
tests/test_sector_service.py         # 单元测试
```

### 5.2 修改文件
```
api/v1/router.py                     # 添加路由注册
apps/dsa-web/src/router/index.js     # 添加前端路由
README.md                            # 添加功能说明
```

## 6. 验收标准

### 6.1 功能验收
- [ ] 能够正确展示当日涨幅前10板块
- [ ] 能够正确展示当日跌幅前10板块
- [ ] 市场概况数据准确（上涨/下跌/涨停/跌停/成交额）
- [ ] 缓存机制正常工作
- [ ] 手动刷新功能正常
- [ ] 非交易日处理正确

### 6.2 性能验收
- [ ] API响应时间 < 2秒（读取缓存时）
- [ ] API响应时间 < 5秒（获取新数据时）
- [ ] 前端首屏加载时间 < 1秒

### 6.3 UI/UX 验收
- [ ] 桌面端双列布局正常
- [ ] 移动端单列布局正常
- [ ] 涨跌颜色标识清晰（绿涨红跌）
- [ ] 错误提示友好
- [ ] 加载状态清晰

### 6.4 代码质量
- [ ] 后端代码有单元测试
- [ ] 代码符合项目规范（flake8）
- [ ] 无明显的性能问题
- [ ] 错误处理完善

## 7. 后续优化方向

### 7.1 短期优化（1-2周内）
- 添加板块历史走势图（最近5日）
- 板块详情页面（点击板块查看成分股）
- 板块资金流向分析

### 7.2 中期优化（1个月内）
- 板块轮动分析（AI分析）
- 热点题材挖掘
- 板块关联度分析

### 7.3 长期优化（3个月内）
- 自选板块功能
- 板块预警功能
- 板块对比分析

## 8. 风险和限制

### 8.1 技术风险
- **数据源限制**：AkShare 板块接口可能有限流或不可用风险
  - 缓解措施：添加降级方案，尝试其他数据源
- **性能风险**：实时获取板块数据可能较慢
  - 缓解措施：使用缓存机制，优化数据获取逻辑

### 8.2 功能限制
- 当前版本仅支持A股市场
- 不包含板块成分股详情
- 不包含历史数据对比
- 不包含AI分析功能

## 9. 参考资料

### 9.1 相关代码
- `src/market_analyzer.py` - 现有市场分析逻辑
- `src/core/market_review.py` - 现有复盘逻辑
- `data_provider/akshare_fetcher.py` - 数据获取逻辑

### 9.2 技术文档
- Element Plus UI: https://element-plus.org/
- FastAPI: https://fastapi.tiangolo.com/
- Vue 3: https://vuejs.org/

---

**设计文档完成，等待实现。**
