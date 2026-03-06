# Daily Stock Analysis - Development Guide

> A comprehensive guide for developers working on the Daily Stock Analysis system.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Getting Started](#getting-started)
4. [Core Components](#core-components)
5. [Data Flow](#data-flow)
6. [Configuration](#configuration)
7. [API Reference](#api-reference)
8. [Frontend Development](#frontend-development)
9. [Bot Development](#bot-development)
10. [Testing](#testing)
11. [Deployment](#deployment)
12. [Contributing](#contributing)

---

## Project Overview

**Daily Stock Analysis** is an AI-powered stock analysis system that:
- Fetches market data from multiple sources with automatic failover
- Uses LLM (Gemini, Claude, OpenAI, DeepSeek) for intelligent analysis
- Generates decision dashboard reports with trading signals
- Sends notifications to multiple channels (WeChat, Feishu, Telegram, Email, etc.)
- Provides a web UI and bot integrations for interactive analysis

### Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.10+, FastAPI, SQLAlchemy, LiteLLM |
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS, Zustand |
| **Database** | SQLite (default), PostgreSQL (optional) |
| **AI/LLM** | Gemini, Claude, OpenAI, DeepSeek via LiteLLM |
| **Data Sources** | Efinance, AkShare, Tushare, Baostock, YFinance |
| **Deployment** | Docker, GitHub Actions (scheduled runs) |

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Entry Points                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  CLI (main.py)  │  API (FastAPI)  │  Web UI (React)  │  Bots (DingTalk, etc)│
└────────┬────────┴────────┬────────┴────────┬─────────┴──────────┬──────────┘
         │                 │                 │                    │
         ▼                 ▼                 ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Core Pipeline (src/core/pipeline.py)               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ Data Fetch  │→ │   Analysis  │→ │    LLM      │→ │    Notification     │ │
│  │ (failover)  │  │  (trends)   │  │  (insights) │  │   (multi-channel)   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
         │                 │                 │                    │
         ▼                 ▼                 ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Infrastructure Layer                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ DataFetcher │  │   Storage   │  │   Config    │  │   Search Service    │ │
│  │   Manager   │  │  (SQLite)   │  │  (singleton)│  │  (Tavily/SerpAPI)   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
daily_stock_analysis/
├── main.py                    # CLI entry point
├── src/
│   ├── config.py              # Configuration management (singleton)
│   ├── storage.py             # Database layer (SQLAlchemy ORM)
│   ├── analyzer.py            # LLM analysis layer
│   ├── notification.py        # Notification service
│   ├── search_service.py      # News search service
│   ├── stock_analyzer.py      # Technical trend analysis
│   ├── core/
│   │   ├── pipeline.py        # Main analysis pipeline
│   │   └── trading_calendar.py
│   ├── services/
│   │   ├── analysis_service.py
│   │   ├── task_queue.py      # Async task management
│   │   └── history_service.py
│   ├── agent/                 # AI agent for strategy chat
│   └── notification_sender/   # Individual channel senders
├── data_provider/
│   ├── base.py                # DataFetcherManager + BaseFetcher
│   ├── efinance_fetcher.py    # East Money (highest priority)
│   ├── akshare_fetcher.py     # AkShare (free, no auth)
│   ├── tushare_fetcher.py     # Tushare Pro (token required)
│   └── yfinance_fetcher.py    # Yahoo Finance (US stocks)
├── api/
│   ├── app.py                 # FastAPI application
│   ├── deps.py                # Dependencies
│   └── v1/
│       ├── router.py          # Route aggregation
│       ├── endpoints/         # API endpoints
│       └── schemas/           # Pydantic models
├── apps/dsa-web/              # React frontend
│   └── src/
│       ├── pages/             # Page components
│       ├── api/               # API client
│       ├── components/        # Reusable components
│       ├── hooks/             # Custom React hooks
│       └── stores/            # Zustand stores
├── bot/
│   ├── models.py              # BotMessage, BotResponse
│   ├── dispatcher.py          # Command routing
│   ├── handler.py             # Webhook handler
│   ├── platforms/             # Platform adapters
│   └── commands/              # Command handlers
├── strategies/                # YAML strategy definitions
├── tests/                     # Test files
└── docker/                    # Docker configuration
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend development)
- SQLite or PostgreSQL

### Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/daily_stock_analysis.git
cd daily_stock_analysis

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd apps/dsa-web && npm install && cd ../..
```

### Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Configure required settings in `.env`:
```bash
# Stock list (required)
STOCK_LIST=600519,000001,300750

# LLM configuration (at least one required)
GEMINI_API_KEY=your-gemini-key
# Or use YAML config for multi-channel:
LITELLM_CONFIG=./litellm_config.yaml

# Notification (at least one recommended)
WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
```

3. Run the analysis:
```bash
# CLI mode
python main.py

# Web UI mode
python main.py --web

# API mode
uvicorn api.app:app --host 0.0.0.0 --port 8000
```

---

## Core Components

### 1. Pipeline (`src/core/pipeline.py`)

The central orchestrator for stock analysis.

```python
from src.core.pipeline import StockAnalysisPipeline

pipeline = StockAnalysisPipeline(config=config)

# Run full analysis
results = pipeline.run(
    stock_codes=['600519', '000001'],
    dry_run=False,           # True = fetch data only
    send_notification=True,
    merge_notification=False
)
```

**Key methods:**

| Method | Description |
|--------|-------------|
| `run()` | Main entry - process all stocks |
| `process_single_stock()` | Process one stock (thread pool) |
| `analyze_stock()` | Deep analysis with LLM |
| `fetch_and_save_stock_data()` | Get data with checkpoint |
| `_send_notifications()` | Broadcast to all channels |

### 2. Analyzer (`src/analyzer.py`)

LLM integration for generating analysis.

```python
from src.analyzer import GeminiAnalyzer

analyzer = GeminiAnalyzer()

result = analyzer.analyze(
    context={
        'code': '600519',
        'stock_name': '贵州茅台',
        'today': {...},
        'realtime': {...},
        'chip': {...}
    },
    news_context="Recent news..."
)

# Returns AnalysisResult with:
# - sentiment_score (0-100)
# - trend_prediction
# - operation_advice
# - dashboard (decision dashboard data)
```

### 3. Data Provider (`data_provider/base.py`)

Multi-source data fetching with failover.

```python
from data_provider import DataFetcherManager

manager = DataFetcherManager()

# Get daily data (auto-failover)
df, source = manager.get_daily_data('600519', days=30)

# Get realtime quote
quote = manager.get_realtime_quote('600519')
print(quote.price, quote.volume_ratio, quote.turnover_rate)

# Get chip distribution
chip = manager.get_chip_distribution('600519')
print(chip.profit_ratio, chip.avg_cost)
```

**Data source priority:**
1. EfinanceFetcher (East Money)
2. AkshareFetcher
3. TushareFetcher (if token configured)
4. PytdxFetcher
5. BaostockFetcher
6. YfinanceFetcher (US stocks only)

### 4. Storage (`src/storage.py`)

Database layer using SQLAlchemy ORM.

```python
from src.storage import DatabaseManager

db = DatabaseManager.get_instance()

# Check if data exists (checkpoint)
if db.has_today_data('600519'):
    print("Data already fetched")

# Save daily data
db.save_daily_data(df, code='600519', data_source='efinance')

# Get analysis context
context = db.get_analysis_context('600519')

# Save analysis result
record_id = db.save_analysis_history(
    result=analysis_result,
    query_id='abc123',
    news_content=news_text
)

# Query history
records = db.get_analysis_history(query_id='abc123', limit=10)
```

### 5. Notification (`src/notification.py`)

Multi-channel notification service.

```python
from src.notification import NotificationService

notifier = NotificationService()

# Check available channels
if notifier.is_available():
    channels = notifier.get_available_channels()
    print(f"Channels: {channels}")  # [WECHAT, FEISHU, TELEGRAM, ...]

# Generate report
report = notifier.generate_dashboard_report(results)

# Save to file
filepath = notifier.save_report_to_file(report)

# Send to all channels
notifier.send(report)
```

### 6. Configuration (`src/config.py`)

Singleton configuration manager.

```python
from src.config import get_config, Config

config = get_config()

# Access settings
stock_list = config.stock_list
api_keys = config.gemini_api_keys
model = config.litellm_model

# Hot-reload stock list
config.refresh_stock_list()

# Validate configuration
issues = config.validate_structured()
for issue in issues:
    print(f"[{issue.severity}] {issue.field}: {issue.message}")
```

---

## Data Flow

### Analysis Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         Stock Analysis Flow                               │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. INIT                                                                 │
│     └── Load config (stock_list, API keys, channels)                     │
│                                                                          │
│  2. DATA FETCH (per stock, parallel)                                     │
│     ├── Check checkpoint (has_today_data?)                               │
│     ├── Fetch from priority source (Efinance → Akshare → ...)            │
│     ├── Calculate technical indicators (MA5, MA10, MA20)                  │
│     ├── Save to database                                                 │
│     │                                                                    │
│     ├── Fetch realtime quote (volume_ratio, turnover_rate)               │
│     ├── Fetch chip distribution (profit_ratio, avg_cost)                 │
│     └── Search news (Tavily/SerpAPI)                                     │
│                                                                          │
│  3. ANALYSIS                                                             │
│     ├── Get context from database (today + yesterday comparison)         │
│     ├── Build prompt (decision dashboard format)                         │
│     ├── Call LLM (with fallback models)                                  │
│     └── Parse response → AnalysisResult                                  │
│                                                                          │
│  4. NOTIFICATION                                                         │
│     ├── Generate dashboard report (Markdown)                             │
│     ├── Save to file (reports/report_YYYYMMDD.md)                        │
│     └── Send to all configured channels                                  │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Task Queue Flow (Async Mode)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         Async Task Flow                                   │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Client                          Server                                  │
│    │                               │                                     │
│    │  POST /api/v1/analysis/analyze│                                     │
│    │  { stock_code, async_mode }   │                                     │
│    │──────────────────────────────>│                                     │
│    │                               │                                     │
│    │  202 { task_id, status }      │                                     │
│    │<──────────────────────────────│                                     │
│    │                               │                                     │
│    │  GET /api/v1/analysis/tasks/stream (SSE)                           │
│    │──────────────────────────────>│                                     │
│    │                               │                                     │
│    │  event: task_created          │  (task queued)                      │
│    │<──────────────────────────────│                                     │
│    │                               │                                     │
│    │  event: task_started          │  (worker picks up)                  │
│    │<──────────────────────────────│                                     │
│    │                               │                                     │
│    │  event: task_completed        │  (analysis done)                    │
│    │<──────────────────────────────│                                     │
│    │                               │                                     │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Configuration

### Environment Variables

#### LLM Configuration (3 Tiers)

```bash
# Tier 1: YAML Config (Recommended for multi-channel)
LITELLM_CONFIG=./litellm_config.yaml
LITELLM_MODEL=gemini/gemini-2.5-flash
LITELLM_FALLBACK_MODELS=anthropic/claude-3-5-sonnet,openai/gpt-4o

# Tier 2: Channel String
LLM_CHANNELS=gemini:KEY1,KEY2|anthropic:KEY3

# Tier 3: Legacy Keys
GEMINI_API_KEY=key1,key2,key3
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx
DEEPSEEK_API_KEY=sk-xxx
```

#### Data Sources

```bash
TUSHARE_TOKEN=xxx                    # Optional, higher priority when set
HTTP_PROXY=http://127.0.0.1:7890    # Optional, auto-excludes domestic sites
HTTPS_PROXY=http://127.0.0.1:7890
```

#### Real-time Data

```bash
ENABLE_REALTIME_QUOTE=true
ENABLE_CHIP_DISTRIBUTION=true
REALTIME_SOURCE_PRIORITY=tencent,akshare_sina,efinance
```

#### Notifications

```bash
# WeChat Work
WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx

# Feishu
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC
TELEGRAM_CHAT_ID=-100123456789

# Email
EMAIL_SENDER=your@email.com
EMAIL_PASSWORD=your-app-password
EMAIL_RECEIVERS=receiver1@email.com,receiver2@email.com

# Stock-to-email routing (Issue #268)
STOCK_GROUP_1=600519,000001
EMAIL_GROUP_1=alice@example.com,bob@example.com
```

#### Bot Configuration

```bash
BOT_ENABLED=true
BOT_COMMAND_PREFIX=/
BOT_RATE_LIMIT_REQUESTS=10
BOT_RATE_LIMIT_WINDOW=60

# Feishu Bot
FEISHU_APP_ID=cli_xxx
FEISHU_APP_SECRET=xxx
FEISHU_STREAM_ENABLED=true

# DingTalk Bot
DINGTALK_APP_KEY=xxx
DINGTALK_APP_SECRET=xxx
DINGTALK_STREAM_ENABLED=true
```

#### Scheduling

```bash
SCHEDULE_ENABLED=false
SCHEDULE_TIME=18:00
MARKET_REVIEW_ENABLED=true
MARKET_REVIEW_REGION=cn
TRADING_DAY_CHECK_ENABLED=true
```

### YAML Configuration (litellm_config.yaml)

```yaml
model_list:
  - model_name: gemini-flash
    litellm_params:
      model: gemini/gemini-2.5-flash
      api_key: env/GEMINI_API_KEY

  - model_name: claude-sonnet
    litellm_params:
      model: anthropic/claude-3-5-sonnet-20241022
      api_key: env/ANTHROPIC_API_KEY

router_settings:
  routing_strategy: simple-shuffle
```

---

## API Reference

### Base URL

```
http://localhost:8000/api/v1
```

### Endpoints

#### Analysis

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/analysis/analyze` | Trigger analysis (sync/async) |
| `GET` | `/analysis/tasks` | List tasks |
| `GET` | `/analysis/tasks/stream` | SSE task updates |
| `GET` | `/analysis/status/{task_id}` | Get task status |

#### Agent (Chat)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/agent/strategies` | List strategies |
| `POST` | `/agent/chat` | Chat with agent |
| `POST` | `/agent/chat/stream` | Stream chat (SSE) |
| `GET` | `/agent/chat/sessions` | List chat sessions |
| `DELETE` | `/agent/chat/sessions/{id}` | Delete session |

#### History

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/history` | List history (paginated) |
| `GET` | `/history/{query_id}` | Get detail |
| `GET` | `/history/{query_id}/news` | Get news intel |

#### System

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/system/config` | Get all config |
| `PUT` | `/system/config` | Update config |
| `POST` | `/system/config/reload` | Reload from env |

### Example Requests

```bash
# Trigger async analysis
curl -X POST http://localhost:8000/api/v1/analysis/analyze \
  -H "Content-Type: application/json" \
  -d '{"stock_code": "600519", "async_mode": true}'

# Get task status
curl http://localhost:8000/api/v1/analysis/status/{task_id}

# Chat with agent
curl -X POST http://localhost:8000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "用缠论分析茅台", "skills": ["chan_theory"]}'

# Update config
curl -X PUT http://localhost:8000/api/v1/system/config \
  -H "Content-Type: application/json" \
  -d '{"STOCK_LIST": "600519,000001,300750"}'
```

---

## Frontend Development

### Tech Stack

- **Framework**: React 19 + TypeScript
- **Build**: Vite
- **Routing**: React Router 6
- **State**: Zustand (global), useState (local)
- **Styling**: Tailwind CSS
- **HTTP**: Axios
- **Real-time**: Server-Sent Events (SSE)

### Development Server

```bash
cd apps/dsa-web
npm install
npm run dev
```

### Key Files

| File | Purpose |
|------|---------|
| `src/App.tsx` | Router + Auth + Navigation |
| `src/pages/HomePage.tsx` | Main analysis view |
| `src/pages/ChatPage.tsx` | AI strategy chat |
| `src/hooks/useTaskStream.ts` | SSE connection |
| `src/api/analysis.ts` | Analysis API client |
| `src/stores/analysisStore.ts` | Zustand store |

### Adding a New Page

1. Create page component in `src/pages/`:
```tsx
// src/pages/NewPage.tsx
import React from 'react';

const NewPage: React.FC = () => {
  return <div>New Page</div>;
};

export default NewPage;
```

2. Add route in `src/App.tsx`:
```tsx
import NewPage from './pages/NewPage';

// In Routes:
<Route path="/new" element={<NewPage />} />
```

3. Add navigation item:
```tsx
const NAV_ITEMS = [
  // ...
  { key: 'new', label: 'New', to: '/new', icon: NewIcon },
];
```

### SSE Hook Usage

```tsx
import { useTaskStream } from '../hooks';

const MyComponent = () => {
  const { isConnected } = useTaskStream({
    onTaskCreated: (task) => console.log('Created:', task),
    onTaskCompleted: (task) => console.log('Done:', task),
    onTaskFailed: (task) => console.error('Failed:', task),
    enabled: true,
  });

  return <div>Connected: {isConnected}</div>;
};
```

---

## Bot Development

### Architecture

```
bot/
├── models.py          # BotMessage, BotResponse, WebhookResponse
├── handler.py         # Webhook entry point
├── dispatcher.py      # Command routing + rate limiting
├── platforms/
│   ├── base.py        # BotPlatform abstract class
│   ├── dingtalk.py    # DingTalk adapter
│   ├── feishu_stream.py
│   └── discord.py
└── commands/
    ├── base.py        # BotCommand abstract class
    ├── analyze.py
    ├── help.py
    └── ...
```

### Adding a New Platform

1. Create adapter in `bot/platforms/`:
```python
# bot/platforms/my_platform.py
from bot.platforms.base import BotPlatform
from bot.models import BotMessage, BotResponse, WebhookResponse

class MyPlatform(BotPlatform):
    @property
    def platform_name(self) -> str:
        return "myplatform"

    def verify_request(self, headers, body) -> bool:
        # Verify webhook signature
        return True

    def parse_message(self, data) -> Optional[BotMessage]:
        # Parse platform message
        return BotMessage(
            platform="myplatform",
            message_id=data['id'],
            user_id=data['user_id'],
            # ...
        )

    def format_response(self, response, message) -> WebhookResponse:
        # Convert to platform format
        return WebhookResponse.success({
            "text": response.text
        })
```

2. Register in `bot/platforms/__init__.py`:
```python
from .my_platform import MyPlatform

ALL_PLATFORMS = {
    # ...
    "myplatform": MyPlatform,
}
```

### Adding a New Command

1. Create command in `bot/commands/`:
```python
# bot/commands/my_command.py
from bot.commands.base import BotCommand
from bot.models import BotMessage, BotResponse

class MyCommand(BotCommand):
    @property
    def name(self) -> str:
        return "mycommand"

    @property
    def aliases(self) -> list:
        return ["mc", "我的命令"]

    @property
    def description(self) -> str:
        return "我的自定义命令"

    @property
    def usage(self) -> str:
        return "/mycommand <参数>"

    def execute(self, message, args) -> BotResponse:
        return BotResponse.text_response("执行成功!")
```

2. Register in `bot/commands/__init__.py`:
```python
from .my_command import MyCommand

ALL_COMMANDS = [
    # ...
    MyCommand,
]
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific file
pytest tests/test_analyzer.py

# Run with coverage
pytest --cov=src --cov=api --cov=data_provider
```

### Writing Tests

```python
# tests/test_pipeline.py
import pytest
from src.core.pipeline import StockAnalysisPipeline
from src.config import Config

@pytest.fixture
def mock_config():
    return Config(
        stock_list=['600519'],
        gemini_api_keys=['test-key'],
    )

def test_pipeline_init(mock_config):
    pipeline = StockAnalysisPipeline(config=mock_config)
    assert pipeline.max_workers > 0

def test_normalize_stock_code():
    from data_provider.base import normalize_stock_code
    assert normalize_stock_code('SH600519') == '600519'
    assert normalize_stock_code('600519.SH') == '600519'
    assert normalize_stock_code('HK00700') == 'HK00700'
```

### Test Structure

```
tests/
├── conftest.py           # Fixtures
├── test_analyzer.py      # Analyzer tests
├── test_pipeline.py      # Pipeline tests
├── test_storage.py       # Storage tests
├── test_data_provider.py # Data fetcher tests
└── test_api/             # API tests
    ├── test_analysis.py
    └── test_history.py
```

---

## Deployment

### Docker

```bash
# Build image
docker build -f docker/Dockerfile -t stock-analysis .

# Run container
docker run -d \
  --name stock-analysis \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/.env:/app/.env \
  stock-analysis
```

### GitHub Actions (Scheduled)

The project includes GitHub Actions workflow for scheduled runs:

```yaml
# .github/workflows/scheduled_analysis.yml
name: Scheduled Analysis

on:
  schedule:
    - cron: '0 10 * * 1-5'  # 18:00 Beijing time (weekdays)
  workflow_dispatch:

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run analysis
        env:
          STOCK_LIST: ${{ secrets.STOCK_LIST }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          # ...
        run: |
          pip install -r requirements.txt
          python main.py
```

### Environment Variables for Production

```bash
# Required
STOCK_LIST=600519,000001,300750
GEMINI_API_KEY=xxx

# Recommended
WECHAT_WEBHOOK_URL=xxx
DATABASE_PATH=/data/stock_analysis.db

# Optional
TUSHARE_TOKEN=xxx
TAVILY_API_KEY=xxx
```

---

## Contributing

### Branch Naming

- `feature/xxx` - New features
- `fix/xxx` - Bug fixes
- `refactor/xxx` - Code refactoring
- `docs/xxx` - Documentation updates

### Commit Convention

```
feat: add support for new notification channel
fix: resolve duplicate task submission issue
refactor: extract common notification logic
docs: update deployment guide
test: add unit tests for analyzer
```

### Pull Request Process

1. Create feature branch from `main`
2. Make changes with tests
3. Run tests: `pytest`
4. Run linter: `ruff check .`
5. Submit PR with description

### Code Style

- Python: Follow PEP 8, use `ruff` for linting
- TypeScript: Follow Airbnb style guide
- Use type hints in Python
- Use TypeScript strict mode

---

## Troubleshooting

### Common Issues

#### 1. Data Fetch Fails

```bash
# Check data source availability
python -c "from data_provider import DataFetcherManager; m = DataFetcherManager(); print(m.available_fetchers)"

# Check proxy settings
echo $HTTP_PROXY
echo $NO_PROXY
```

#### 2. LLM API Errors

```bash
# Verify API key
python -c "from src.config import get_config; c = get_config(); print(c.gemini_api_keys)"

# Test LLM connection
python -c "
from src.analyzer import GeminiAnalyzer
a = GeminiAnalyzer()
print('Available:', a.is_available())
"
```

#### 3. Notification Not Sent

```bash
# Check configured channels
python -c "
from src.notification import NotificationService
n = NotificationService()
print('Available:', n.is_available())
print('Channels:', n.get_available_channels())
"
```

#### 4. Database Issues

```bash
# Check database
sqlite3 data/stock_analysis.db ".tables"
sqlite3 data/stock_analysis.db "SELECT COUNT(*) FROM stock_daily"
```

---

## Resources

- [LiteLLM Documentation](https://docs.litellm.ai/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Tailwind CSS](https://tailwindcss.com/)

---

*Last updated: 2024-01*
