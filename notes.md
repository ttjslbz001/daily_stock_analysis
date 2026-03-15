# 项目笔记

---

## 📋 会话摘要（2026-03-15）

### 当前分支
`feature/software-engineering-improvement`

### 最近完成的工作

#### 1. 软件工程改进（P0-P1）
- ✅ CI 安全扫描
- ✅ 数据库 Session 上下文管理
- ✅ 测试覆盖率报告（70% 阈值）
- ✅ 统一错误处理中间件
- ✅ BaseRepository 减少代码重复
- ✅ 完整的架构文档（ARCHITECTURE.md）

#### 2. 前端测试基础设施
- ✅ Vitest 配置
- ✅ 测试环境设置
- ✅ 测试脚本和 Makefile
- ✅ Pre-commit 自动检查
- ✅ CI/CD 集成

#### 3. 关注股票功能
- ✅ Phase 1-7: 数据库层、后端核心逻辑、后端 API、前端类型定义、前端 API 服务、前端组件、集成到主页
- ✅ Phase 10-11: 单只股票刷新功能、指标行布局优化

#### 4. WatchListIndicatorScheduler (Phase 1 完成)
- ✅ Phase 1, Task 1.1: 创建 WatchListIndicatorScheduler 类
- ✅ Phase 1, Task 1.2: 实现过期检查逻辑
- ✅ Task 4.1: 编写过期检查单元测试（14个测试）
- ✅ Task 4.2: 编写刷新逻辑单元测试
- 测试覆盖率: 75% (新增代码)

### Git 状态
- 工作区干净，无待提交的更改
- 最近提交：`e3c893e feat: implement WatchListIndicatorScheduler for automatic indicator refresh`

### 可用命令

```bash
# 运行所有测试
make test-all

# 快速检查
make check

# 查看帮助
make help
```

### 下一次会话待办
- [ ] Phase 8: 测试与验证（后端 API 测试、前端组件测试、端到端测试）
- [ ] Phase 9: 样式优化（响应式布局优化、样式细节调整、用户体验改进）
- [ ] 可能需要修复的其他问题

---

## 前端测试改进

### 2026-03-15 - 前端测试基础设施完成

#### 测试框架配置 ✅

1. **Vitest 配置**
   - 创建 `apps/dsa-web/vitest.config.ts`
   - 配置 jsdom 测试环境
   - 设置 70% 覆盖率阈值（行、函数、分支、语句）
   - 配置覆盖率报告（HTML、JSON、LCOV）
   - 支持并行测试执行

2. **测试环境设置**
   - 创建 `apps/dsa-web/src/test/setup.ts`
   - 集成 @testing-library/jest-dom 匹配器
   - 自动清理 DOM（afterEach）

3. **测试依赖**
   - @testing-library/react - React 组件测试
   - @testing-library/user-event - 用户交互模拟
   - @testing-library/jest-dom - DOM 匹配器
   - @vitest/ui - 可视化测试 UI
   - @vitest/coverage-v8 - 覆盖率工具
   - jsdom - DOM 环境

#### 测试脚本 ✅

1. **package.json 脚本**
   ```json
   "test": "vitest"                    // 监听模式
   "test:ui": "vitest --ui"          // 可视化 UI
   "test:run": "vitest run"           // 单次运行
   "test:coverage": "vitest run --coverage"  // 覆盖率报告
   "type-check": "tsc --noEmit"       // 类型检查
   "check": "npm run type-check && npm run lint && npm run test:run"  // 完整检查
   ```

2. **全项目测试脚本** (`scripts/test-all.sh`)
   - Python 语法检查
   - 后端 pytest 测试（覆盖率 60%）
   - 前端类型检查（TypeScript）
   - 前端 lint（ESLint）
   - 前端测试（Vitest）
   - 前端构建验证

3. **Pre-commit 检查脚本** (`scripts/pre-commit-check.sh`)
   - Python 文件语法检查
   - Python flake8 代码风格检查
   - TypeScript/JavaScript 类型检查
   - ESLint 代码风格检查
   - JSON/YAML 配置文件验证
   - 快速测试（跳过慢测试）

4. **Makefile 简化命令**
   - `make test-all` - 运行所有测试
   - `make test-quick` - 快速测试
   - `make test-backend` - 后端测试
   - `make test-frontend` - 前端测试
   - `make test-coverage-backend` - 后端覆盖率
   - `make test-coverage-frontend` - 前端覆盖率
   - `make check` - 完整检查（类型 + lint + 测试）
   - `make build` - 构建所有项目
   - `make dev` - 启动开发服务器

