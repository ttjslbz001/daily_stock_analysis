# 关注股票功能实施计划

## 项目概述

在主页中添加"我关注的股票"功能模块，支持用户添加、删除关注股票，并显示实时价格和技术指标（布林线、MACD、RSI）。

**创建日期**: 2026-03-15
**优先级**: 高
**预计工期**: 2-3小时

## 技术架构

### 后端 (Python + FastAPI)
- 数据库: SQLite (现有)
- 用户管理: 固定用户 ID 'default_user'
- 技术指标计算: 复用 `StockTrendAnalyzer` 类

### 前端 (React + TypeScript)
- UI 框架: Tailwind CSS
- 状态管理: Zustand
- HTTP 客户端: 现有 API 封装

## 实施任务

### Phase 1: 数据库层 (10分钟)

#### 1.1 创建数据库表
- [ ] 创建 `watched_stocks` 表迁移脚本
- [ ] 添加表结构 (id, user_id, stock_code, stock_name, created_at, updated_at)
- [ ] 添加唯一索引 (user_id, stock_code)

**文件**: `src/repositories/watched_stocks_repo.py`
```python
from dataclasses import dataclass
from typing import List, Optional
import sqlite3
from datetime import datetime

@dataclass
class WatchedStock:
    id: int
    user_id: str
    stock_code: str
    stock_name: Optional[str]
    created_at: datetime
    updated_at: datetime

class WatchedStocksRepository:
    def __init__(self, db_path: str = "data/stocks.db"):
        self.db_path = db_path
        self._init_table()

    def _init_table(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS watched_stocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id VARCHAR(50) NOT NULL DEFAULT 'default_user',
                    stock_code VARCHAR(20) NOT NULL,
                    stock_name VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, stock_code)
                )
            """)
            conn.commit()

    def add(self, user_id: str, stock_code: str, stock_name: str = None) -> bool
    def remove(self, user_id: str, stock_code: str) -> bool
    def list(self, user_id: str) -> List[WatchedStock]
    def exists(self, user_id: str, stock_code: str) -> bool
```

#### 1.2 运行迁移
```bash
python -c "from src.repositories.watched_stocks_repo import WatchedStocksRepository; WatchedStocksRepository()"
```

---

### Phase 2: 后端核心逻辑 (30分钟)

#### 2.1 添加布林线计算方法
- [ ] 在 `StockTrendAnalyzer` 类中添加 `_calculate_bollinger` 方法

**文件**: `src/stock_analyzer.py`
```python
def _calculate_bollinger(self, df: pd.DataFrame, period: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    """
    计算布林线指标

    参数:
        period: 周期（默认20日）
        num_std: 标准差倍数（默认2.0）

    返回:
        添加 BB_UPPER, BB_MIDDLE, BB_LOWER 列的 DataFrame
    """
    df = df.copy()
    df['BB_MIDDLE'] = df['close'].rolling(window=period).mean()
    df['BB_STD'] = df['close'].rolling(window=period).std()
    df['BB_UPPER'] = df['BB_MIDDLE'] + (df['BB_STD'] * num_std)
    df['BB_LOWER'] = df['BB_MIDDLE'] - (df['BB_STD'] * num_std)
    return df

def _analyze_bollinger(self, df: pd.DataFrame, result: TrendAnalysisResult) -> None:
    """
    分析布林线指标并更新结果
    """
    latest = df.iloc[-1]
    result.bollinger_upper = float(latest['BB_UPPER'])
    result.bollinger_middle = float(latest['BB_MIDDLE'])
    result.bollinger_lower = float(latest['BB_LOWER'])
```

#### 2.2 更新 TrendAnalysisResult 数据类
- [ ] 添加布林线字段

**文件**: `src/stock_analyzer.py`
```python
@dataclass
class TrendAnalysisResult:
    # ... 现有字段 ...
    # 布林线指标
    bollinger_upper: float = 0.0
    bollinger_middle: float = 0.0
    bollinger_lower: float = 0.0
```

#### 2.3 创建技术指标服务
- [ ] 创建 `TechnicalIndicatorsService` 类
- [ ] 实现批量获取股票技术指标的方法

