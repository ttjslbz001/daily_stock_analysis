import type React from 'react';
import { useState, useEffect } from 'react';

interface SectorData {
  rank: number;
  name: string;
  change_pct: number;
  leading_stock: string;
}

interface MarketOverview {
  up_count: number;
  down_count: number;
  flat_count: number;
  limit_up_count: number;
  limit_down_count: number;
  total_amount: number;
}

interface SectorsBoardData {
  date: string;
  update_time: string;
  market_overview: MarketOverview;
  top_sectors: SectorData[];
  bottom_sectors: SectorData[];
}

const SectorsBoardPage: React.FC = () => {
  const [data, setData] = useState<SectorsBoardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async (forceRefresh = false) => {
    try {
      setError(null);
      const url = forceRefresh
        ? '/api/v1/sectors/board?force_refresh=true'
        : '/api/v1/sectors/board';
      const response = await fetch(url);
      if (!response.ok) throw new Error('获取数据失败');
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取数据失败');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData(true);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-8 h-8 border-2 border-cyan/20 border-t-cyan rounded-full animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4">
        <p className="text-red-400">{error}</p>
        <button onClick={() => fetchData()} className="btn-primary">
          重试
        </button>
      </div>
    );
  }

  if (!data) return null;

  const { market_overview, top_sectors, bottom_sectors } = data;

  return (
    <div className="p-4 md:p-6 max-w-6xl mx-auto">
      {/* 标题栏 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-white">板块看板</h1>
          <p className="text-xs text-muted mt-1">
            {data.date} {data.update_time}
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-elevated border border-white/10 rounded-lg hover:border-white/20 disabled:opacity-50"
        >
          <svg
            className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`}
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
          刷新
        </button>
      </div>

      {/* 市场概况 */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-3 mb-6">
        <div className="bg-card rounded-xl border border-white/5 p-3">
          <div className="text-xs text-muted mb-1">上涨</div>
          <div className="text-lg font-bold text-red-400">{market_overview.up_count}</div>
        </div>
        <div className="bg-card rounded-xl border border-white/5 p-3">
          <div className="text-xs text-muted mb-1">下跌</div>
          <div className="text-lg font-bold text-green-400">{market_overview.down_count}</div>
        </div>
        <div className="bg-card rounded-xl border border-white/5 p-3">
          <div className="text-xs text-muted mb-1">平盘</div>
          <div className="text-lg font-bold text-secondary">{market_overview.flat_count}</div>
        </div>
        <div className="bg-card rounded-xl border border-white/5 p-3">
          <div className="text-xs text-muted mb-1">涨停</div>
          <div className="text-lg font-bold text-red-500">{market_overview.limit_up_count}</div>
        </div>
        <div className="bg-card rounded-xl border border-white/5 p-3">
          <div className="text-xs text-muted mb-1">跌停</div>
          <div className="text-lg font-bold text-green-500">{market_overview.limit_down_count}</div>
        </div>
        <div className="bg-card rounded-xl border border-white/5 p-3">
          <div className="text-xs text-muted mb-1">成交额(亿)</div>
          <div className="text-lg font-bold text-cyan">{market_overview.total_amount.toFixed(0)}</div>
        </div>
      </div>

      {/* 涨跌榜 */}
      <div className="grid md:grid-cols-2 gap-4">
        {/* 涨幅榜 */}
        <div className="bg-card rounded-xl border border-white/5 overflow-hidden">
          <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5">
            <svg className="w-4 h-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
            </svg>
            <span className="text-sm font-medium text-white">板块涨幅榜</span>
          </div>
          <div className="divide-y divide-white/5">
            {top_sectors.map((sector) => (
              <div key={sector.rank} className="flex items-center justify-between px-4 py-2.5 hover:bg-elevated/50">
                <div className="flex items-center gap-3">
                  <span className="text-xs text-muted w-4">{sector.rank}</span>
                  <span className="text-sm text-white">{sector.name}</span>
                </div>
                <span className="text-sm font-medium text-red-400">
                  +{sector.change_pct.toFixed(2)}%
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* 跌幅榜 */}
        <div className="bg-card rounded-xl border border-white/5 overflow-hidden">
          <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5">
            <svg className="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
            </svg>
            <span className="text-sm font-medium text-white">板块跌幅榜</span>
          </div>
          <div className="divide-y divide-white/5">
            {bottom_sectors.map((sector) => (
              <div key={sector.rank} className="flex items-center justify-between px-4 py-2.5 hover:bg-elevated/50">
                <div className="flex items-center gap-3">
                  <span className="text-xs text-muted w-4">{sector.rank}</span>
                  <span className="text-sm text-white">{sector.name}</span>
                </div>
                <span className="text-sm font-medium text-green-400">
                  {sector.change_pct.toFixed(2)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SectorsBoardPage;
