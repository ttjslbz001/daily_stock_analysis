import React, { useState, useEffect, useCallback } from 'react';
import apiClient from '../../api/index';
import type { WatchedStock } from '../../types/watchedStocks';

// 基础股票信息（不含指标）
interface BasicStock {
  stock_code: string;
  stock_name: string;
  year_high?: number;
  year_low?: number;
  updated_at: string;
}

// 加载状态
interface StockWithLoading extends WatchedStock {
  loading?: boolean;
  error?: string;
  refreshing?: boolean;  // 单只股票刷新状态
}

// 指标数据展示组件
const IndicatorValue: React.FC<{
  label: string;
  values: Array<{ value: string; color: string }>;
  separator?: string;
}> = ({ label, values, separator = '/' }) => (
  <div className="flex items-center gap-2 text-sm min-w-[140px]">
    <span className="text-muted shrink-0 text-xs w-12">{label}</span>
    <div className="flex items-center gap-1 font-mono text-xs">
      {values.map((item, idx) => (
        <React.Fragment key={idx}>
          <span className={item.color}>{item.value}</span>
          {idx < values.length - 1 && (
            <span className="text-muted text-[10px]">{separator}</span>
          )}
        </React.Fragment>
      ))}
    </div>
  </div>
);

export const WatchedStocksPanel: React.FC = () => {
  const [stocks, setStocks] = useState<StockWithLoading[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [addingStock, setAddingStock] = useState(false);
  const [newStockCode, setNewStockCode] = useState('');
  const [deletingStock, setDeletingStock] = useState<StockWithLoading | null>(null);

  // 获取基础列表（快速）
  const fetchStockList = async () => {
    try {
      const response = await apiClient.get<{ total: number; items: BasicStock[] }>('/api/v1/watched');
      const basicStocks = response.data.items.map(s => ({
        stock_code: s.stock_code,
        stock_name: s.stock_name,
        current_price: 0,
        bollinger: { upper: 0, middle: 0, lower: 0 },
        macd: { dif: 0, dea: 0, bar: 0 },
        rsi: { rsi6: 0, rsi12: 0, rsi24: 0 },
        year_high: undefined,
        year_low: undefined,
        updated_at: s.updated_at,
        loading: true,
      }));
      setStocks(basicStocks);
      return basicStocks;
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取失败');
      return [];
    }
  };

  // 获取单只股票指标
  const fetchStockIndicators = async (stockCode: string, forceRefresh = false) => {
    try {
      const url = `/api/v1/watched/${stockCode}/indicators${forceRefresh ? '?force_refresh=true' : ''}`;
      const response = await apiClient.get<WatchedStock>(url);
      return response.data;
    } catch (err) {
      console.error(`获取 ${stockCode} 指标失败:`, err);
      return null;
    }
  };

  // 逐个加载指标
  const loadIndicatorsSequentially = useCallback(async (stockList: StockWithLoading[], forceRefresh = false) => {
    for (let i = 0; i < stockList.length; i++) {
      const stock = stockList[i];
      const data = await fetchStockIndicators(stock.stock_code, forceRefresh);

      setStocks(prev => prev.map(s => {
        if (s.stock_code === stock.stock_code) {
          if (data) {
            return { ...data, loading: false };
          }
          return { ...s, loading: false, error: '加载失败' };
        }
        return s;
      }));
    }
  }, []);

  // 初始加载
  useEffect(() => {
    const init = async () => {
      setLoading(true);
      const basicStocks = await fetchStockList();
      setLoading(false);
      // 后台逐个加载指标
      if (basicStocks.length > 0) {
        loadIndicatorsSequentially(basicStocks);
      }
    };
    init();
  }, [loadIndicatorsSequentially]);

  // 刷新（强制获取新数据）
  const handleRefresh = async () => {
    setRefreshing(true);
    const basicStocks = await fetchStockList();
    if (basicStocks.length > 0) {
      await loadIndicatorsSequentially(basicStocks, true);  // forceRefresh=true
    }
    setRefreshing(false);
  };

  // 添加股票
  const handleAddStock = async () => {
    if (!newStockCode.trim()) return;
    try {
      const response = await apiClient.post('/api/v1/watched', {
        stock_code: newStockCode.trim().toUpperCase()
      });
      if (response.data.success) {
        setNewStockCode('');
        setAddingStock(false);
        handleRefresh();
      }
    } catch (err) {
      console.error('添加关注失败:', err);
    }
  };

  // 删除股票
  const handleRemove = async (stockCode: string) => {
    try {
      await apiClient.delete(`/api/v1/watched/${stockCode}`);
      setStocks(prev => prev.filter(s => s.stock_code !== stockCode));
      setDeletingStock(null);
    } catch (err) {
      console.error('取消关注失败:', err);
    }
  };

  // 单只股票刷新
  const handleRefreshStock = async (stockCode: string) => {
    setStocks(prev => prev.map(s => {
      if (s.stock_code === stockCode) {
        return { ...s, refreshing: true };
      }
      return s;
    }));

    try {
      const data = await fetchStockIndicators(stockCode, true);
      if (data) {
        setStocks(prev => prev.map(s => {
          if (s.stock_code === stockCode) {
            return { ...data, loading: false, refreshing: false };
          }
          return s;
        }));
      } else {
        setStocks(prev => prev.map(s => {
          if (s.stock_code === stockCode) {
            return { ...s, refreshing: false, error: '刷新失败' };
          }
          return s;
        }));
      }
    } catch (err) {
      console.error(`刷新 ${stockCode} 失败:`, err);
      setStocks(prev => prev.map(s => {
        if (s.stock_code === stockCode) {
          return { ...s, refreshing: false, error: '刷新失败' };
        }
        return s;
      }));
    }
  };

  // 添加对话框
  if (addingStock) {
    return (
      <div className="bg-card rounded-xl border border-white/5 overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
          <span className="text-sm font-medium text-white">添加关注股票</span>
          <button onClick={() => setAddingStock(false)} className="text-muted hover:text-white">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="p-4">
          <div className="flex gap-2">
            <input
              type="text"
              value={newStockCode}
              onChange={(e) => setNewStockCode(e.target.value.toUpperCase())}
              onKeyDown={(e) => e.key === 'Enter' && handleAddStock()}
              placeholder="输入股票代码，如 600519、NVDA、00700"
              className="flex-1 px-4 py-2 text-sm bg-elevated border border-white/10 rounded-lg text-white placeholder-muted focus:outline-none focus:border-cyan/50"
              autoFocus
            />
            <button
              onClick={handleAddStock}
              disabled={!newStockCode.trim()}
              className="px-4 py-2 text-sm bg-cyan text-white rounded-lg hover:bg-cyan/80 disabled:opacity-50"
            >
              添加
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 删除确认对话框
  if (deletingStock) {
    return (
      <div className="bg-card rounded-xl border border-red-500/30 overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-white/5 bg-red-500/10">
          <span className="text-sm font-medium text-red-400">确认删除</span>
          <button onClick={() => setDeletingStock(null)} className="text-muted hover:text-white">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="p-4">
          <p className="text-sm text-secondary mb-4">
            确定要删除 <span className="text-white font-medium">{deletingStock.stock_name || deletingStock.stock_code}</span> 吗？
          </p>
          <div className="flex gap-2 justify-end">
            <button
              onClick={() => setDeletingStock(null)}
              className="px-4 py-2 text-sm text-muted hover:text-white transition-colors"
            >
              取消
            </button>
            <button
              onClick={() => handleRemove(deletingStock.stock_code)}
              className="px-4 py-2 text-sm bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
            >
              确认删除
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 加载状态
  if (loading) {
    return (
      <div className="bg-card rounded-xl border border-white/5 overflow-hidden">
        <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5">
          <svg className="w-4 h-4 text-cyan" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
          </svg>
          <span className="text-sm font-medium text-white">我关注的股票</span>
        </div>
        <div className="p-6 flex items-center justify-center">
          <div className="w-6 h-6 border-2 border-cyan/20 border-t-cyan rounded-full animate-spin" />
        </div>
      </div>
    );
  }

  // 错误状态
  if (error) {
    return (
      <div className="bg-card rounded-xl border border-white/5 overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
          <span className="text-sm font-medium text-white">我关注的股票</span>
          <button onClick={handleRefresh} className="text-xs text-cyan hover:text-cyan/80">重试</button>
        </div>
        <div className="p-4 text-center text-sm text-red-400">{error}</div>
      </div>
    );
  }

  // 渲染单行股票
  const renderStockRow = (stock: StockWithLoading) => {
    const isPositive = (stock.change_percent ?? 0) >= 0;
    const changeColor = isPositive ? 'text-red-400' : 'text-green-400';
    const isLoading = stock.loading;

    return (
      <div
        key={stock.stock_code}
        className="flex items-center gap-4 px-4 py-3 border-b border-white/5 hover:bg-white/[0.02] transition-colors group flex-wrap"
      >
        {/* 股票代码和名称 */}
        <div className="flex items-center gap-3 min-w-[140px]">
          <button
            onClick={() => setDeletingStock(stock)}
            className="text-red-400/60 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
            title="取消关注"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
          <div>
            <span className="text-sm font-medium text-white">{stock.stock_name || stock.stock_code}</span>
            <span className="text-xs text-muted ml-2">{stock.stock_code}</span>
          </div>
        </div>

        {/* 价格和涨跌 */}
        <div className="flex items-baseline gap-2 min-w-[160px]">
          {isLoading ? (
            <div className="w-20 h-5 bg-white/5 rounded animate-pulse" />
          ) : (
            <>
              <span className="text-lg font-bold text-white">
                {stock.current_price > 0 ? stock.current_price.toFixed(2) : '-'}
              </span>
              {stock.change_percent !== undefined && stock.change_percent !== null && (
                <span className={`text-sm font-medium ${changeColor}`}>
                  {isPositive ? '+' : ''}{stock.change_percent.toFixed(2)}%
                </span>
              )}
            </>
          )}
        </div>

        {/* 分隔线 */}
        <div className="w-px h-6 bg-white/10 hidden sm:block" />

        {/* 指标区域 */}
        {isLoading ? (
          <div className="flex items-center gap-4 flex-1 overflow-hidden">
            <div className="w-32 h-4 bg-white/5 rounded animate-pulse" />
            <div className="w-28 h-4 bg-white/5 rounded animate-pulse" />
            <div className="w-20 h-4 bg-white/5 rounded animate-pulse" />
          </div>
        ) : (
          <div className="flex items-center gap-3 flex-1 overflow-hidden sm:flex-nowrap flex-wrap sm:flex-nowrap">
            <IndicatorValue
              label="BOLL"
              values={[
                { value: stock.bollinger.upper.toFixed(1), color: 'text-red-400' },
                { value: stock.bollinger.middle.toFixed(1), color: 'text-secondary' },
                { value: stock.bollinger.lower.toFixed(1), color: 'text-green-400' }
              ]}
            />
            <div className="w-px h-6 bg-white/10" />
            <IndicatorValue
              label="MACD"
              values={[{
                value: stock.macd.bar.toFixed(2),
                color: stock.macd.bar >= 0 ? 'text-red-400' : 'text-green-400'
              }]}
            />
            <div className="w-px h-6 bg-white/10" />
            <IndicatorValue
              label="RSI"
              values={[
                { value: stock.rsi.rsi6.toFixed(0), color: 'text-secondary' },
                { value: stock.rsi.rsi12.toFixed(0), color: 'text-secondary' },
                { value: stock.rsi.rsi24.toFixed(0), color: 'text-secondary' }
              ]}
            />
            <div className="w-px h-6 bg-white/10" />
            <IndicatorValue
              label="年高/低"
              values={[
                { value: stock.year_high?.toFixed(2) || '-', color: 'text-red-400' },
                { value: stock.year_low?.toFixed(2) || '-', color: 'text-green-400' }
              ]}
            />
          </div>
        )}

        {/* 刷新按钮 */}
        {!isLoading && (
          <button
            onClick={() => handleRefreshStock(stock.stock_code)}
            disabled={stock.refreshing}
            className="p-1 text-muted hover:text-cyan transition-colors disabled:opacity-50"
            title="刷新指标"
          >
            <svg
              className={`w-4 h-4 ${stock.refreshing ? 'animate-spin' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
          </button>
        )}
      </div>
    );
  };

  return (
    <div className="bg-card rounded-xl border border-white/5 overflow-hidden">
      {/* 标题栏 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-cyan" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
          </svg>
          <span className="text-sm font-medium text-white">我关注的股票</span>
          {stocks.length > 0 && (
            <span className="text-xs text-muted">({stocks.length})</span>
          )}
          {stocks.some(s => s.loading) && (
            <div className="w-3 h-3 border border-cyan/20 border-t-cyan rounded-full animate-spin" />
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="p-1.5 text-muted hover:text-white transition-colors disabled:opacity-50"
            title="刷新"
          >
            <svg className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
          <button
            onClick={() => setAddingStock(true)}
            className="flex items-center gap-1 px-3 py-1.5 text-xs bg-cyan/10 border border-cyan/20 text-cyan rounded-lg hover:bg-cyan/20 transition-colors"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            添加
          </button>
        </div>
      </div>

      {/* 表头 */}
      {stocks.length > 0 && (
        <div className="flex items-center gap-3 px-4 py-2 text-xs text-muted border-b border-white/5 bg-white/[0.01] flex-wrap">
          <div className="min-w-[140px]">股票</div>
          <div className="min-w-[160px]">价格 / 涨跌</div>
          <div className="w-px h-4 bg-white/10 hidden sm:block" />
          <div className="min-w-[140px]">布林线 (上/中/下)</div>
          <div className="min-w-[140px]">MACD</div>
          <div className="min-w-[140px]">RSI (6/12/24)</div>
          <div className="min-w-[140px]">年高/低</div>
          <div className="w-8" /> {/* 刷新按钮占位 */}
        </div>
      )}

      {/* 股票列表 */}
      {stocks.length === 0 ? (
        <div className="p-8 text-center">
          <p className="text-sm text-muted mb-3">暂无关注股票</p>
          <button
            onClick={() => setAddingStock(true)}
            className="text-sm text-cyan hover:text-cyan/80"
          >
            + 添加第一只股票
          </button>
        </div>
      ) : (
        <div className="divide-y divide-white/5">
          {stocks.map(stock => renderStockRow(stock))}
        </div>
      )}
    </div>
  );
};