**文件**: `src/services/technical_indicators_service.py`
```python
from typing import List, Dict, Any
from src.stock_analyzer import StockTrendAnalyzer
from src.data_fetcher import DataFetcher

class TechnicalIndicatorsService:
    def __init__(self):
        self.analyzer = StockTrendAnalyzer()
        self.fetcher = DataFetcher()

    def get_indicators(self, stock_codes: List[str]) -> Dict[str, Any]:
        """
        批量获取股票技术指标

        返回: {stock_code: indicators_dict}
        """
        results = {}
        for code in stock_codes:
            df = self.fetcher.get_stock_data(code, period='3mo')
            if df is not None and not df.empty:
                result = self.analyzer.analyze(df, code)
                results[code] = {
                    'price': result.current_price,
                    'change': 0,  # 需从实时行情获取
                    'change_percent': 0,
                    'bollinger': {
                        'upper': result.bollinger_upper,
                        'middle': result.bollinger_middle,
                        'lower': result.bollinger_lower
                    },
                    'macd': {
                        'dif': result.macd_dif,
                        'dea': result.macd_dea,
                        'bar': result.macd_bar
                    },
                    'rsi': {
                        'rsi6': result.rsi_6,
                        'rsi12': result.rsi_12,
                        'rsi24': result.rsi_24
                    }
                }
        return results

    def get_quote(self, stock_code: str) -> Dict[str, Any]:
        """
        获取实时行情数据
        """
        # 调用现有的行情 API
        pass
```

---

### Phase 3: 后端 API (20分钟)

#### 3.1 创建 Pydantic 模型
- [ ] 创建请求和响应模型

**文件**: `api/v1/schemas/watched_stocks.py`
```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class WatchedStockResponse(BaseModel):
    stock_code: str
    stock_name: str
    current_price: float
    change: float
    change_percent: float
    bollinger: dict
    macd: dict
    rsi: dict
    updated_at: datetime

class WatchedStocksListResponse(BaseModel):
    total: int
    items: List[WatchedStockResponse]

class AddWatchedStockRequest(BaseModel):
    stock_code: str

class AddWatchedStockResponse(BaseModel):
    success: bool
    message: str
    stock_code: str

class RemoveWatchedStockResponse(BaseModel):
    success: bool
    message: str
    stock_code: str
```

#### 3.2 创建 API 路由
- [ ] 实现 GET /api/v1/watched
- [ ] 实现 POST /api/v1/watched
- [ ] 实现 DELETE /api/v1/watched/{stock_code}

**文件**: `api/v1/endpoints/watched_stocks.py`
```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from src.repositories.watched_stocks_repo import WatchedStocksRepository
from src.services.technical_indicators_service import TechnicalIndicatorsService
from .schemas.watched_stocks import (
    WatchedStockResponse,
    WatchedStocksListResponse,
    AddWatchedStockRequest,
    AddWatchedStockResponse,
    RemoveWatchedStockResponse
)

router = APIRouter(prefix="/api/v1/watched", tags=["WatchedStocks"])

DEFAULT_USER_ID = "default_user"

@router.get("", response_model=WatchedStocksListResponse)
async def get_watched_stocks():
    """获取关注股票列表"""
    repo = WatchedStocksRepository()
    indicator_service = TechnicalIndicatorsService()

    watched = repo.list(DEFAULT_USER_ID)
    stock_codes = [ws.stock_code for ws in watched]

    if not stock_codes:
        return WatchedStocksListResponse(total=0, items=[])

    # 批量获取技术指标
    indicators = indicator_service.get_indicators(stock_codes)

    # 构建响应
    items = []
    for ws in watched:
        code = ws.stock_code
        data = indicators.get(code, {})
        items.append(WatchedStockResponse(
            stock_code=code,
            stock_name=ws.stock_name or code,
            current_price=data.get('price', 0),
            change=data.get('change', 0),
            change_percent=data.get('change_percent', 0),
            bollinger=data.get('bollinger', {}),
            macd=data.get('macd', {}),
            rsi=data.get('rsi', {}),
            updated_at=ws.updated_at
        ))

    return WatchedStocksListResponse(total=len(items), items=items)

@router.post("", response_model=AddWatchedStockResponse)
async def add_watched_stock(request: AddWatchedStockRequest):
    """添加关注股票"""
    repo = WatchedStocksRepository()

    if repo.exists(DEFAULT_USER_ID, request.stock_code):
        return AddWatchedStockResponse(
            success=False,
            message="股票已在关注列表中",
            stock_code=request.stock_code
        )

    success = repo.add(DEFAULT_USER_ID, request.stock_code)
    if success:
        return AddWatchedStockResponse(
            success=True,
            message="添加成功",
            stock_code=request.stock_code
        )
    else:
        raise HTTPException(status_code=500, detail="添加失败")

@router.delete("/{stock_code}", response_model=RemoveWatchedStockResponse)
async def remove_watched_stock(stock_code: str):
    """取消关注股票"""
    repo = WatchedStocksRepository()
    success = repo.remove(DEFAULT_USER_ID, stock_code)

    if success:
        return RemoveWatchedStockResponse(
            success=True,
            message="取消关注成功",
            stock_code=stock_code
        )
    else:
        raise HTTPException(status_code=404, detail="股票不在关注列表中")
```