#### CI/CD 集成 ✅

1. **更新 CI workflow**
   - web-gate 任务添加：
     - TypeScript 类型检查
     - ESLint 代码风格检查
     - Vitest 测试执行
     - 覆盖率报告上传
   - 并行执行后端和前端测试

2. **Git Pre-commit Hook**
   - 配置 `.git/hooks/pre-commit`
   - 自动运行 pre-commit 检查脚本
   - 防止提交有问题的代码

#### 测试示例 ✅

1. **组件测试示例** (`src/components/Button.test.tsx`)
   - 渲染测试
   - 点击事件测试
   - 禁用状态测试

2. **API 测试示例** (`src/api/watchedStocks.test.ts`)
   - API 调用测试
   - 错误处理测试
   - 参数验证测试

#### 使用指南

##### 本地开发

```bash
# 运行所有测试（后端 + 前端）
make test-all

# 运行快速测试（跳过慢测试）
make test-quick

# 只运行前端测试
make test-frontend

# 运行前端测试覆盖率
make test-coverage-frontend

# 运行前端测试 UI
cd apps/dsa-web && npm run test:ui

# 完整检查（类型 + lint + 测试）
make check
```

##### 提交前检查

```bash
# Git 会自动运行 pre-commit 检查
git add .
git commit  # 自动运行检查脚本

# 手动运行检查
./scripts/pre-commit-check.sh
```

##### CI/CD

- PR 创建或更新时自动运行
- 并行执行后端和前端测试
- 生成覆盖率报告
- 上传到 GitHub Actions artifacts

#### 测试覆盖率目标

- **总体覆盖率**: 70%
- **核心模块**: 80%
- **新增代码**: 85%

#### 测试文件位置

```
apps/dsa-web/
├── src/
│   ├── components/
│   │   └── Button.test.tsx        # 组件测试示例
│   ├── api/
│   │   └── watchedStocks.test.ts  # API 测试示例
│   └── test/
│       └── setup.ts              # 测试环境设置
├── vitest.config.ts              # Vitest 配置
└── package.json                  # 测试脚本

scripts/
├── test-all.sh                  # 全项目测试
└── pre-commit-check.sh           # Pre-commit 检查

Makefile                        # Make 命令
```

#### 后续改进

- [ ] 添加更多组件测试
- [ ] 添加集成测试
- [ ] 添加 E2E 测试（Playwright）
- [ ] 创建测试工具函数和 mock 数据
- [ ] 添加性能测试
- [ ] 创建测试文档

## 软件工程改进

### 2026-03-15 - P0-P1 改进完成

#### P0 关键问题 (已完成)

1. **CI 安全扫描** ✅
   - 创建 `.github/workflows/security.yml`
   - 包含 Safety (依赖漏洞扫描)、Bandit (SAST)、Semgrep (SAST)
   - 添加 CodeQL 分析支持
   - 集成 TruffleHog 密钥泄露检测
   - 支持定时扫描和手动触发

2. **数据库 Session 管理** ✅
   - 实现 `SessionContext` 类，支持自动事务管理
   - 添加 `__enter__/__exit__` 方法确保资源正确释放
   - 改进 `DatabaseManager.get_session()` 返回上下文管理器
   - 支持自动提交和手动提交两种模式
   - 详细的错误日志记录

3. **测试覆盖率** ✅
   - 创建 `pytest.ini` 配置文件
   - 添加 pytest、pytest-cov 等测试依赖
   - 设置 70% 覆盖率阈值
   - 生成 HTML、XML 和终端覆盖率报告
   - 更新 CI workflow 添加测试覆盖率任务

4. **错误处理** ✅
   - 创建 `ErrorCode` 类，统一错误码定义
   - 实现 `create_error_response()` 函数，标准化错误响应
   - 改进 `ErrorHandlerMiddleware`，添加请求 ID 追踪
   - 支持调试模式，返回详细错误信息
   - 集成 SQLAlchemy 异常处理

#### P1 高优先级问题 (已完成)

1. **依赖注入/代码复用** ✅
   - 创建 `BaseRepository` 泛型基类
   - 提供通用 CRUD 操作 (get, create, update, delete, filter, count)
   - 支持批量操作 (bulk_create)
   - 自动错误处理和日志记录
   - 类型安全的查询构建

2. **架构文档** ✅
   - 创建 `docs/ARCHITECTURE.md`
   - 包含系统概述和技术栈
   - 详细的分层架构图
   - 核心模块设计说明
   - 数据流图
   - 安全性和性能优化策略
   - 部署和监控指南

