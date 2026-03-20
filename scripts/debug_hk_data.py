#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股数据调试脚本

用法：
    python scripts/debug_hk_data.py [股票代码]

示例：
    python scripts/debug_hk_data.py           # 默认测试 HK00700, 00700, HK09988
    python scripts/debug_hk_data.py HK00700
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from datetime import datetime

# 启用详细日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# 让 data_provider 输出 INFO
logging.getLogger("data_provider").setLevel(logging.INFO)

HK_TEST_CODES = ["HK00700", "00700", "HK09988"]


def step(name: str, fn, *args, **kwargs):
    """执行一步并打印结果"""
    print(f"\n{'='*60}")
    print(f"▶ {name}")
    print("=" * 60)
    try:
        result = fn(*args, **kwargs)
        print(f"✓ 成功: {type(result).__name__}")
        if result is not None:
            if hasattr(result, "__len__") and not isinstance(result, str):
                print(f"  长度/行数: {len(result)}")
            if hasattr(result, "columns"):
                print(f"  列: {list(result.columns)}")
            elif isinstance(result, dict) and len(result) < 20:
                for k, v in list(result.items())[:10]:
                    print(f"  {k}: {v}")
        return result
    except Exception as e:
        print(f"✗ 失败: {type(e).__name__}: {e}")
        return None


def main():
    codes = sys.argv[1:] if len(sys.argv) > 1 else HK_TEST_CODES
    print(f"\n港股数据调试 | 测试代码: {codes} | {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    # 1. HK 代码识别
    from data_provider.akshare_fetcher import is_hk_stock_code

    print("\n" + "=" * 60)
    print("1. 港股代码识别 (is_hk_stock_code)")
    print("=" * 60)
    for c in codes:
        ok = is_hk_stock_code(c)
        print(f"  {c:12} -> {'✓ 港股' if ok else '✗ 非港股'}")

    # 2. 历史数据
    from data_provider.base import DataFetcherManager

    manager = DataFetcherManager()
    for code in codes:
        if not is_hk_stock_code(code):
            print(f"\n跳过 {code} (非港股)")
            continue
        step(f"2. 历史数据 get_daily_data({code})", manager.get_daily_data, code, days=5)

    # 3. 实时行情
    for code in codes:
        if not is_hk_stock_code(code):
            continue
        step(f"3. 实时行情 get_realtime_quote({code})", manager.get_realtime_quote, code)

    # 4. 股票名称
    for code in codes:
        if not is_hk_stock_code(code):
            continue
        step(f"4. 股票名称 get_stock_name({code})", manager.get_stock_name, code)

    # 5. 完整技术指标流程 (StockService -> TechnicalIndicatorsService)
    from src.services.technical_indicators_service import TechnicalIndicatorsService

    svc = TechnicalIndicatorsService()
    for code in codes:
        if not is_hk_stock_code(code):
            continue
        result = step(f"5. 技术指标 get_indicators([{code}])", svc.get_indicators, [code])
        if result and code in result:
            ind = result[code]
            price = ind.get("price", 0)
            has_data = price and price > 0
            print(f"  价格: {price} | 有数据: {has_data}")

    print("\n" + "=" * 60)
    print("调试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