#### 3.3 注册路由
- [ ] 在 `api/app.py` 中注册路由

---

### Phase 4: 前端类型定义 (10分钟)

#### 4.1 创建 TypeScript 类型
- [ ] 创建 watched stocks 类型定义

**文件**: `apps/dsa-web/src/types/watchedStocks.ts`
```typescript
export interface BollingerBands {
  upper: number;
  middle: number;
  lower: number;
}

export interface MACD {
  dif: number;
  dea: number;
  bar: number;
}

export interface RSI {
  rsi6: number;
  rsi12: number;
  rsi24: number;
}

export interface WatchedStock {
  stock_code: string;
  stock_name: string;
  current_price: number;
  change: number;
  change_percent: number;
  bollinger: BollingerBands;
  macd: MACD;
  rsi: RSI;
  updated_at: string;
}

export interface WatchedStocksListResponse {
  total: number;
  items: WatchedStock[];
}

export interface AddWatchedStockRequest {
  stock_code: string;
}

export interface AddWatchedStockResponse {
  success: boolean;
  message: string;
  stock_code: string;
}

export interface RemoveWatchedStockResponse {
  success: boolean;
  message: string;
  stock_code: string;
}
```

---

### Phase 5: 前端 API 服务 (10分钟)

#### 5.1 创建 API 客户端
- [ ] 实现 API 调用方法

**文件**: `apps/dsa-web/src/api/watchedStocks.ts`
```typescript
import api from './index';
import {
  WatchedStock,
  WatchedStocksListResponse,
  AddWatchedStockRequest,
  AddWatchedStockResponse,
  RemoveWatchedStockResponse
} from '../types/watchedStocks';

export const watchedStocksApi = {
  getWatchedStocks: async (): Promise<WatchedStocksListResponse> => {
    const response = await api.get<WatchedStocksListResponse>('/api/v1/watched');
    return response.data;
  },

  addWatchedStock: async (
    request: AddWatchedStockRequest
  ): Promise<AddWatchedStockResponse> => {
    const response = await api.post<AddWatchedStockResponse>(
      '/api/v1/watched',
      request
    );
    return response.data;
  },

  removeWatchedStock: async (
    stockCode: string
  ): Promise<RemoveWatchedStockResponse> => {
    const response = await api.delete<RemoveWatchedStockResponse>(
      `/api/v1/watched/${stockCode}`
    );
    return response.data;
  }
};
```

#### 5.2 导出 API
- [ ] 在 `apps/dsa-web/src/api/index.ts` 中导出

---

### Phase 6: 前端组件 (40分钟)

#### 6.1 创建 WatchedStockCard 组件
- [ ] 创建单个股票卡片组件
- [ ] 显示价格、涨跌幅、技术指标

