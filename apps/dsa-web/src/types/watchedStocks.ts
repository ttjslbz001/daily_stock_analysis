/**
 * 关注股票相关类型定义
 * 与 API 规范 (api/v1/schemas/watched_stocks.py) 对齐
 */

// ============ 技术指标类型 ============

/** 布林线指标 */
export interface BollingerBands {
  upper: number;  // 上轨
  middle: number; // 中轨
  lower: number;  // 下轨
}

/** MACD 指标 */
export interface MACD {
  dif: number;  // DIF 快线
  dea: number;  // DEA 慢线
  bar: number;  // MACD 柱状图
}

/** RSI 指标 */
export interface RSI {
  rsi6: number;   // RSI(6) 短期
  rsi12: number;  // RSI(12) 中期
  rsi24: number;  // RSI(24) 长期
}

// ============ 响应类型 ============

/** 关注股票响应 */
export interface WatchedStock {
  stock_code: string;       // 股票代码
  stock_name: string;       // 股票名称
  current_price: number;    // 当前价格
  change?: number;          // 涨跌额
  change_percent?: number;  // 涨跌幅（%）
  year_high?: number;       // 一年内最高价
  year_low?: number;        // 一年内最低价
  bollinger: BollingerBands; // 布林线指标
  macd: MACD;              // MACD 指标
  rsi: RSI;                // RSI 指标
  updated_at: string;      // 更新时间
}

/** 关注股票列表响应 */
export interface WatchedStocksListResponse {
  total: number;                    // 总数
  items: WatchedStock[];            // 关注股票列表
}

// ============ 请求类型 ============

/** 添加关注股票请求 */
export interface AddWatchedStockRequest {
  stock_code: string;     // 股票代码
  stock_name?: string;    // 股票名称（可选）
}

/** 添加关注股票响应 */
export interface AddWatchedStockResponse {
  success: boolean;       // 是否成功
  message: string;        // 消息
  stock_code: string;     // 股票代码
}

/** 取消关注股票响应 */
export interface RemoveWatchedStockResponse {
  success: boolean;       // 是否成功
  message: string;        // 消息
  stock_code: string;     // 股票代码
}

// ============ 辅助函数 ============

/** 格式化价格 */
export const formatPrice = (price: number, decimals: number = 2): string => {
  return price.toFixed(decimals);
};

/** 格式化百分比 */
export const formatPercent = (percent: number, decimals: number = 2): string => {
  return percent.toFixed(decimals);
};

/** 获取涨跌幅颜色 */
export const getChangeColor = (changePercent?: number): string => {
  if (changePercent === undefined || changePercent === null) return 'text-gray-500';
  return changePercent >= 0 ? 'text-red-500' : 'text-green-500';
};

/** 获取 MACD 柱状图颜色 */
export const getMACDBarColor = (bar: number): string => {
  return bar >= 0 ? 'text-red-400' : 'text-green-400';
};
