# Tushare 数据源技术文档

> 本文档详细说明 Tushare 数据提供器的架构设计、API 集成、数据处理流程及配置方法。

## 📑 目录

- [概述](#概述)
- [架构设计](#架构设计)
- [API 能力](#api-能力)
- [数据处理流程](#数据处理流程)
- [速率限制与重试](#速率限制与重试)
- [优先级系统](#优先级系统)
- [实时行情系统](#实时行情系统)
- [缓存机制](#缓存机制)
- [配置说明](#配置说明)
- [错误处理](#错误处理)
- [数据库存储](#数据库存储)
- [最佳实践](#最佳实践)

---

## 概述

### 什么是 Tushare

[Tushare](https://tushare.pro) 是一个开放的金融数据接口，提供股票、基金、期货、外汇等金融产品的历史数据和实时数据。本系统通过 `TushareFetcher` 类集成 Tushare Pro API，作为多数据源策略中的可选数据源之一。

### 特点

| 特性 | 说明 |
|------|------|
| **数据质量** | 高质量、标准化的金融数据 |
| **接口稳定性** | 官方维护，接口稳定可靠 |
| **覆盖范围** | A股、ETF、指数、基金等 |
| **认证要求** | 需要 Token（免费用户可用） |
| **配额限制** | 免费用户 80 次/分钟，500 次/天 |

### 在系统中的定位

```
┌─────────────────────────────────────────────────────────────┐
│                    数据源优先级顺序                          │
├─────────────────────────────────────────────────────────────┤
│  Priority -1: TushareFetcher  ◄── 配置 Token 时最高优先级  │
│  Priority  0: EfinanceFetcher                              │
│  Priority  1: AkshareFetcher                               │
│  Priority  2: PytdxFetcher / TushareFetcher (无 Token)     │
│  Priority  3: BaostockFetcher                              │
│  Priority  4: YfinanceFetcher  ◄── 美股专用               │
└─────────────────────────────────────────────────────────────┘
```

---

## 架构设计

### 类结构

```
BaseFetcher (抽象基类)
    │
    ├── name: str              # 数据源名称
    ├── priority: int          # 优先级
    │
    ├── get_daily_data()       # 获取日线数据（统一入口）
    ├── _fetch_raw_data()      # 获取原始数据 [抽象]
    ├── _normalize_data()      # 标准化数据 [抽象]
    ├── _clean_data()          # 数据清洗
    ├── _calculate_indicators() # 计算技术指标
    │
    └── get_realtime_quote()   # 获取实时行情
    └── get_stock_name()       # 获取股票名称
    └── get_stock_list()       # 获取股票列表
    └── get_main_indices()     # 获取主要指数
    └── get_market_stats()     # 获取市场统计

        ▲
        │ 继承
        │
TushareFetcher
    │
    ├── _api: object           # Tushare API 实例
    ├── _call_count: int       # 当前分钟调用次数
    ├── _minute_start: float   # 计数周期开始时间
    ├── _stock_name_cache: dict # 股票名称缓存
    │
    ├── _init_api()            # 初始化 API
    ├── _patch_api_endpoint()  # 修复 API 端点
    ├── _determine_priority()  # 动态优先级
    ├── _check_rate_limit()    # 速率限制检查
    ├── _convert_stock_code()  # 代码格式转换
    └── ...                    # 其他方法实现
```

### 文件位置

```
data_provider/
├── __init__.py
├── base.py                    # 基类和管理器
├── tushare_fetcher.py         # Tushare 实现 ←── 本文档核心
├── realtime_types.py          # 实时行情类型定义
└── ...                        # 其他数据源
```

---

## API 能力

### 支持的 Tushare 接口

| 接口 | 方法 | 用途 | 返回字段 |
|------|------|------|----------|
| `daily()` | 日线数据 | A股历史行情 | ts_code, trade_date, open, high, low, close, pre_close, change, pct_chg, vol, amount |
| `fund_daily()` | 基金日线 | ETF历史行情 | 同 daily |
| `stock_basic()` | 股票基础 | 股票基本信息 | ts_code, name, industry, area, market |
| `fund_basic()` | 基金基础 | ETF基本信息 | ts_code, name |
| `quotation()` | Pro实时行情 | 实时行情(需2000积分) | price, pct_chg, vol, amount, pe, pb, total_mv, turnover_ratio |
| `get_realtime_quotes()` | 旧版实时 | 实时行情(免费) | price, pre_close, volume, amount, name |
| `index_daily()` | 指数日线 | 主要指数历史 | close, pre_close, change, pct_chg, open, high, low, vol, amount |
| `trade_cal()` | 交易日历 | 交易日查询 | cal_date, is_open |

### 支持的股票类型

#### A股股票

| 市场类型 | 代码前缀 | Tushare 格式 | 示例 |
|----------|----------|--------------|------|
| 沪市主板 | 600xxx, 601xxx, 603xxx | XXXXXX.SH | 600519.SH |
| 科创板 | 688xxx | XXXXXX.SH | 688981.SH |
| 深市主板 | 000xxx | XXXXXX.SZ | 000001.SZ |
| 中小板 | 002xxx | XXXXXX.SZ | 002594.SZ |
| 创业板 | 300xxx | XXXXXX.SZ | 300750.SZ |

#### ETF 基金

| 市场 | 代码前缀 | Tushare 格式 | 示例 |
|------|----------|--------------|------|
| 沪市 ETF | 51xxxx, 52xxxx, 56xxxx, 58xxxx | XXXXXX.SH | 510050.SH |
| 深市 ETF | 15xxxx, 16xxxx, 18xxxx | XXXXXX.SZ | 159919.SZ |

#### 主要指数

| 指数名称 | Tushare 代码 |
|----------|--------------|
| 上证指数 | 000001.SH |
| 深证成指 | 399001.SZ |
| 创业板指 | 399006.SZ |
| 科创50 | 000688.SH |
| 上证50 | 000016.SH |
| 沪深300 | 000300.SH |

#### 不支持的类型

- **美股**：如 AAPL, TSLA（请使用 YfinanceFetcher）
- **港股**：暂不支持（请使用 AkshareFetcher）

### 代码格式转换逻辑

```python
# 位置: tushare_fetcher.py:252-289

def _convert_stock_code(self, stock_code: str) -> str:
    """
    输入格式转换规则:

    '600519'     → '600519.SH'  # 沪市股票
    '000001'     → '000001.SZ'  # 深市股票
    '510050'     → '510050.SH'  # 沪市ETF
    '159919'     → '159919.SZ'  # 深市ETF
    '600519.SH'  → '600519.SH'  # 已有后缀，直接返回
    """
    code = stock_code.strip()

    # 已有后缀
    if '.' in code:
        return code.upper()

    # ETF 判断
    if code.startswith(('51', '52', '56', '58')) and len(code) == 6:
        return f"{code}.SH"  # 沪市ETF
    if code.startswith(('15', '16', '18')) and len(code) == 6:
        return f"{code}.SZ"  # 深市ETF

    # 普通股票
    if code.startswith(('600', '601', '603', '688')):
        return f"{code}.SH"  # 沪市
    elif code.startswith(('000', '002', '300')):
        return f"{code}.SZ"  # 深市
    else:
        return f"{code}.SZ"  # 默认深市
```

---

## 数据处理流程

### 完整流水线

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       Tushare 数据处理流水线                            │
└─────────────────────────────────────────────────────────────────────────┘

    用户请求
        │
        ▼
┌───────────────────┐
│  get_daily_data() │  ─── 统一入口 (BaseFetcher)
│   (BaseFetcher)   │
└─────────┬─────────┘
          │
          ▼
┌───────────────────────────────────────────────────────────────────────┐
│ Step 1: 速率限制检查                                                   │
│         _check_rate_limit()                                           │
│                                                                       │
│   • 检查当前分钟内的调用次数                                           │
│   • 超过 80 次则休眠到下一分钟                                         │
│   • 增加调用计数                                                       │
└───────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────────────────────────────────────────────────┐
│ Step 2: 股票代码转换                                                   │
│         _convert_stock_code()                                         │
│                                                                       │
│   600519 → 600519.SH                                                  │
│   159919 → 159919.SZ                                                  │
└───────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────────────────────────────────────────────────┐
│ Step 3: 调用 Tushare API                                              │
│         _fetch_raw_data()                                             │
│                                                                       │
│   • ETF: api.fund_daily(ts_code, start_date, end_date)               │
│   • 股票: api.daily(ts_code, start_date, end_date)                   │
│   • 自动重试 3 次（指数退避）                                          │
└───────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────────────────────────────────────────────────┐
│ Step 4: 数据标准化                                                     │
│         _normalize_data()                                             │
│                                                                       │
│   列名映射:                                                            │
│     trade_date → date                                                 │
│     vol → volume                                                      │
│                                                                       │
│   单位转换:                                                            │
│     volume: 手 → 股 (×100)                                            │
│     amount: 千元 → 元 (×1000)                                         │
│                                                                       │
│   日期格式:                                                            │
│     YYYYMMDD → YYYY-MM-DD                                             │
└───────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────────────────────────────────────────────────┐
│ Step 5: 数据清洗                                                       │
│         _clean_data() (BaseFetcher)                                   │
│                                                                       │
│   • 日期列转换为 datetime 类型                                         │
│   • 数值列类型转换                                                     │
│   • 移除空值行                                                         │
│   • 按日期升序排序                                                     │
└───────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────────────────────────────────────────────────┐
│ Step 6: 技术指标计算                                                   │
│         _calculate_indicators() (BaseFetcher)                         │
│                                                                       │
│   MA5  = close.rolling(5).mean()                                      │
│   MA10 = close.rolling(10).mean()                                     │
│   MA20 = close.rolling(20).mean()                                     │
│   Volume_Ratio = volume / avg_volume_5.shift(1)                       │
└───────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌───────────────────────────────────────────────────────────────────────┐
│ 输出: 标准化 DataFrame                                                 │
│                                                                       │
│   code | date | open | high | low | close | volume | amount | pct_chg│
│   ma5 | ma10 | ma20 | volume_ratio | data_source                    │
└───────────────────────────────────────────────────────────────────────┘
```

### 原始数据 vs 标准化数据

```
原始 Tushare 数据 (daily 接口返回):
┌───────────┬────────────┬──────┬──────┬───────┬───────┬────────┬─────────┬─────────┐
│ ts_code   │ trade_date │ open │ high │ low   │ close │ pre_cl │ pct_chg │ vol     │ amount  │
├───────────┼────────────┼──────┼──────┼───────┼───────┼────────┼─────────┼─────────┤
│ 600519.SH │ 20240315   │ 1750 │ 1780 │ 1745  │ 1775  │ 1730   │ 2.60    │ 25000   │ 450000  │
│           │            │      │      │       │       │        │         │ (手)    │ (千元)  │
└───────────┴────────────┴──────┴──────┴───────┴───────┴────────┴─────────┴─────────┘
                                        │
                                        ▼ _normalize_data()

标准化后数据:
┌────────┬────────────┬──────┬──────┬───────┬───────┬──────────┬───────────┬─────────┐
│ code   │ date       │ open │ high │ low   │ close │ pct_chg  │ volume    │ amount   │
├────────┼────────────┼──────┼──────┼───────┼───────┼──────────┼───────────┼─────────┤
│ 600519 │ 2024-03-15 │ 1750 │ 1780 │ 1745  │ 1775  │ 2.60     │ 2500000   │ 450000000│
│        │            │      │      │       │       │          │ (股)      │ (元)    │
└────────┴────────────┴──────┴──────┴───────┴───────┴──────────┴───────────┴─────────┘
```

---

## 速率限制与重试

### 速率限制机制

```python
# 位置: tushare_fetcher.py:210-250

class TushareFetcher:
    def __init__(self, rate_limit_per_minute: int = 80):
        """
        免费用户配额:
        - 每分钟最多 80 次请求
        - 每天最多 500 次请求
        """
        self.rate_limit_per_minute = rate_limit_per_minute
        self._call_count = 0           # 当前分钟调用次数
        self._minute_start = None      # 当前计数周期开始时间

    def _check_rate_limit(self):
        """
        流控状态机:

        ┌─────────────┐    60s     ┌─────────────┐
        │   COUNTING  │ ─────────► │    RESET    │
        │  count < 80 │            │  count = 0  │
        └──────┬──────┘            └──────┬──────┘
               │                          ▲
               │ count >= 80              │
               ▼                          │
        ┌─────────────┐                   │
        │  SLEEPING   │ ──────────────────┘
        │ sleep(60-t) │
        └─────────────┘
        """
        current_time = time.time()

        # 重置计数器（每分钟）
        if self._minute_start is None:
            self._minute_start = current_time
            self._call_count = 0
        elif current_time - self._minute_start >= 60:
            self._minute_start = current_time
            self._call_count = 0

        # 超过限制则休眠
        if self._call_count >= self.rate_limit_per_minute:
            elapsed = current_time - self._minute_start
            sleep_time = max(0, 60 - elapsed) + 1  # +1秒缓冲
            logger.warning(f"速率限制触发，休眠 {sleep_time:.1f}s...")
            time.sleep(sleep_time)
            self._minute_start = time.time()
            self._call_count = 0

        self._call_count += 1
```

### 重试机制

```python
# 位置: tushare_fetcher.py:291-296

@retry(
    stop=stop_after_attempt(3),                          # 最多重试 3 次
    wait=wait_exponential(multiplier=1, min=2, max=30), # 指数退避: 2s → 4s → 8s
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
def _fetch_raw_data(self, stock_code: str, start_date: str, end_date: str):
    ...

# 重试时间线:
# 尝试 1 ──► 失败 ──► 等待 2s
# 尝试 2 ──► 失败 ──► 等待 4s
# 尝试 3 ──► 失败 ──► 抛出 DataFetchError
```

### API 端点修复

Tushare SDK v1.4.x 默认使用 `api.waditu.com/dataapi` 端点，该端点可能返回 503 错误。系统通过 Monkey Patch 修复此问题：

```python
# 位置: tushare_fetcher.py:144-178

def _patch_api_endpoint(self, token: str):
    """
    修复 Tushare SDK 端点问题

    原始 SDK 行为:
      POST http://api.waditu.com/dataapi/{api_name}  ← 可能 503

    修复后行为:
      POST http://api.tushare.pro  ← 官方稳定端点
    """
    TUSHARE_API_URL = "http://api.tushare.pro"

    def patched_query(self_api, api_name, fields='', **kwargs):
        req_params = {
            'api_name': api_name,
            'token': token,
            'params': kwargs,
            'fields': fields,
        }
        res = requests.post(TUSHARE_API_URL, json=req_params, timeout=30)
        # ... 处理响应 ...

    self._api.query = types.MethodType(patched_query, self._api)
```

---

## 优先级系统

### 动态优先级分配

```python
# 位置: tushare_fetcher.py:180-199

def _determine_priority(self) -> int:
    """
    优先级逻辑:

    ┌─────────────────────────────────────────────────────────┐
    │                    Token 状态                           │
    ├─────────────────────────────────────────────────────────┤
    │                                                         │
    │   TUSHARE_TOKEN 已配置 且 API 初始化成功?              │
    │                      │                                  │
    │           ┌──────────┴──────────┐                      │
    │           ▼                     ▼                      │
    │         [是]                  [否]                     │
    │           │                     │                      │
    │           ▼                     ▼                      │
    │   Priority: -1           Priority: 2                   │
    │   (最高优先级)           (默认优先级)                  │
    │                                                         │
    └─────────────────────────────────────────────────────────┘
    """
    config = get_config()

    if config.tushare_token and self._api is not None:
        logger.info("✅ TUSHARE_TOKEN 已配置，优先级提升为 -1 (最高)")
        return -1

    return 2
```

### 实时行情优先级自动注入

```python
# 位置: src/config.py:943-970

@classmethod
def _resolve_realtime_source_priority(cls) -> str:
    """
    当配置了 TUSHARE_TOKEN 但未显式设置 REALTIME_SOURCE_PRIORITY 时，
    自动将 tushare 加入优先级列表首位。
    """
    explicit = os.getenv('REALTIME_SOURCE_PRIORITY')
    if explicit:
        return explicit  # 尊重用户显式配置

    if os.getenv('TUSHARE_TOKEN'):
        # Token 已配置，自动注入 tushare 到首位
        return f'tushare,tencent,akshare_sina,efinance,akshare_em'

    return 'tencent,akshare_sina,efinance,akshare_em'  # 默认
```

---

## 实时行情系统

### 双接口策略

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       实时行情获取策略                                   │
└─────────────────────────────────────────────────────────────────────────┘

    get_realtime_quote(stock_code)
              │
              ▼
    ┌─────────────────────────────────────┐
    │ Step 1: 尝试 Pro 接口               │
    │         api.quotation()             │
    │                                     │
    │   要求: 2000+ Tushare 积分          │
    │   返回: 完整数据 (价格、量比、PE等) │
    └──────────────────┬──────────────────┘
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
          [成功]              [失败]
             │                   │
             ▼                   ▼
          返回结果    ┌─────────────────────────────────────┐
                      │ Step 2: 降级到旧版接口             │
                      │         ts.get_realtime_quotes()  │
                      │                                     │
                      │   要求: 免费可用                   │
                      │   返回: 基础数据 (价格、成交量)   │
                      └──────────────────┬──────────────────┘
                                         │
                               ┌─────────┴─────────┐
                               ▼                   ▼
                            [成功]              [失败]
                               │                   │
                               ▼                   ▼
                            返回结果           返回 None
```

### 接口对比

| 特性 | Pro 接口 (`quotation`) | 旧版接口 (`get_realtime_quotes`) |
|------|------------------------|----------------------------------|
| **积分要求** | 2000+ | 免费可用 |
| **最新价** | ✅ | ✅ |
| **涨跌幅** | ✅ | ✅ |
| **成交量/额** | ✅ | ✅ |
| **量比** | ✅ | ❌ |
| **换手率** | ✅ | ❌ |
| **PE/PB** | ✅ | ❌ |
| **市值** | ✅ | ❌ |
| **稳定性** | 高 | 较低 |

### 统一数据结构

```python
# 位置: data_provider/realtime_types.py:106-176

@dataclass
class UnifiedRealtimeQuote:
    """统一实时行情数据结构"""

    # 身份信息
    code: str                                    # 股票代码
    name: str = ""                               # 股票名称
    source: RealtimeSource = RealtimeSource.TUSHARE

    # 核心价格 (Pro + 旧版)
    price: Optional[float] = None               # 最新价
    change_pct: Optional[float] = None          # 涨跌幅(%)
    change_amount: Optional[float] = None       # 涨跌额

    # 量价指标
    volume: Optional[int] = None                # 成交量(手)
    amount: Optional[float] = None              # 成交额(元)
    volume_ratio: Optional[float] = None        # 量比 (Pro)
    turnover_rate: Optional[float] = None       # 换手率 (Pro)

    # 价格区间
    open_price: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    pre_close: Optional[float] = None

    # 估值指标 (Pro)
    pe_ratio: Optional[float] = None            # 市盈率
    pb_ratio: Optional[float] = None            # 市净率
    total_mv: Optional[float] = None            # 总市值
```

---

## 缓存机制

### 股票名称缓存

```python
# 位置: tushare_fetcher.py:404-456

class TushareFetcher:
    def get_stock_name(self, stock_code: str) -> Optional[str]:
        """
        内存缓存策略:

        ┌─────────────────────────────────────────────────────────┐
        │                                                         │
        │   1. 检查 _stock_name_cache (内存字典)                 │
        │              │                                          │
        │      ┌───────┴───────┐                                 │
        │      ▼               ▼                                 │
        │   [命中]           [未命中]                            │
        │      │               │                                 │
        │      ▼               ▼                                 │
        │   返回缓存值      调用 API                             │
        │                   stock_basic()                       │
        │                   或 fund_basic()                     │
        │                       │                               │
        │                       ▼                               │
        │                   缓存结果                            │
        │                   返回名称                            │
        │                                                         │
        └─────────────────────────────────────────────────────────┘
        """
        # 检查缓存
        if hasattr(self, '_stock_name_cache') and stock_code in self._stock_name_cache:
            return self._stock_name_cache[stock_code]

        # 初始化缓存
        if not hasattr(self, '_stock_name_cache'):
            self._stock_name_cache = {}

        # 调用 API 获取
        ts_code = self._convert_stock_code(stock_code)
        if _is_etf_code(stock_code):
            df = self._api.fund_basic(ts_code=ts_code, fields='ts_code,name')
        else:
            df = self._api.stock_basic(ts_code=ts_code, fields='ts_code,name')

        # 缓存并返回
        if df is not None and not df.empty:
            name = df.iloc[0]['name']
            self._stock_name_cache[stock_code] = name
            return name

        return None
```

### 全局缓存配置

```python
# 位置: src/config.py

realtime_cache_ttl: int = 600  # 实时行情缓存时间: 10 分钟
```

---

## 配置说明

### 环境变量

```bash
# .env 文件配置

# Tushare API Token (必需)
TUSHARE_TOKEN=your_token_here

# 速率限制 (可选，默认: 80)
TUSHARE_RATE_LIMIT_PER_MINUTE=80

# 优先级覆盖 (可选)
TUSHARE_PRIORITY=-1

# 实时行情数据源优先级 (可选)
# 当配置了 TUSHARE_TOKEN 时，系统会自动将 tushare 加入优先级
REALTIME_SOURCE_PRIORITY=tushare,tencent,akshare_sina,efinance
```

### 获取 Tushare Token

1. 访问 [Tushare Pro](https://tushare.pro)
2. 注册并登录
3. 进入"个人中心" → "接口Token"
4. 复制 Token 到 `.env` 文件

### 配置类集成

```python
# 位置: src/config.py

@dataclass
class Config:
    # Tushare Token
    tushare_token: Optional[str] = None  # 从 TUSHARE_TOKEN 环境变量读取

    # 速率限制
    tushare_rate_limit_per_minute: int = 80  # 免费用户配额

    # 实时行情优先级
    realtime_source_priority: str = "tencent,akshare_sina,efinance,akshare_em"
    # 当 TUSHARE_TOKEN 配置时，自动变为:
    # "tushare,tencent,akshare_sina,efinance,akshare_em"
```

---

## 错误处理

### 异常层次结构

```python
# 位置: data_provider/base.py:96-108

class DataFetchError(Exception):
    """数据获取异常基类"""
    pass

class RateLimitError(DataFetchError):
    """API 速率限制异常"""
    pass

class DataSourceUnavailableError(DataFetchError):
    """数据源不可用异常"""
    pass
```

### 错误检测逻辑

```python
# 位置: tushare_fetcher.py:351-359

def _fetch_raw_data(self, ...):
    try:
        # ... API 调用 ...
    except Exception as e:
        error_msg = str(e).lower()

        # 检测配额超限
        if any(keyword in error_msg for keyword in ['quota', '配额', 'limit', '权限']):
            logger.warning(f"Tushare 配额可能超限: {e}")
            raise RateLimitError(f"Tushare 配额超限: {e}") from e

        raise DataFetchError(f"Tushare 获取数据失败: {e}") from e
```

### 故障切换

当 Tushare 失败时，系统自动切换到下一个数据源：

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       故障切换流程                                       │
└─────────────────────────────────────────────────────────────────────────┘

[TushareFetcher] 尝试获取数据
        │
        ▼
    ┌───────┐
    │ 成功? │
    └───┬───┘
        │
   ┌────┴────┐
   ▼         ▼
 [是]      [否]
   │         │
   ▼         ▼
 返回结果  记录错误
           │
           ▼
    切换到下一个数据源
    (EfinanceFetcher)
           │
           ▼
        ┌───────┐
        │ 成功? │
        └───┬───┘
           ...
           │
           ▼
    所有数据源失败
           │
           ▼
    抛出 DataFetchError
```

---

## 数据库存储

### 数据表结构

```sql
-- 股票日线数据表
CREATE TABLE stock_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(10) NOT NULL,           -- 股票代码
    date DATE NOT NULL,                  -- 交易日期
    open FLOAT,                          -- 开盘价
    high FLOAT,                          -- 最高价
    low FLOAT,                           -- 最低价
    close FLOAT,                         -- 收盘价
    volume FLOAT,                        -- 成交量(股)
    amount FLOAT,                        -- 成交额(元)
    pct_chg FLOAT,                       -- 涨跌幅(%)
    ma5 FLOAT,                           -- 5日均线
    ma10 FLOAT,                          -- 10日均线
    ma20 FLOAT,                          -- 20日均线
    volume_ratio FLOAT,                  -- 量比
    data_source VARCHAR(50),             -- 数据来源
    created_at DATETIME,                 -- 创建时间
    updated_at DATETIME,                 -- 更新时间
    CONSTRAINT uix_code_date UNIQUE (code, date)
);

CREATE INDEX ix_code_date ON stock_daily(code, date);
CREATE INDEX ix_stock_daily_code ON stock_daily(code);
CREATE INDEX ix_stock_daily_date ON stock_daily(date);
```

### ORM 模型

```python
# 位置: src/storage.py:62-131

class StockDaily(Base):
    """股票日线数据模型"""
    __tablename__ = 'stock_daily'

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    # OHLC 数据
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)

    # 成交数据
    volume = Column(Float)    # 成交量（股）
    amount = Column(Float)    # 成交额（元）
    pct_chg = Column(Float)   # 涨跌幅（%）

    # 技术指标
    ma5 = Column(Float)
    ma10 = Column(Float)
    ma20 = Column(Float)
    volume_ratio = Column(Float)

    # 数据来源
    data_source = Column(String(50))

    # 时间戳
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        UniqueConstraint('code', 'date', name='uix_code_date'),
        Index('ix_code_date', 'code', 'date'),
    )
```

---

## 最佳实践

### 1. Token 配置建议

```bash
# 推荐：生产环境配置 Tushare Token
TUSHARE_TOKEN=your_token_here

# 原因：
# - 提升优先级到最高 (-1)
# - 获取更高质量的金融数据
# - 支持更多 API 接口
```

### 2. 速率限制管理

```python
# 对于批量获取场景，建议控制并发

# 不推荐：大量并发请求
for code in stock_codes:
    fetcher.get_daily_data(code)  # 可能触发速率限制

# 推荐：分批获取 + 延迟
import time
for i, code in enumerate(stock_codes):
    fetcher.get_daily_data(code)
    if i % 70 == 0:  # 每获取 70 条后暂停
        time.sleep(60)
```

### 3. 错误处理

```python
from data_provider.base import DataFetchError, RateLimitError

try:
    df, source = manager.get_daily_data('600519')
except RateLimitError:
    logger.warning("Tushare 配额已用尽，使用其他数据源")
    # 系统会自动切换到下一个数据源
except DataFetchError as e:
    logger.error(f"所有数据源均失败: {e}")
```

### 4. 缓存利用

```python
# 利用股票名称缓存
fetcher = TushareFetcher()

# 首次调用会请求 API
name1 = fetcher.get_stock_name('600519')  # API 调用

# 后续调用使用缓存
name2 = fetcher.get_stock_name('600519')  # 缓存命中
```

### 5. 实时行情优先级

```bash
# 推荐：Tushare 用户配置
REALTIME_SOURCE_PRIORITY=tushare,tencent,akshare_sina

# 原因：
# - tushare: 数据最全（需要积分）
# - tencent: 稳定，有量比/换手率
# - akshare_sina: 基础行情稳定
```

---

## 参考资料

- [Tushare Pro 官方文档](https://tushare.pro/document/2)
- [Tushare 积分规则](https://tushare.pro/document/1)
- [项目 README](../README.md)
- [完整配置指南](./full-guide.md)
