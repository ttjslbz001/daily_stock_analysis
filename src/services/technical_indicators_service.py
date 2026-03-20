# -*- coding: utf-8 -*-
"""
===================================
技术指标服务
===================================

职责：
1. 批量获取股票技术指标
2. 获取实时行情数据
3. 为关注股票提供技术指标和价格信息
"""

import logging
from typing import List, Dict, Any, Optional

from src.stock_analyzer import StockTrendAnalyzer
from src.services.stock_service import StockService

logger = logging.getLogger(__name__)


class TechnicalIndicatorsService:
    """
    技术指标服务

    提供批量获取技术指标和实时行情的功能
    """

    def __init__(self):
        """初始化服务"""
        self.analyzer = StockTrendAnalyzer()
        self.stock_service = StockService()

    def get_indicators(self, stock_codes: List[str]) -> Dict[str, Any]:
        """
        批量获取股票技术指标

        Args:
            stock_codes: 股票代码列表

        Returns:
            {stock_code: indicators_dict}
        """
        results = {}

        for code in stock_codes:
            try:
                # 获取历史数据用于技术指标计算（90天用于技术指标）
                history_data = self.stock_service.get_history_data(code, period="daily", days=90)

                if not history_data or not history_data.get("data"):
                    logger.warning(f"获取 {code} 历史数据失败")
                    results[code] = self._get_empty_indicators(code)
                    continue

                # 转换为 DataFrame
                import pandas as pd
                df = pd.DataFrame(history_data["data"])
                df.rename(columns={"date": "date"}, inplace=True)
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date').reset_index(drop=True)

                # 计算技术指标
                analysis_result = self.analyzer.analyze(df, code)

                # 获取实时行情
                quote = self.stock_service.get_realtime_quote(code)

                # 计算一年内最高/最低价
                year_high = float(df['high'].max()) if len(df) > 0 else 0.0
                year_low = float(df['low'].min()) if len(df) > 0 else 0.0

                # 计算 KDJ 指标
                # KDJ 使用 9 日 RSV (未成熟随机值)
                # RSV = (收盘价 - 9日最低价) / (9日最高价 - 9日最低价) * 100
                df['low_9'] = df['low'].rolling(window=9).min()
                df['high_9'] = df['high'].rolling(window=9).max()
                df['rsv'] = ((df['close'] - df['low_9']) / (df['high_9'] - df['low_9']) * 100).fillna(50)

                # K 值 = (2/3) * 前一日 K + (1/3) * 当日 RSV
                # D 值 = (2/3) * 前一日 D + (1/3) * 当日 K
                # J 值 = 3 * 当日 K - 2 * 当日 D
                df['k'] = df['rsv'].ewm(alpha=1/3, adjust=False).mean()
                df['d'] = df['k'].ewm(alpha=1/3, adjust=False).mean()
                df['j'] = 3 * df['k'] - 2 * df['d']

                # 获取最新的 KDJ 值
                latest_kdj = df.iloc[-1]
                kdj_k = float(latest_kdj['k']) if pd.notna(latest_kdj['k']) else 0.0
                kdj_d = float(latest_kdj['d']) if pd.notna(latest_kdj['d']) else 0.0
                kdj_j = float(latest_kdj['j']) if pd.notna(latest_kdj['j']) else 0.0

                # Latest bar data (today's OHLCV)
                latest_data = df.iloc[-1]
                volume = float(latest_data.get('volume', 0)) if pd.notna(latest_data.get('volume')) else 0.0
                day_high = float(latest_data.get('high', 0)) if pd.notna(latest_data.get('high')) else None
                day_low = float(latest_data.get('low', 0)) if pd.notna(latest_data.get('low')) else None

                results[code] = {
                    'price': analysis_result.current_price,
                    'change': quote.get('change') if quote else 0,
                    'change_percent': quote.get('change_percent') if quote else 0,
                    'day_high': day_high,
                    'day_low': day_low,
                    'bollinger': {
                        'upper': analysis_result.bollinger_upper,
                        'middle': analysis_result.bollinger_middle,
                        'lower': analysis_result.bollinger_lower
                    },
                    'macd': {
                        'dif': analysis_result.macd_dif,
                        'dea': analysis_result.macd_dea,
                        'bar': analysis_result.macd_bar
                    },
                    'rsi': {
                        'rsi6': analysis_result.rsi_6,
                        'rsi12': analysis_result.rsi_12,
                        'rsi24': analysis_result.rsi_24
                    },
                    'kdj': {
                        'k': kdj_k,
                        'd': kdj_d,
                        'j': kdj_j
                    },
                    'volume': volume,
                    'year_high': year_high,
                    'year_low': year_low,
                    'stock_name': quote.get('stock_name') if quote else code
                }

            except Exception as e:
                logger.error(f"计算 {code} 技术指标失败: {e}", exc_info=True)
                results[code] = self._get_empty_indicators(code)

        return results

    def get_quote(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        获取实时行情数据

        Args:
            stock_code: 股票代码

        Returns:
            实时行情数据字典，失败时返回 None
        """
        try:
            return self.stock_service.get_realtime_quote(stock_code)
        except Exception as e:
            logger.error(f"获取 {stock_code} 实时行情失败: {e}", exc_info=True)
            return None

    def _get_empty_indicators(self, stock_code: str) -> Dict[str, Any]:
        """
        获取空的技术指标（用于数据获取失败时）

        Args:
            stock_code: 股票代码

        Returns:
            空的技术指标字典
        """
        return {
            'price': 0.0,
            'change': 0.0,
            'change_percent': 0.0,
            'day_high': None,
            'day_low': None,
            'bollinger': {
                'upper': 0.0,
                'middle': 0.0,
                'lower': 0.0
            },
            'macd': {
                'dif': 0.0,
                'dea': 0.0,
                'bar': 0.0
            },
            'rsi': {
                'rsi6': 0.0,
                'rsi12': 0.0,
                'rsi24': 0.0
            },
            'kdj': {
                'k': 0.0,
                'd': 0.0,
                'j': 0.0
            },
            'volume': 0.0,
            'stock_name': stock_code,
            'year_high': 0.0,
            'year_low': 0.0
        }
