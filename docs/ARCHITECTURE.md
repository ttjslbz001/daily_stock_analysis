# A股自选股智能分析系统 - 架构文档

## 1. 系统概述

本系统是一个基于 Python 和 FastAPI 的股票智能分析平台，提供实时数据分析、技术指标计算、AI 驱动的投资建议和多渠道通知功能。

### 1.1 核心特性

- **多数据源支持**: 整合东方财富、Tushare、Akshare 等多个数据源
- **智能分析**: 基于 LLM (Gemini/DeepSeek 等) 的股票分析和投资建议
- **技术指标**: 自动计算布林线、MACD、RSI、KDJ 等技术指标
- **实时通知**: 支持钉钉、飞书、Discord 等多渠道消息推送
- **Web UI**: 基于 React 的现代化前端界面
- **MCP 协议**: 支持 Model Context Protocol，可与大模型工具集成

### 1.2 技术栈

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| 后端框架 | FastAPI | 现代、高性能的 Python Web 框架 |
| 数据库 | SQLite | 轻量级关系数据库，适合单机部署 |
| ORM | SQLAlchemy 2.0 | Python SQL 工具包和 ORM |
| 数据处理 | Pandas | 数据分析和处理 |
| 前端框架 | React 18 | 用户界面框架 |
| 样式方案 | Tailwind CSS | 实用优先的 CSS 框架 |
| AI/LLM | Litellm | 统一 LLM 客户端 |
| 任务调度 | Schedule | Python 定时任务库 |
| 测试框架 | Pytest | 测试框架 |

## 2. 系统架构

### 2.1 分层架构

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │   Web UI  │  │  API     │  │  Bots    │          │
│  │ (React)   │  │ (FastAPI)│  │(钉钉/飞书)│          │
│  └──────────┘  └────┬─────┘  └────┬─────┘          │
└───────────────────────┼──────────────┼─────────────────┘
                        │              │
┌───────────────────────┼──────────────┼─────────────────┐
│                    Business Layer                      │
│  ┌──────────┐  ┌──────┴──────┐  ┌──────┴──────┐      │
│  │Services  │  │  Analyzer   │  │Notification │      │
│  │  (业务)  │  │  (AI分析)   │  │ Service     │      │
│  └──────────┘  └─────────────┘  └─────────────┘      │
└───────────────────────┼───────────────────────────────┘
                        │
┌───────────────────────┼───────────────────────────────┐
│                   Data Access Layer                   │
│  ┌──────────┐  ┌──────┴──────┐  ┌──────────────┐     │
│  │Repository│  │DataFetcher  │  │  Database    │     │
│  │  (CRUD)  │  │ Manager     │  │  Manager     │     │
│  └──────────┘  └─────────────┘  └──────────────┘     │
└───────────────────────┼───────────────────────────────┘
                        │
