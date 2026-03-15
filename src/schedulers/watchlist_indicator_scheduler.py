# -*- coding: utf-8 -*-
"""
===================================
Watch List Indicator Scheduler
===================================

职责：
1. 管理关注股票技术指标的自动刷新
2. 检查指标是否需要刷新（超过8小时）
3. 在后台定期执行刷新任务
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

from src.repositories.watched_stocks_repo import WatchedStocksRepository
from src.services.technical_indicators_service import TechnicalIndicatorsService

logger = logging.getLogger(__name__)


class WatchListIndicatorScheduler:
    """
    Watch List Indicator Scheduler

    Manages automatic refresh of watch list technical indicators every 8 hours.
    """

    def __init__(
        self,
        repo: WatchedStocksRepository,
        indicators_service: TechnicalIndicatorsService,
        refresh_interval_hours: Optional[int] = None,
        user_id: str = 'default_user',
    ):
        """
        Initialize the scheduler

        Args:
            repo: WatchedStocksRepository instance for database operations
            indicators_service: TechnicalIndicatorsService for fetching indicators
            refresh_interval_hours: Number of hours between refreshes (default from env or 8)
            user_id: User ID to fetch watch list for (default: 'default_user')
        """
        self.repo = repo
        self.indicators_service = indicators_service
        # Read from environment variable if not provided, otherwise use default
        self.refresh_interval_hours = (
            refresh_interval_hours
            if refresh_interval_hours is not None
            else int(os.getenv('WATCHLIST_REFRESH_INTERVAL_HOURS', '8'))
        )
        self.user_id = user_id

        # Background task reference
        self._refresh_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self) -> None:
        """
        Start the background refresh loop

        This will:
        1. Check if any stocks need immediate refresh (if stale)
        2. Start the periodic refresh loop
        """
        if self._running:
            logger.warning("Scheduler is already running")
            return

        logger.info("Starting WatchListIndicatorScheduler")

        # Initial check - refresh if any indicators are stale on startup
        # This ensures that indicators are fresh when the server starts
        await self.refresh_if_needed()

        # Start the periodic refresh loop in the background
        # This runs asynchronously and doesn't block the main application
        self._running = True
        self._refresh_task = asyncio.create_task(self._run_refresh_loop())
        logger.info(
            f"Started background refresh loop (interval: {self.refresh_interval_hours} hours)"
        )

    async def stop(self) -> None:
        """
        Stop the background refresh loop

        Cancels the running background task gracefully.
        """
        if not self._running:
            return

        logger.info("Stopping WatchListIndicatorScheduler")
        self._running = False

        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                logger.debug("Refresh task cancelled successfully")

        logger.info("WatchListIndicatorScheduler stopped")

    async def refresh_if_needed(self) -> None:
        """
        Check if indicators need refresh and refresh them if needed

        This is called on startup to handle stale indicators.
        Refresh is triggered if ANY stock's indicators are older than the threshold.
        """
        try:
            watched_stocks = self.repo.list(self.user_id)

            if not watched_stocks:
                logger.info("No watched stocks to check for refresh")
                return

            # Check if any stock needs refresh
            # Extract indicators_cached_at before session closes to avoid DetachedInstanceError
            # This is necessary because SQLAlchemy objects become detached when the session context exits
            stock_timestamps = []
            for stock in watched_stocks:
                try:
                    timestamp = stock.indicators_cached_at
                    stock_timestamps.append(timestamp)
                except Exception as e:
                    logger.warning(f"Error accessing indicators_cached_at for {stock.stock_code}: {e}")
                    # If we can't access the timestamp, assume refresh is needed
                    # This ensures we don't skip refreshing stocks with potential data issues
                    stock_timestamps.append(None)

            # Determine if any stock needs refresh based on cached timestamps
            needs_refresh = any(
                self._is_refresh_needed_with_timestamp(timestamp)
                for timestamp in stock_timestamps
            )

            # Trigger batch refresh if any stock's indicators are stale
            if needs_refresh:
                logger.info("Some indicators are stale, triggering refresh")
                await self._refresh_all_indicators()
            else:
                logger.info("All indicators are fresh, skipping refresh")

        except Exception as e:
            logger.error(f"Error checking if refresh is needed: {e}", exc_info=True)

    async def _refresh_all_indicators(self) -> None:
        """
        Refresh indicators for all watched stocks

        This fetches fresh indicators and updates the database.
        Individual stock failures are logged but don't stop the batch.
        """
        try:
            watched_stocks = self.repo.list(self.user_id)

            if not watched_stocks:
                logger.info("No watched stocks to refresh")
                return

            stock_codes = [stock.stock_code for stock in watched_stocks]
            logger.info(f"Refreshing indicators for {len(stock_codes)} stocks: {stock_codes}")

            # Batch fetch indicators from the data source
            # This is more efficient than fetching each stock individually
            indicators_data = self.indicators_service.get_indicators(stock_codes)

            # Update each stock's cached indicators in the database
            # Individual failures are logged but don't stop the batch operation
            success_count = 0
            failure_count = 0

            for stock in watched_stocks:
                code = stock.stock_code
                if code in indicators_data:
                    try:
                        # Update the cached indicators in the database
                        success = self.repo.update_cached_indicators(
                            code,
                            indicators_data[code],
                            self.user_id
                        )
                        if success:
                            success_count += 1
                        else:
                            failure_count += 1
                            logger.warning(f"Failed to update cached indicators for {code}")
                    except Exception as e:
                        # Log error but continue with other stocks
                        failure_count += 1
                        logger.error(f"Error updating {code} indicators: {e}", exc_info=True)
                else:
                    # No data returned for this stock - possibly invalid code or API issue
                    failure_count += 1
                    logger.warning(f"No indicators data returned for {code}")

            # Log summary of the refresh operation
            logger.info(
                f"Refresh complete: {success_count} succeeded, {failure_count} failed"
            )

        except Exception as e:
            logger.error(f"Error refreshing all indicators: {e}", exc_info=True)

    def _is_refresh_needed(self, stock) -> bool:
        """
        Check if a stock's indicators need refreshing

        Args:
            stock: WatchedStock object

        Returns:
            True if indicators are stale (older than threshold) or never cached
        """
        # If indicators were never cached, refresh is needed
        if stock.indicators_cached_at is None:
            return True

        # Check if indicators are older than the threshold
        time_since_refresh = datetime.now() - stock.indicators_cached_at
        threshold = timedelta(hours=self.refresh_interval_hours)

        return time_since_refresh > threshold

    def _is_refresh_needed_with_timestamp(self, cached_at) -> bool:
        """
        Check if indicators need refreshing given a timestamp

        This helper method avoids DetachedInstanceError by working with timestamps
        directly instead of accessing attributes on detached SQLAlchemy objects.

        Args:
            cached_at: datetime object or None representing when indicators were cached

        Returns:
            True if indicators are stale (older than threshold) or never cached
        """
        # If indicators were never cached, refresh is needed
        if cached_at is None:
            return True

        # Check if indicators are older than the threshold
        time_since_refresh = datetime.now() - cached_at
        threshold = timedelta(hours=self.refresh_interval_hours)

        return time_since_refresh > threshold

    async def _run_refresh_loop(self) -> None:
        """
        Run the periodic refresh loop

        This runs in the background and triggers a refresh every refresh_interval_hours.
        The loop continues until stop() is called.
        """
        try:
            while self._running:
                # Sleep for the configured interval (in seconds)
                # Convert hours to seconds: refresh_interval_hours * 3600
                await asyncio.sleep(self.refresh_interval_hours * 3600)

                # Double-check if still running before proceeding
                # This handles the case where stop() is called during the sleep period
                if not self._running:
                    break

                logger.info("Periodic refresh triggered")
                await self._refresh_all_indicators()

        except asyncio.CancelledError:
            # Gracefully handle task cancellation when stop() is called
            logger.debug("Refresh loop cancelled")
            raise
        except Exception as e:
            # Log any unexpected errors but don't crash the loop
            # The loop will continue after logging the error
            logger.error(f"Error in refresh loop: {e}", exc_info=True)
