# -*- coding: utf-8 -*-
"""
股票日线数据同步脚本

功能：
1. 从 .env 读取用户关注的股票列表 (STOCK_LIST)
2. 获取每只股票的日线数据（最近 500 个交易日）
3. 保存到本地 data/daily_kline/ 目录（CSV 格式）
4. 支持增量更新（仅获取缺失的日期）

使用方式：
    python scripts/sync_daily_data.py              # 立即执行同步
    python scripts/sync_daily_data.py --schedule   # 启动定时任务（每天 8:00）
    python scripts/sync_daily_data.py --schedule --time 09:00  # 自定义时间
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 设置环境变量
os.chdir(PROJECT_ROOT)
from src.config import setup_env
setup_env()

from data_provider.base import DataFetcherManager, canonical_stock_code
from src.config import get_config
from src.logging_config import setup_logging

# 配置日志
logger = logging.getLogger(__name__)

# 默认数据存储目录
DEFAULT_DATA_DIR = Path(os.getenv('DAILY_DATA_DIR', PROJECT_ROOT / "data" / "daily_kline"))
# 默认获取天数
DEFAULT_DAYS = int(os.getenv('DAILY_DATA_SYNC_DAYS', '500'))


class DailyDataSyncer:
    """日线数据同步器"""

    def __init__(self, data_dir: Optional[Path] = None):
        """
        初始化同步器

        Args:
            data_dir: 数据存储目录，默认为 data/daily_kline/
        """
        self.config = get_config()
        self.data_dir = data_dir or DEFAULT_DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 初始化数据获取器
        self.fetcher_manager = DataFetcherManager()

        logger.info(f"数据存储目录: {self.data_dir}")

    def get_stock_list(self) -> List[str]:
        """获取用户关注的股票列表"""
        stock_list = self.config.stock_list
        if not stock_list:
            logger.warning("未配置 STOCK_LIST，请检查 .env 文件")
            return []
        return [canonical_stock_code(code) for code in stock_list]

    def get_local_data_path(self, stock_code: str) -> Path:
        """获取本地数据文件路径"""
        # 使用大写代码作为文件名
        safe_code = stock_code.replace("/", "_").replace("\\", "_")
        return self.data_dir / f"{safe_code}.csv"

    def load_local_data(self, stock_code: str) -> Tuple[pd.DataFrame, Optional[str]]:
        """
        加载本地数据

        Returns:
            (DataFrame, 最后日期) - 如果不存在则返回 (空DataFrame, None)
        """
        file_path = self.get_local_data_path(stock_code)
        if not file_path.exists():
            return pd.DataFrame(), None

        try:
            df = pd.read_csv(file_path, parse_dates=['date'])
            if df.empty:
                return pd.DataFrame(), None

            last_date = df['date'].max().strftime('%Y-%m-%d')
            logger.info(f"[{stock_code}] 本地数据: {len(df)} 条，最后日期: {last_date}")
            return df, last_date
        except Exception as e:
            logger.warning(f"[{stock_code}] 读取本地数据失败: {e}")
            return pd.DataFrame(), None

    def save_data(self, stock_code: str, df: pd.DataFrame) -> bool:
        """
        保存数据到本地

        Args:
            stock_code: 股票代码
            df: 日线数据

        Returns:
            是否保存成功
        """
        if df.empty:
            return False

        file_path = self.get_local_data_path(stock_code)
        try:
            # 确保日期列格式正确
            df = df.copy()
            df['date'] = pd.to_datetime(df['date'])

            # 按日期排序并去重
            df = df.sort_values('date').drop_duplicates(subset=['date'], keep='last')

            # 保存为 CSV
            df.to_csv(file_path, index=False, date_format='%Y-%m-%d')
            logger.info(f"[{stock_code}] 保存成功: {len(df)} 条数据 -> {file_path}")
            return True
        except Exception as e:
            logger.error(f"[{stock_code}] 保存失败: {e}")
            return False

    def sync_stock(self, stock_code: str, days: int = 500) -> bool:
        """
        同步单只股票的日线数据

        Args:
            stock_code: 股票代码
            days: 获取的天数（当无本地数据时）

        Returns:
            是否同步成功
        """
        logger.info(f"\n{'='*50}")
        logger.info(f"开始同步: {stock_code}")
        logger.info(f"{'='*50}")

        try:
            # 1. 加载本地数据
            local_df, last_date = self.load_local_data(stock_code)

            # 2. 计算需要获取的日期范围
            end_date = datetime.now().strftime('%Y-%m-%d')

            if last_date:
                # 增量更新：从最后日期的第二天开始
                start_dt = datetime.strptime(last_date, '%Y-%m-%d') + timedelta(days=1)
                start_date = start_dt.strftime('%Y-%m-%d')

                if start_date > end_date:
                    logger.info(f"[{stock_code}] 数据已是最新，无需更新")
                    return True

                logger.info(f"[{stock_code}] 增量更新: {start_date} ~ {end_date}")
            else:
                # 全量获取
                start_dt = datetime.now() - timedelta(days=days * 2)
                start_date = start_dt.strftime('%Y-%m-%d')
                logger.info(f"[{stock_code}] 全量获取: {start_date} ~ {end_date}")

            # 3. 获取数据
            new_df, source = self.fetcher_manager.get_daily_data(
                stock_code=stock_code,
                start_date=start_date,
                end_date=end_date,
                days=days
            )

            if new_df.empty:
                logger.warning(f"[{stock_code}] 未获取到新数据")
                return not local_df.empty  # 如果本地有数据，认为成功

            logger.info(f"[{stock_code}] 获取成功: {len(new_df)} 条数据 (来源: {source})")

            # 4. 合并数据
            if not local_df.empty:
                combined_df = pd.concat([local_df, new_df], ignore_index=True)
                combined_df = combined_df.drop_duplicates(subset=['date'], keep='last')
                combined_df = combined_df.sort_values('date').reset_index(drop=True)
            else:
                combined_df = new_df

            # 5. 保存数据
            return self.save_data(stock_code, combined_df)

        except Exception as e:
            logger.error(f"[{stock_code}] 同步失败: {e}")
            return False

    def sync_all(self, stock_codes: Optional[List[str]] = None, days: int = 500) -> dict:
        """
        同步所有股票数据

        Args:
            stock_codes: 股票代码列表，如果为 None 则从配置读取
            days: 获取的天数

        Returns:
            同步结果统计
        """
        if stock_codes is None:
            stock_codes = self.get_stock_list()

        if not stock_codes:
            logger.error("没有需要同步的股票")
            return {"total": 0, "success": 0, "failed": 0}

        logger.info(f"\n开始同步 {len(stock_codes)} 只股票的日线数据...")
        logger.info(f"股票列表: {stock_codes}")

        results = {
            "total": len(stock_codes),
            "success": 0,
            "failed": 0,
            "failed_codes": []
        }

        for i, code in enumerate(stock_codes):
            logger.info(f"\n进度: [{i+1}/{len(stock_codes)}]")
            if self.sync_stock(code, days=days):
                results["success"] += 1
            else:
                results["failed"] += 1
                results["failed_codes"].append(code)

        # 打印摘要
        logger.info(f"\n{'='*60}")
        logger.info("同步完成")
        logger.info(f"{'='*60}")
        logger.info(f"总数: {results['total']}")
        logger.info(f"成功: {results['success']}")
        logger.info(f"失败: {results['failed']}")
        if results["failed_codes"]:
            logger.info(f"失败股票: {results['failed_codes']}")

        return results


def run_scheduled_sync(schedule_time: str = "08:00", days: int = 500):
    """
    启动定时同步任务

    Args:
        schedule_time: 每日执行时间，格式 "HH:MM"
        days: 获取的天数
    """
    try:
        import schedule
    except ImportError:
        logger.error("schedule 库未安装，请执行: pip install schedule")
        sys.exit(1)

    # 简单的退出信号处理
    import signal
    import threading

    shutdown_event = threading.Event()

    def signal_handler(signum, frame):
        logger.info(f"收到退出信号 ({signum})，等待当前任务完成...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    def sync_task():
        logger.info(f"\n{'#'*60}")
        logger.info(f"定时任务开始 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'#'*60}")
        syncer = DailyDataSyncer()
        syncer.sync_all(days=days)
        logger.info(f"\n定时任务完成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 设置定时任务
    schedule.every().day.at(schedule_time).do(sync_task)
    logger.info(f"定时同步任务已启动")
    logger.info(f"执行时间: 每天 {schedule_time}")
    logger.info(f"按 Ctrl+C 退出...")

    # 立即执行一次
    logger.info("\n立即执行一次同步...")
    sync_task()

    # 主循环
    import time
    while not shutdown_event.is_set():
        schedule.run_pending()
        time.sleep(30)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='股票日线数据同步工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  python scripts/sync_daily_data.py              # 立即执行同步
  python scripts/sync_daily_data.py --schedule   # 启动定时任务（默认 8:00）
  python scripts/sync_daily_data.py --schedule --time 09:30  # 自定义时间
  python scripts/sync_daily_data.py --stocks 600519,300750  # 指定股票
  python scripts/sync_daily_data.py --days 1000  # 获取 1000 天数据
        '''
    )

    parser.add_argument(
        '--schedule',
        action='store_true',
        help='启动定时任务模式'
    )

    parser.add_argument(
        '--time',
        type=str,
        default='08:00',
        help='定时任务执行时间，格式 HH:MM（默认 08:00）'
    )

    parser.add_argument(
        '--stocks',
        type=str,
        help='指定要同步的股票代码，逗号分隔（覆盖配置）'
    )

    parser.add_argument(
        '--days',
        type=int,
        default=DEFAULT_DAYS,
        help=f'获取的天数（默认 {DEFAULT_DAYS}）'
    )

    parser.add_argument(
        '--data-dir',
        type=str,
        help='数据存储目录（默认 data/daily_kline/）'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='调试模式'
    )

    args = parser.parse_args()

    # 设置日志
    setup_logging(
        log_prefix="sync_daily_data",
        debug=args.debug,
        log_dir=os.getenv('LOG_DIR', './logs')
    )

    logger.info("="*60)
    logger.info("股票日线数据同步工具")
    logger.info(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)

    # 解析股票列表
    stock_codes = None
    if args.stocks:
        stock_codes = [canonical_stock_code(c) for c in args.stocks.split(',') if c.strip()]
        logger.info(f"使用命令行指定的股票列表: {stock_codes}")

    # 解析数据目录
    data_dir = Path(args.data_dir) if args.data_dir else None

    # 定时任务模式
    if args.schedule:
        run_scheduled_sync(schedule_time=args.time, days=args.days)
        return 0

    # 单次执行模式
    syncer = DailyDataSyncer(data_dir=data_dir)
    results = syncer.sync_all(stock_codes=stock_codes, days=args.days)

    return 0 if results["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