┌───────────────────────┼───────────────────────────────┐
│                  External Services                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │   LLM    │  │  数据源   │  │  搜索    │             │
│  │ (Gemini) │  │(东财/等)  │  │ (Tavily) │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────┘
```

### 2.2 目录结构

```
daily_stock_analysis/
├── api/                          # API 层
│   ├── middlewares/              # 中间件
│   │   ├── auth.py              # 认证中间件
│   │   └── error_handler.py     # 错误处理中间件
│   ├── v1/                      # API v1 版本
│   │   ├── endpoints/           # 端点实现
│   │   ├── schemas/             # Pydantic 模型
│   │   └── router.py            # 路由配置
│   └── app.py                   # FastAPI 应用入口
├── apps/                        # 前端应用
│   └── dsa-web/                # Web UI
│       ├── src/                 # 源代码
│       │   ├── components/      # React 组件
│       │   ├── api/             # API 客户端
│       │   └── types/          # TypeScript 类型
│       └── package.json
├── bot/                         # 机器人
│   ├── dispatcher.py            # 命令分发器
│   └── handlers/               # 处理器
├── data_provider/               # 数据提供者
│   ├── base.py                 # 基础类
│   ├── akshare_fetcher.py      # Akshare 数据源
│   ├── efinance_fetcher.py     # 东方财富数据源
│   └── tushare_fetcher.py      # Tushare 数据源
├── src/                         # 核心业务逻辑
│   ├── analyzer.py              # AI 分析器
│   ├── config.py               # 配置管理
│   ├── notification.py         # 通知服务
│   ├── repositories/           # 数据访问层
│   │   ├── base.py             # 基础 Repository
│   │   ├── stock_repo.py       # 股票 Repository
│   │   └── ...
│   ├── services/               # 业务服务层
│   │   └── technical_indicators_service.py
│   ├── storage.py              # 数据库模型和管理
│   └── search_service.py      # 搜索服务
├── tests/                      # 测试
│   ├── test_*.py               # 单元测试
│   └── integration/           # 集成测试
├── scripts/                    # 脚本
│   └── ci_gate.sh             # CI 门控脚本
├── docs/                       # 文档
├── .github/                    # GitHub Actions
│   └── workflows/             # CI/CD 工作流
├── requirements.txt             # Python 依赖
├── pytest.ini                  # 测试配置
└── ARCHITECTURE.md             # 本文档
```

## 3. 核心模块设计

### 3.1 数据访问层 (Repository)

#### 设计原则

- **单一职责**: 每个 Repository 只负责一个数据模型的 CRUD 操作
- **依赖注入**: 通过 BaseRepository 提供 Session 上下文管理
- **事务管理**: 使用上下文管理器自动处理事务提交/回滚

#### 关键类

```python
# BaseRepository - 所有 Repository 的基类
class BaseRepository(Generic[ModelType]):
    """提供通用的 CRUD 操作"""
    def get_by_id(self, id: int) -> Optional[ModelType]
    def get_all(self, limit, offset, order_by) -> List[ModelType]
    def filter(self, filters) -> List[ModelType]
    def create(self, **kwargs) -> ModelType
    def update(self, id, **kwargs) -> ModelType
    def delete(self, id) -> bool
    def count(self, filters) -> int
    def bulk_create(self, items) -> List[ModelType]
```

#### Session 管理

使用 `SessionContext` 包装器确保会话正确关闭：

```python
with db.get_session() as session:
    # 自动提交
    obj = session.query(Model).first()

with db.get_session(auto_commit=False) as session:
    # 手动控制事务
    session.add(obj1)
    session.add(obj2)
    session.commit()
```

### 3.2 业务服务层 (Service)

#### 职责

- 实现业务逻辑
- 协调多个 Repository
- 调用外部服务
- 数据转换和验证

#### 示例

```python
class TechnicalIndicatorsService:
    """技术指标计算服务"""

    def get_indicators_for_stocks(self, stock_codes: List[str]) -> Dict:
        """批量获取股票技术指标"""
        results = {}

        for code in stock_codes:
            # 获取历史数据
            df = self.data_manager.get_daily_data(code)

            # 计算技术指标
            analysis = self.analyzer.analyze(code, df)

            # 构建响应
            results[code] = {
                'price': analysis.current_price,
                'bollinger': {...},
                'macd': {...},
                'rsi': {...},
                'kdj': {...}
            }

        return results
```

### 3.3 API 层

#### 设计模式

- **端点分离**: 每个功能模块一个端点文件
- **Schema 验证**: 使用 Pydantic 进行请求/响应验证
- **错误处理**: 统一错误处理中间件

#### 端点结构

```
api/v1/endpoints/
├── stocks.py          # 股票相关端点
├── watched_stocks.py  # 关注股票端点
├── analysis.py        # 分析端点
├── backtest.py       # 回测端点
└── sectors.py        # 板块端点
```

#### 错误响应格式

```json
{
  "error": "error_code",
  "message": "Human readable message",
  "timestamp": "2024-01-01T00:00:00Z",
  "request_id": "uuid"
}
```

### 3.4 数据提供者层 (Data Provider)

#### 设计模式

- **策略模式**: 支持多个数据源切换
- **优先级机制**: 按优先级尝试不同数据源
- **断点续传**: 支持智能更新已获取的数据

#### 数据源优先级

1. **东方财富** (efinance) - 最高优先级
2. **Akshare** - 备选
3. **Tushare** - 需要授权码
4. **通达信** (pytdx) - 实时行情
5. **证券宝** (baostock)
6. **Yahoo Finance** (yfinance) - 兜底

#### 断点续传机制

```python
def sync_daily_data(self, code: str, force_update: bool = False):
    """同步日线数据（支持断点续传）"""

    # 获取数据库中最新日期
    last_date = self.get_last_date(code)

    # 按日期增量获取数据
    for date in self.get_missing_dates(last_date):
        data = self.fetcher.get_daily_data(code, date)

        if data:
            self.save_daily_data(code, date, data)
        else:
            logger.warning(f"获取 {code} {date} 数据失败，将重试")