3. **前端测试** ⏸️ (待后续实施)
   - 规划使用 Vitest + Testing Library
   - 需要创建前端测试套件

4. **API 文档** ⏸️ (待后续实施)
   - 当前使用 FastAPI 自动生成的 OpenAPI 文档
   - 计划添加更多错误码文档和示例响应

### 技术细节

#### SessionContext 使用示例

```python
# 自动提交模式（默认）
with db.get_session() as session:
    result = session.query(Stock).all()
    # 自动提交事务

# 手动提交模式
with db.get_session(auto_commit=False) as session:
    session.add(obj1)
    session.add(obj2)
    session.commit()  # 手动提交
    # 如果发生异常，自动回滚
```

#### BaseRepository 使用示例

```python
from src.repositories.base import BaseRepository
from src.storage import StockDaily

class StockRepository(BaseRepository[StockDaily]):
    def __init__(self):
        super().__init__(StockDaily)

    # 继承通用方法：
    # - get_by_id(id)
    # - get_all(limit, offset, order_by)
    # - filter(filters)
    # - create(**kwargs)
    # - update(id, **kwargs)
    # - delete(id)
    # - count(filters)
    # - bulk_create(items)
```

#### 错误响应格式

```json
{
  "error": "error_code",
  "message": "Human readable message",
  "timestamp": "2024-01-01T00:00:00Z",
  "request_id": "uuid",
  "detail": {...}
}
```

### 相关文件

- `.github/workflows/security.yml` - 安全扫描 CI workflow
- `.github/workflows/ci.yml` - CI workflow（已更新）
- `pytest.ini` - 测试配置
- `src/storage.py` - SessionContext 类
- `src/repositories/base.py` - BaseRepository 类
- `api/middlewares/error_handler.py` - 错误处理中间件
- `docs/ARCHITECTURE.md` - 系统架构文档
- `requirements.txt` - 更新的依赖列表

## 关注股票功能改进

### 设计决策

#### 1. 单只股票刷新功能
- **API 策略**: 复用现有的 `GET /api/v1/watched/{stock_code}/indicators?force_refresh=true` 端点
- **状态管理**: 在单个组件内管理 `refreshing` 状态，无需全局状态管理
- **用户体验**:
  - 刷新按钮显示旋转动画
  - 刷新期间禁用按钮，防止重复点击
  - 保留旧数据直到新数据到达
  - 刷新失败显示错误信息

#### 2. 指标行布局优化
- **布局方案**: 使用固定宽度的列布局 + flexbox
  - 每个指标组有固定的 min-width
  - 使用 flex-1 分配剩余空间
  - 表头和内容列宽度严格对齐
- **组件化**: 创建 `IndicatorValue` 复用组件，统一指标展示格式
- **响应式设计**:
  - 大屏幕 (sm+): 单行显示所有指标
  - 小屏幕: 允许换行，保持数据可读性
- **视觉优化**:
  - 指标之间添加分隔线
  - 使用一致的字体（等宽字体用于数值）
  - 统一的颜色方案（红色涨/绿色跌）

### 技术栈

#### 前端
- **框架**: React 18 + TypeScript
- **样式**: Tailwind CSS
- **状态管理**: React Hooks (useState, useEffect, useCallback)
- **HTTP 客户端**: 自定义 apiClient 封装

#### 后端
- **框架**: FastAPI
- **数据库**: SQLite
- **缓存策略**: 12小时缓存
  - 使用 `force_refresh` 参数强制刷新
  - 缓存存储在数据库中

### 文件结构

```
apps/dsa-web/src/
├── components/watchedStocks/
│   └── WatchedStocksPanel.tsx  # 主组件（需要修改）
├── types/
│   └── watchedStocks.ts        # 类型定义（无需修改）
└── api/
    └── watchedStocks.ts         # API 客户端（无需修改）

api/v1/endpoints/
└── watched_stocks.py            # 后端 API（已支持单只股票刷新，无需修改）
```

### 约束与假设

1. **网络延迟**: 单只股票刷新可能需要 1-3 秒
2. **并发限制**: 当前未实现防抖，连续点击会发起多个请求
3. **数据完整性**: 刷新期间显示旧数据，不显示加载占位
4. **移动端**: 小屏幕允许指标换行，不追求完美对齐

### 已知问题

1. ~~**布局对齐**: 当前使用 flex-wrap 导致不同行之间列不对齐~~ (已修复)
2. ~~**刷新粒度**: 只能全局刷新所有股票，无法单独刷新某一只~~ (已修复)
3. ~~**响应式**: 移动端指标显示可能过于拥挤~~ (已优化)

