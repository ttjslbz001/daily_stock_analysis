# 任务计划 - 关注股票功能

## 目标
在主页中添加"我关注的股票"功能模块，显示股票价格和技术指标（布林线、MACD、RSI）

## 设计决策

### 数据存储
- **方式**: 数据库存储（SQLite）
- **表**: `watched_stocks`
- **用户**: 使用固定用户 ID 'default_user'
- **字段**: id, user_id, stock_code, stock_name, created_at, updated_at

### 数据更新方式
- **方式**: 一次性加载所有数据（价格 + 技术指标）
- **实时性**: 技术指标不实时更新，页面刷新时更新
- **用户体验**: 提供"刷新"按钮手动更新

### 技术指标计算
- 复用 `StockTrendAnalyzer` 类的 MACD、RSI 计算方法
- 新增布林线（Bollinger Bands）计算方法
- 服务类 `TechnicalIndicatorsService` 批量获取指标

### UI 设计
- 组件: `WatchedStocksPanel` 主容器
- 视图: 卡片形式展示关注股票
- 布局: 响应式网格（1/2/3列）
- 功能: 添加、删除、刷新关注股票

## 实施阶段

### Phase 1: 数据库层 (10分钟)
- [ ] 创建 `watched_stocks` 表
- [ ] 实现 `WatchedStocksRepository` 类
- [ ] 添加 CRUD 方法（add, remove, list, exists）
- [ ] 测试数据库操作

### Phase 2: 后端核心逻辑 (30分钟)
- [ ] 在 `StockTrendAnalyzer` 中添加 `_calculate_bollinger` 方法
- [ ] 在 `TrendAnalysisResult` 中添加布林线字段
- [ ] 创建 `TechnicalIndicatorsService` 服务类
- [ ] 实现批量获取技术指标方法
- [ ] 实现获取实时行情方法

### Phase 3: 后端 API (20分钟)
- [ ] 创建 Pydantic 模型（schemas/watched_stocks.py）
- [ ] 实现 GET /api/v1/watched 端点
- [ ] 实现 POST /api/v1/watched 端点
- [ ] 实现 DELETE /api/v1/watched/{stock_code} 端点
- [ ] 在 app.py 中注册路由
- [ ] 测试 API 端点

### Phase 4: 前端类型定义 (10分钟)
- [ ] 创建 watchedStocks.ts 类型文件
- [ ] 定义 WatchedStock, BollingerBands, MACD, RSI 接口
- [ ] 定义请求/响应类型

### Phase 5: 前端 API 服务 (10分钟)
- [ ] 创建 watchedStocks.ts API 客户端
- [ ] 实现 getWatchedStocks 方法
- [ ] 实现 addWatchedStock 方法
- [ ] 实现 removeWatchedStock 方法
- [ ] 在 api/index.ts 中导出

### Phase 6: 前端组件 (40分钟)
- [ ] 创建 WatchedStockCard 组件
- [ ] 创建 WatchedStocksPanel 组件
- [ ] 实现添加/删除功能
- [ ] 实现刷新功能
- [ ] 创建组件导出文件

### Phase 7: 集成到主页 (10分钟)
- [ ] 在 HomePage 中添加 WatchedStocksPanel
- [ ] 调整布局和样式
- [ ] 测试集成效果

### Phase 8: 测试与验证 (20分钟)
- [ ] 后端 API 测试
- [ ] 前端组件测试
- [ ] 端到端测试
- [ ] 修复发现的问题

### Phase 9: 样式优化 (10分钟)
- [ ] 响应式布局优化
- [ ] 样式细节调整
- [ ] 用户体验改进

## 关键问题

### 待解决的问题
1. 获取实时行情需要调用哪个 API？
2. 关注股票数量上限是否需要限制？
3. 技术指标计算超时如何处理？
4. 添加股票时如何验证股票代码有效性？

## 已做决策
- 使用固定用户 ID 'default_user'
- 一次性加载所有数据
- 卡片视图展示关注股票
- 复用现有 StockTrendAnalyzer

## 遇到的错误

(记录实施过程中遇到的问题和解决方案)

## 状态
- 总任务数: 42
- 已完成: 0
- 进行中: 0
- 待开始: 42

## 下一步
从 Phase 1 开始，创建数据库表和 Repository 类
