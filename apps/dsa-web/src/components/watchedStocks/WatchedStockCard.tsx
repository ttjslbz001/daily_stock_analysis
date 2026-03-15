import React from 'react';
import type { WatchedStock } from '../../types/watchedStocks';

interface WatchedStockCardProps {
  stock: WatchedStock;
  onRemove: (code: string) => void;
}

export const WatchedStockCard: React.FC<WatchedStockCardProps> = ({
  stock,
  onRemove
}) => {
  const isPositive = stock.change_percent !== undefined && stock.change_percent !== null && stock.change_percent >= 0;
  const changeColor = isPositive ? 'text-red-400' : 'text-green-400';

  return (
    <div className="bg-elevated rounded-lg border border-white/5 p-3 hover:border-white/10 transition-colors">
      {/* 股票基本信息 */}
      <div className="flex justify-between items-start mb-2">
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-medium text-white truncate">
            {stock.stock_name}
          </h3>
          <p className="text-xs text-muted">{stock.stock_code}</p>
        </div>
        <button
          onClick={() => onRemove(stock.stock_code)}
          className="text-muted hover:text-red-400 transition-colors p-1"
          title="取消关注"
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* 价格信息 */}
      <div className="mb-3">
        <div className="text-lg font-bold text-white">
          {stock.current_price.toFixed(2)}
        </div>
        <div className={`text-xs font-medium ${changeColor}`}>
          {stock.change !== undefined && stock.change !== null && (
            <>
              {isPositive ? '+' : ''}{stock.change.toFixed(2)}
            </>
          )}
          {stock.change_percent !== undefined && stock.change_percent !== null && (
            <span className="ml-1">
              ({isPositive ? '+' : ''}{stock.change_percent.toFixed(2)}%)
            </span>
          )}
        </div>
      </div>

      {/* 技术指标 */}
      <div className="space-y-2 text-xs">
        {/* 布林线 */}
        <div className="bg-card rounded p-2 border border-white/5">
          <div className="text-muted mb-1">布林线</div>
          <div className="flex justify-between gap-2">
            <span className="text-red-400">上 {stock.bollinger.upper.toFixed(2)}</span>
            <span className="text-secondary">中 {stock.bollinger.middle.toFixed(2)}</span>
            <span className="text-green-400">下 {stock.bollinger.lower.toFixed(2)}</span>
          </div>
        </div>

        {/* MACD */}
        <div className="bg-card rounded p-2 border border-white/5">
          <div className="text-muted mb-1">MACD</div>
          <div className="flex justify-between gap-1">
            <span>DIF {stock.macd.dif.toFixed(3)}</span>
            <span>DEA {stock.macd.dea.toFixed(3)}</span>
            <span className={stock.macd.bar >= 0 ? 'text-red-400' : 'text-green-400'}>
              BAR {stock.macd.bar.toFixed(3)}
            </span>
          </div>
        </div>

        {/* RSI */}
        <div className="bg-card rounded p-2 border border-white/5">
          <div className="text-muted mb-1">RSI</div>
          <div className="flex justify-between">
            <span>R6 {stock.rsi.rsi6.toFixed(1)}</span>
            <span>R12 {stock.rsi.rsi12.toFixed(1)}</span>
            <span>R24 {stock.rsi.rsi24.toFixed(1)}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