```

## 4. 数据流

### 4.1 股票分析流程

```
用户请求
    │
    ▼
┌─────────────────┐
│  API 端点       │
│  /api/v1/stock/ │
│  {code}/analyze │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  StockService   │
│  验证请求       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ DataFetcher     │
│ 获取历史数据    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ StockAnalyzer   │
│ 计算技术指标    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ GeminiAnalyzer  │
│ AI 分析和建议    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  返回结果       │
│  JSON 响应      │
└─────────────────┘
```

### 4.2 关注股票更新流程

```
定时任务触发
    │
    ▼
┌─────────────────┐
│  遍历关注列表   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 获取实时行情    │
│ (DataFetcher)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 计算技术指标    │
│ (技术分析)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 判断触发条件    │
│ - 价格突破      │
│ - 指标变化      │
└────────┬────────┘
         │
         ▼
    ┌────┴────┐
    │         │
    ▼         ▼
┌──────┐ ┌────────┐
│满足  │ │ 不满足  │
└──┬───┘ └────┬───┘
   │          │
   ▼          │
┌─────────┐   │
│ 通知用户 │   │
└────┬────┘   │
     │        │
     └────┬───┘
          ▼
    更新缓存
```

## 5. 安全性

### 5.1 认证和授权

- **API Key**: 通过 HTTP Header 认证
- **Rate Limiting**: 防止 API 滥用
- **输入验证**: Pydantic Schema 验证

### 5.2 数据安全

- **SQL 注入防护**: 使用 SQLAlchemy ORM 参数化查询
- **敏感信息**: 存储在环境变量中，不提交到代码仓库
- **密钥扫描**: CI 流程自动检测泄露的密钥

## 6. 性能优化

### 6.1 数据库优化

- **索引**: 为常用查询字段创建索引
- **连接池**: 使用 SQLAlchemy 连接池
- **批量操作**: 使用 bulk_create 批量插入

### 6.2 缓存策略

- **技术指标缓存**: 关注股票指标缓存 12 小时
- **实时行情**: 可通过 force_refresh 强制刷新
- **Session 管理**: 使用上下文管理器防止连接泄漏

### 6.3 异步处理

- **FastAPI 异步端点**: 使用 async/await
- **后台任务**: 使用 FastAPI BackgroundTasks
- **定时任务**: 使用 schedule 库

## 7. 测试策略

### 7.1 测试金字塔

```
        ┌──────┐
        │ E2E  │  (少量，端到端测试)
        │ 10%  │
        ├──────┤
        │Integration│
        │ 30%       │
        ├───────────┤
        │   Unit    │  (大量，单元测试)
        │   60%     │
        └───────────┘
```

### 7.2 测试配置

```ini
# pytest.ini
[pytest]
addopts =
    --cov=src
    --cov=api
    --cov-fail-under=70
    --asyncio-mode=auto

markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
```

### 7.3 覆盖率目标

- **总体覆盖率**: >= 70%
- **核心模块**: >= 80%
- **新增代码**: >= 85%

## 8. 部署

### 8.1 Docker 部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 8.2 环境变量

```bash
# 数据库
DB_PATH=data/stock_analysis.db

# LLM 配置
GEMINI_API_KEY=xxx
OPENAI_API_KEY=xxx

# 数据源
TUSHARE_TOKEN=xxx

# 通知配置
DINGTALK_WEBHOOK=xxx
FEISHU_WEBHOOK=xxx
```

## 9. 监控和日志

### 9.1 日志级别

- **DEBUG**: 详细调试信息
- **INFO**: 一般信息
- **WARNING**: 警告信息
- **ERROR**: 错误信息
- **CRITICAL**: 严重错误

### 9.2 日志格式

```python
logger.info(f"用户 {user_id} 请求分析股票 {code}")
logger.error(f"数据库连接失败: {e}", exc_info=True)
```

## 10. 未来改进

- [ ] 添加 Redis 缓存层
- [ ] 支持 PostgreSQL 数据库
- [ ] 实现 WebSocket 实时推送
- [ ] 添加更多技术指标
- [ ] 支持回测报告导出
- [ ] 添加用户认证和权限管理
- [ ] 实现多租户支持