## 实施记录

### 2026-03-15 - Phase 10 & 11 完成

#### Phase 10: 单只股票刷新功能 (已完成)
- 在 `StockWithLoading` 接口中添加 `refreshing` 状态
- 实现 `handleRefreshStock` 函数，调用 `force_refresh=true` 的 API
- 在指标行右侧添加刷新按钮，带加载状态动画
- 测试通过 - API 返回正确的数据

#### Phase 11: 指标行布局优化 (已完成)
- 创建 `IndicatorValue` 组件，统一指标展示格式
- 使用固定宽度的列布局 (min-w-[140px])，确保各指标行对齐
- 更新表头宽度与指标列匹配
- 添加指标之间的分隔线
- 优化响应式布局 (flex-wrap 处理小屏幕)
- 测试通过 - TypeScript 编译成功，前端构建正常

### 测试要点

1. **功能测试**
   - 单只股票刷新按钮点击
   - 刷新加载状态显示
   - 刷新失败错误处理
   - 刷新成功数据更新

2. **布局测试**
   - 不同屏幕尺寸（移动端、平板、桌面）
   - 长股票代码/数值的显示
   - 空数据状态（year_high/low 为 null）
   - 表头与内容对齐

3. **边界测试**
   - 连续快速点击刷新按钮
   - 网络错误处理
   - 多只股票同时刷新

---

## 关注股票指标定时刷新功能

### 2026-03-15 - 规划阶段

#### 功能需求

创建一个定时任务，自动刷新关注股票的技术指标：

1. **刷新间隔**: 每 8 小时自动刷新一次
2. **启动行为**: 服务器启动时，如果指标缓存时间超过 8 小时，立即刷新
3. **刷新方式**: 使用现有的 `TechnicalIndicatorsService` 批量获取指标
4. **错误处理**: 单个股票刷新失败不影响其他股票，记录错误日志

#### 技术设计

##### 架构方案

使用 FastAPI 的 `lifespan` 事件和 `asyncio` 后台任务：

```
FastAPI Startup
    └─> WatchListIndicatorScheduler.start()
         └─> asyncio.create_task(_run_refresh_loop())
              ├─> Initial: refresh_if_needed()
              ├─> Wait 8 hours
              └─> Loop: refresh_all_indicators() -> Wait 8 hours
```

##### 组件设计

1. **WatchListIndicatorScheduler** (`src/services/watchlist_indicator_scheduler.py`)
   - `_run_refresh_loop()`: 异步循环，每 8 小时触发一次刷新
   - `refresh_if_needed()`: 检查并刷新过期指标
   - `_refresh_all_indicators()`: 批量刷新所有关注股票
   - `_is_refresh_needed()`: 检查指标是否过期
   - `start()`: 启动后台任务
   - `stop()`: 取消后台任务

2. **FastAPI Lifespan 集成** (`api/app.py`)
   - 在 `app_lifespan()` 中启动和停止调度器

3. **配置支持**
   - `WATCHLIST_AUTO_REFRESH_ENABLED`: 是否启用自动刷新（默认: true）
   - `WATCHLIST_REFRESH_INTERVAL_HOURS`: 刷新间隔小时数（默认: 8）

##### 数据库依赖

- `WatchedStock.indicators_cached_at`: 记录指标缓存时间
- `WatchedStocksRepository.list()`: 获取所有关注股票
- `WatchedStocksRepository.update_cached_indicators()`: 更新指标缓存

##### 服务依赖

- `TechnicalIndicatorsService.get_indicators()`: 批量获取技术指标

#### 实施计划

**Phase 1: 创建调度器服务** (2 任务)
- Task 1.1: 创建 WatchListIndicatorScheduler 类（15-20分钟）
- Task 1.2: 实现过期检查逻辑（10分钟）

**Phase 2: 集成到 FastAPI** (1 任务)
- Task 2.1: 添加到 app_lifespan（10分钟）

**Phase 3: 配置支持** (2 任务)
- Task 3.1: 添加环境变量配置（5分钟）
- Task 3.2: 加载配置（10分钟）

**Phase 4: 测试** (3 任务)
- Task 4.1: 过期检查单元测试（15分钟）
- Task 4.2: 刷新逻辑单元测试（15分钟）
- Task 4.3: 手动集成测试（20分钟）

**Phase 5: 文档** (2 任务)
- Task 5.1: 更新 README（10分钟）
- Task 5.2: 添加代码注释（10分钟）

