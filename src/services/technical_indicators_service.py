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
                # 获取历史数据用于技术指标计算
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

                # 构建响应
                results[code] = {
                    'price': analysis_result.current_price,
                    'change': quote.get('change') if quote else 0,
                    'change_percent': quote.get('change_percent') if quote else 0,
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
            'stock_name': stock_code
        }