**文件**: `apps/dsa-web/src/components/watchedStocks/WatchedStockCard.tsx`
```typescript
import React from 'react';
import { WatchedStock } from '../../types/watchedStocks';
import { formatPrice, formatPercent } from '../../utils/format';

interface WatchedStockCardProps {
  stock: WatchedStock;
  onRemove: (code: string) => void;
}

export const WatchedStockCard: React.FC<WatchedStockCardProps> = ({
  stock,
  onRemove
}) => {
  const isPositive = stock.change >= 0;

  return (
    <div className="bg-white rounded-lg shadow-md p-4 border border-gray-200">
      {/* 股票基本信息 */}
      <div className="flex justify-between items-start mb-3">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            {stock.stock_name}
          </h3>
          <p className="text-sm text-gray-500">{stock.stock_code}</p>
        </div>
        <button
          onClick={() => onRemove(stock.stock_code)}
          className="text-gray-400 hover:text-red-500 transition-colors"
          title="取消关注"
        >
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </button>
      </div>

      {/* 价格信息 */}
      <div className="mb-4">
        <div className="text-2xl font-bold text-gray-900">
          {formatPrice(stock.current_price)}
        </div>
        <div
          className={`text-sm font-medium ${
            isPositive ? 'text-red-500' : 'text-green-500'
          }`}
        >
          {isPositive ? '+' : ''}
          {formatPrice(stock.change)}
          {' '}
          {isPositive ? '+' : ''}
          {formatPercent(stock.change_percent)}%
        </div>
      </div>

      {/* 技术指标 */}
      <div className="space-y-2">
        {/* 布林线 */}
        <div className="bg-gray-50 rounded p-2">
          <div className="text-xs text-gray-500 mb-1">布林线</div>
          <div className="flex justify-between text-xs">
            <span className="text-red-400">上轨: {formatPrice(stock.bollinger.upper)}</span>
            <span className="text-gray-600">中轨: {formatPrice(stock.bollinger.middle)}</span>
            <span className="text-green-400">下轨: {formatPrice(stock.bollinger.lower)}</span>
          </div>
        </div>

        {/* MACD */}
        <div className="bg-gray-50 rounded p-2">
          <div className="text-xs text-gray-500 mb-1">MACD</div>
          <div className="flex justify-between text-xs">
            <span>DIF: {stock.macd.dif.toFixed(4)}</span>
            <span>DEA: {stock.macd.dea.toFixed(4)}</span>
            <span className={stock.macd.bar >= 0 ? 'text-red-400' : 'text-green-400'}>
              MACD: {stock.macd.bar.toFixed(4)}
            </span>
          </div>
        </div>

        {/* RSI */}
        <div className="bg-gray-50 rounded p-2">
          <div className="text-xs text-gray-500 mb-1">RSI</div>
          <div className="flex justify-between text-xs">
            <span>RSI(6): {stock.rsi.rsi6.toFixed(1)}</span>
            <span>RSI(12): {stock.rsi.rsi12.toFixed(1)}</span>
            <span>RSI(24): {stock.rsi.rsi24.toFixed(1)}</span>
          </div>
        </div>
      </div>

      {/* 更新时间 */}
      <div className="mt-3 text-xs text-gray-400 text-right">
        更新于 {new Date(stock.updated_at).toLocaleString('zh-CN')}
      </div>
    </div>
  );
};
```

#### 6.2 创建 WatchedStocksPanel 组件
- [ ] 创建主面板组件
- [ ] 添加刷新和添加股票功能

**文件**: `apps/dsa-web/src/components/watchedStocks/WatchedStocksPanel.tsx`
```typescript
import React, { useState, useEffect } from 'react';
import { watchedStocksApi } from '../../api/watchedStocks';
import { WatchedStock } from '../../types/watchedStocks';
import { WatchedStockCard } from './WatchedStockCard';
import { Loading } from '../common/Loading';

export const WatchedStocksPanel: React.FC = () => {
  const [stocks, setStocks] = useState<WatchedStock[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStocks = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await watchedStocksApi.getWatchedStocks();
      setStocks(response.items);
    } catch (err) {
      setError('获取关注股票失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStocks();
  }, []);

  const handleRemove = async (stockCode: string) => {
    try {
      await watchedStocksApi.removeWatchedStock(stockCode);
      setStocks(stocks.filter(s => s.stock_code !== stockCode));
    } catch (err) {
      console.error('取消关注失败:', err);
      alert('取消关注失败');
    }
  };

  const handleRefresh = () => {
    fetchStocks();
  };

  const handleAddStock = () => {
    // TODO: 实现添加股票对话框
    const stockCode = prompt('请输入股票代码（如 600519）');
    if (stockCode) {
      addStock(stockCode);
    }
  };

  const addStock = async (stockCode: string) => {
    try {
      const response = await watchedStocksApi.addWatchedStock({ stock_code: stockCode });
      if (response.success) {
        await fetchStocks();
      } else {
        alert(response.message);
      }
    } catch (err) {
      console.error('添加关注失败:', err);
      alert('添加关注失败');
    }
  };

  if (loading) {
    return <Loading />;
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg">
        {error}
      </div>
    );
  }

  return (
    <div className="bg-gray-50 rounded-lg">
      {/* 标题栏 */}
      <div className="flex justify-between items-center p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">
          我关注的股票
        </h2>
        <div className="flex gap-2">
          <button
            onClick={handleRefresh}
            className="px-3 py-1.5 text-sm bg-white border border-gray-300 rounded hover:bg-gray-50"
          >
            刷新
          </button>
          <button
            onClick={handleAddStock}
            className="px-3 py-1.5 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            添加
          </button>
        </div>
      </div>

      {/* 内容区 */}
      {stocks.length === 0 ? (
        <div className="p-8 text-center text-gray-500">
          暂无关注股票，点击"添加"按钮添加
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
          {stocks.map(stock => (
            <WatchedStockCard
              key={stock.stock_code}
              stock={stock}
              onRemove={handleRemove}
            />
          ))}
        </div>
      )}
    </div>
  );
};
```