#### 设计决策

1. **刷新策略**: 滑动窗口（从上次成功刷新时间开始计算）
   - 优势: 灵活适应不同启动时间
   - 劣势: 刷新时间不固定

2. **启动刷新**: 只在指标过期时刷新
   - 优势: 避免不必要的刷新，加快启动速度
   - 劣势: 首次启动可能显示旧数据（如果未过期）

3. **技术选型**: asyncio 后台任务
   - 优势: 与 FastAPI 原生集成，不阻塞事件循环
   - 劣势: 需要处理异步取消

4. **服务复用**: 使用现有 TechnicalIndicatorsService
   - 优势: 避免代码重复，利用已有优化
   - 劣势: 依赖服务层的实现

#### 错误处理策略

1. **单个股票失败**: 记录日志，继续处理其他股票
2. **数据库错误**: 记录日志，不启动调度器
3. **调度循环异常**: 捕获异常，继续循环（不崩溃）

#### 配置示例

```bash
# .env
WATCHLIST_AUTO_REFRESH_ENABLED=true
WATCHLIST_REFRESH_INTERVAL_HOURS=8
```

#### 相关文件

- `src/services/watchlist_indicator_scheduler.py` (新建)
- `api/app.py` (修改)
- `.env.example` (修改)
- `tests/test_watchlist_indicator_scheduler.py` (新建)
- `README.md` (修改)
- `docs/plans/2026-03-15-watchlist-indicator-scheduler.md` (详细计划)
- `task_plan_scheduler.md` (任务跟踪)

### 2026-03-15 - Phase 1 完成（调度器服务与测试）

#### 完成任务

1. **Task 1.1: 创建 WatchListIndicatorScheduler 类** ✅
   - 文件: `src/schedulers/watchlist_indicator_scheduler.py`
   - 实现所有方法:
     - `__init__`: 初始化调度器
     - `start()`: 启动后台刷新循环
     - `stop()`: 停止后台任务
     - `refresh_if_needed()`: 检查并刷新过期指标
     - `_refresh_all_indicators()`: 批量刷新所有关注股票
     - `_is_refresh_needed()`: 检查指标是否过期
     - `_run_refresh_loop()`: 异步刷新循环
   - 添加全面的日志记录

2. **Task 1.2: 实现过期检查逻辑** ✅
   - 检查 `indicators_cached_at` 对比 8 小时阈值
   - 处理 None 值（从未缓存的情况）
   - 实现滑动窗口策略（从上次成功刷新时间计算）

3. **Task 4.1: 编写过期检查单元测试** ✅
   - 测试 None 时间戳（需要刷新）
   - 测试旧时间戳（超过阈值，需要刷新）
   - 测试新鲜时间戳（不需要刷新）
   - 测试恰好处于阈值的时间戳（需要刷新）

4. **Task 4.2: 编写刷新逻辑单元测试** ✅
   - 测试批量刷新成功
   - 测试单个股票失败时的错误处理
   - 测试空关注列表的处理
   - 测试调度器启动/停止生命周期
   - 测试自定义刷新间隔和用户 ID

#### 测试结果

- **测试数量**: 14 个单元测试
- **通过率**: 100% (14/14)
- **覆盖率**: 75% (新增代码)
- **测试文件**: `tests/test_watchlist_indicator_scheduler.py`

#### 技术实现

**核心类**: WatchListIndicatorScheduler

```python
# 位置: src/schedulers/watchlist_indicator_scheduler.py
from src.schedulers.watchlist_indicator_scheduler import WatchListIndicatorScheduler

# 使用示例
scheduler = WatchListIndicatorScheduler(
    repo=WatchedStocksRepository(),
    indicators_service=TechnicalIndicatorsService(),
    refresh_interval_hours=8,
    user_id='default_user'
)

await scheduler.start()  # 启动后台任务
# ... 运行 ...
await scheduler.stop()   # 停止后台任务
```

**关键特性**:
- 使用 asyncio 后台任务，不阻塞 FastAPI 事件循环
- 滑动窗口刷新间隔（从上次成功刷新时间开始计算）
- 启动时只刷新过期指标，避免不必要的刷新
- 单个股票失败不影响其他股票
- 全面的错误处理和日志记录

#### 下一步

- Task 2.1: 将调度器集成到 FastAPI lifespan
- Task 3.1: 添加环境变量配置
- Task 3.2: 加载配置到调度器
- Task 4.3: 手动集成测试
- Task 5.1: 更新 README
- Task 5.2: 添加代码注释