#### 6.3 创建组件导出文件
**文件**: `apps/dsa-web/src/components/watchedStocks/index.ts`
```typescript
export { WatchedStocksPanel } from './WatchedStocksPanel';
export { WatchedStockCard } from './WatchedStockCard';
```

---

### Phase 7: 集成到主页 (10分钟)

#### 7.1 修改 HomePage 组件
- [ ] 在 HomePage 中添加 WatchedStocksPanel

**文件**: `apps/dsa-web/src/pages/HomePage.tsx`
```typescript
import { WatchedStocksPanel } from '../components/watchedStocks';

// 在现有内容中添加
<div className="mb-6">
  <WatchedStocksPanel />
</div>
```

---

### Phase 8: 测试与验证 (20分钟)

#### 8.1 后端测试
- [ ] 测试 GET /api/v1/watched
- [ ] 测试 POST /api/v1/watched
- [ ] 测试 DELETE /api/v1/watched/{code}

```bash
# 测试添加
curl -X POST http://localhost:8000/api/v1/watched \
  -H "Content-Type: application/json" \
  -d '{"stock_code": "600519"}'

# 测试获取
curl http://localhost:8000/api/v1/watched

# 测试删除
curl -X DELETE http://localhost:8000/api/v1/watched/600519
```

#### 8.2 前端测试
- [ ] 启动前端开发服务器
- [ ] 访问主页验证关注股票板块显示
- [ ] 测试添加/删除关注股票
- [ ] 验证技术指标显示正确

---

### Phase 9: 样式优化 (10分钟)

#### 9.1 响应式布局
- [ ] 优化移动端显示
- [ ] 调整卡片间距和字体大小

---

## 文件清单

### 后端文件
1. `src/repositories/watched_stocks_repo.py` - 数据库仓储
2. `src/services/technical_indicators_service.py` - 技术指标服务
3. `api/v1/schemas/watched_stocks.py` - Pydantic 模型
4. `api/v1/endpoints/watched_stocks.py` - API 路由
5. `src/stock_analyzer.py` - 修改：添加布林线计算

### 前端文件
1. `apps/dsa-web/src/types/watchedStocks.ts` - TypeScript 类型
2. `apps/dsa-web/src/api/watchedStocks.ts` - API 客户端
3. `apps/dsa-web/src/components/watchedStocks/WatchedStockCard.tsx` - 卡片组件
4. `apps/dsa-web/src/components/watchedStocks/WatchedStocksPanel.tsx` - 面板组件
5. `apps/dsa-web/src/components/watchedStocks/index.ts` - 导出文件

### 修改的文件
1. `apps/dsa-web/src/api/index.ts` - 添加 API 导出
2. `apps/dsa-web/src/pages/HomePage.tsx` - 集成关注股票板块

---

## 关键决策

1. **数据更新方式**: 一次性加载所有数据（价格 + 技术指标）
2. **用户认证**: 使用固定用户 ID 'default_user'
3. **技术指标**: 复用 StockTrendAnalyzer，新增布林线计算
4. **UI 组件**: 卡片视图，显示完整技术指标

---

## 依赖与风险

### 依赖
- 现有 StockTrendAnalyzer 类
- 现有数据获取接口
- 现有前端组件库

### 风险
1. 技术指标计算可能较慢，影响页面加载时间
2. 关注股票数量多时，批量获取可能导致性能问题
3. 实时价格数据需要调用外部接口，可能有失败风险

### 缓解措施
1. 后端可考虑添加缓存机制
2. 前端添加 Loading 状态和错误处理
3. 限制最大关注股票数量（如 50 只）

---

## 后续优化方向

1. 添加股票搜索和推荐功能
2. 支持分组管理（如：A股、港股、美股）
3. 添加技术指标图表可视化
4. 支持自定义指标周期
5. 添加价格预警功能
