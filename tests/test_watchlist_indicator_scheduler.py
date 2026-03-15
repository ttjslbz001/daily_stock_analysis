# -*- coding: utf-8 -*-
"""Unit tests for WatchListIndicatorScheduler."""

import asyncio
import unittest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.schedulers.watchlist_indicator_scheduler import WatchListIndicatorScheduler
from src.repositories.watched_stocks_repo import WatchedStocksRepository
from src.services.technical_indicators_service import TechnicalIndicatorsService
from src.storage import WatchedStock


class WatchListIndicatorSchedulerTestCase(unittest.TestCase):
    """Test cases for WatchListIndicatorScheduler."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        # Mock dependencies
        self.mock_repo = MagicMock(spec=WatchedStocksRepository)
        self.mock_indicators_service = MagicMock(spec=TechnicalIndicatorsService)

        # Create scheduler instance
        self.scheduler = WatchListIndicatorScheduler(
            repo=self.mock_repo,
            indicators_service=self.mock_indicators_service,
            refresh_interval_hours=8,
        )

    def tearDown(self) -> None:
        """Clean up after tests."""
        # Ensure any running tasks are cancelled
        if self.scheduler._refresh_task is not None and not self.scheduler._refresh_task.done():
            self.scheduler._refresh_task.cancel()

    def test_init_creates_scheduler(self) -> None:
        """Test that scheduler initializes correctly."""
        self.assertIsNotNone(self.scheduler)
        self.assertEqual(self.scheduler.refresh_interval_hours, 8)
        self.assertEqual(self.scheduler._refresh_task, None)
        self.assertFalse(self.scheduler._running)

    def test_is_refresh_needed_returns_true_for_none_timestamp(self) -> None:
        """Test that refresh is needed when indicators_cached_at is None."""
        mock_stock = MagicMock(spec=WatchedStock)
        mock_stock.indicators_cached_at = None

        self.assertTrue(self.scheduler._is_refresh_needed(mock_stock))

    def test_is_refresh_needed_returns_true_for_old_timestamp(self) -> None:
        """Test that refresh is needed when indicators are older than threshold."""
        mock_stock = MagicMock(spec=WatchedStock)
        # 9 hours ago - older than 8 hour threshold
        mock_stock.indicators_cached_at = datetime.now() - timedelta(hours=9)

        self.assertTrue(self.scheduler._is_refresh_needed(mock_stock))

    def test_is_refresh_needed_returns_false_for_fresh_timestamp(self) -> None:
        """Test that refresh is not needed when indicators are fresh."""
        mock_stock = MagicMock(spec=WatchedStock)
        # 4 hours ago - fresher than 8 hour threshold
        mock_stock.indicators_cached_at = datetime.now() - timedelta(hours=4)

        self.assertFalse(self.scheduler._is_refresh_needed(mock_stock))

    def test_is_refresh_needed_returns_true_for_exactly_old_timestamp(self) -> None:
        """Test that refresh is needed when indicators are exactly at threshold."""
        mock_stock = MagicMock(spec=WatchedStock)
        # Exactly 8 hours ago - at threshold
        mock_stock.indicators_cached_at = datetime.now() - timedelta(hours=8)

        self.assertTrue(self.scheduler._is_refresh_needed(mock_stock))

    def test_refresh_all_indicators_success(self) -> None:
        """Test successful refresh of all indicators."""
        # Set up mock data
        mock_stock1 = MagicMock(spec=WatchedStock)
        mock_stock1.user_id = 'default_user'
        mock_stock1.stock_code = '600519'

        mock_stock2 = MagicMock(spec=WatchedStock)
        mock_stock2.user_id = 'default_user'
        mock_stock2.stock_code = '000001'

        self.mock_repo.list.return_value = [mock_stock1, mock_stock2]

        mock_indicators = {
            'price': 100.0,
            'change': 1.0,
            'change_percent': 1.0,
            'bollinger': {'upper': 110, 'middle': 100, 'lower': 90},
            'macd': {'dif': 0.5, 'dea': 0.4, 'bar': 0.1},
            'rsi': {'rsi6': 60, 'rsi12': 55, 'rsi24': 50},
            'kdj': {'k': 65, 'd': 60, 'j': 75},
            'volume': 1000000,
            'year_high': 150,
            'year_low': 80,
            'stock_name': 'Test Stock'
        }

        self.mock_indicators_service.get_indicators.return_value = {
            '600519': mock_indicators,
            '000001': mock_indicators
        }

        self.mock_repo.update_cached_indicators.return_value = True

        # Run refresh
        asyncio.run(self.scheduler._refresh_all_indicators())

        # Verify
        self.mock_repo.list.assert_called_once_with('default_user')
        self.mock_indicators_service.get_indicators.assert_called_once_with(['600519', '000001'])
        self.assertEqual(self.mock_repo.update_cached_indicators.call_count, 2)

    def test_refresh_all_indicators_handles_individual_failures(self) -> None:
        """Test that refresh continues even if individual stock fails."""
        mock_stock1 = MagicMock(spec=WatchedStock)
        mock_stock1.user_id = 'default_user'
        mock_stock1.stock_code = '600519'

        mock_stock2 = MagicMock(spec=WatchedStock)
        mock_stock2.user_id = 'default_user'
        mock_stock2.stock_code = '000001'

        self.mock_repo.list.return_value = [mock_stock1, mock_stock2]

        mock_indicators = {
            'price': 100.0,
            'change': 1.0,
            'change_percent': 1.0,
            'bollinger': {'upper': 110, 'middle': 100, 'lower': 90},
            'macd': {'dif': 0.5, 'dea': 0.4, 'bar': 0.1},
            'rsi': {'rsi6': 60, 'rsi12': 55, 'rsi24': 50},
            'kdj': {'k': 65, 'd': 60, 'j': 75},
            'volume': 1000000,
            'year_high': 150,
            'year_low': 80,
            'stock_name': 'Test Stock'
        }

        # Return data for first stock, empty for second
        self.mock_indicators_service.get_indicators.return_value = {
            '600519': mock_indicators,
            '000001': mock_indicators
        }

        # First update succeeds, second fails
        call_count = [0]
        def mock_update(stock_code, indicators, user_id=None):
            call_count[0] += 1
            if call_count[0] == 2:
                return False
            return True

        self.mock_repo.update_cached_indicators.side_effect = mock_update

        # Should not raise exception
        asyncio.run(self.scheduler._refresh_all_indicators())

        # Both attempts should have been made
        self.assertEqual(self.mock_repo.update_cached_indicators.call_count, 2)

    def test_refresh_if_needed_refreshes_when_stale(self) -> None:
        """Test that refresh_if_needed triggers refresh when indicators are stale."""
        mock_stock = MagicMock(spec=WatchedStock)
        mock_stock.user_id = 'default_user'
        mock_stock.stock_code = '600519'
        mock_stock.indicators_cached_at = datetime.now() - timedelta(hours=10)

        self.mock_repo.list.return_value = [mock_stock]

        mock_indicators = {
            'price': 100.0,
            'change': 1.0,
            'change_percent': 1.0,
            'bollinger': {'upper': 110, 'middle': 100, 'lower': 90},
            'macd': {'dif': 0.5, 'dea': 0.4, 'bar': 0.1},
            'rsi': {'rsi6': 60, 'rsi12': 55, 'rsi24': 50},
            'kdj': {'k': 65, 'd': 60, 'j': 75},
            'volume': 1000000,
            'year_high': 150,
            'year_low': 80,
            'stock_name': 'Test Stock'
        }

        self.mock_indicators_service.get_indicators.return_value = {'600519': mock_indicators}
        self.mock_repo.update_cached_indicators.return_value = True

        asyncio.run(self.scheduler.refresh_if_needed())

        # Should have called get_indicators because refresh was needed
        self.mock_indicators_service.get_indicators.assert_called_once_with(['600519'])

    def test_refresh_if_needed_skips_when_fresh(self) -> None:
        """Test that refresh_if_needed skips refresh when indicators are fresh."""
        mock_stock = MagicMock(spec=WatchedStock)
        mock_stock.user_id = 'default_user'
        mock_stock.stock_code = '600519'
        mock_stock.indicators_cached_at = datetime.now() - timedelta(hours=2)

        self.mock_repo.list.return_value = [mock_stock]

        asyncio.run(self.scheduler.refresh_if_needed())

        # Should NOT have called get_indicators because refresh was not needed
        self.mock_indicators_service.get_indicators.assert_not_called()

    def test_refresh_if_needed_handles_empty_watchlist(self) -> None:
        """Test that refresh_if_needed handles empty watchlist gracefully."""
        self.mock_repo.list.return_value = []

        # Should not raise exception
        asyncio.run(self.scheduler.refresh_if_needed())

        self.mock_indicators_service.get_indicators.assert_not_called()

    def test_start_and_stop_scheduler(self) -> None:
        """Test that scheduler can be started and stopped."""
        # Start the scheduler
        asyncio.run(self.scheduler.start())

        self.assertTrue(self.scheduler._running)
        self.assertIsNotNone(self.scheduler._refresh_task)

        # Stop the scheduler
        asyncio.run(self.scheduler.stop())

        self.assertFalse(self.scheduler._running)

    def test_stop_without_start_does_not_error(self) -> None:
        """Test that stopping scheduler without starting doesn't error."""
        # Should not raise exception
        asyncio.run(self.scheduler.stop())

        self.assertFalse(self.scheduler._running)

    def test_custom_refresh_interval(self) -> None:
        """Test that custom refresh interval is respected."""
        scheduler = WatchListIndicatorScheduler(
            repo=self.mock_repo,
            indicators_service=self.mock_indicators_service,
            refresh_interval_hours=4,
        )

        self.assertEqual(scheduler.refresh_interval_hours, 4)

    def test_custom_user_id(self) -> None:
        """Test that custom user_id is respected."""
        scheduler = WatchListIndicatorScheduler(
            repo=self.mock_repo,
            indicators_service=self.mock_indicators_service,
            refresh_interval_hours=8,
            user_id='custom_user',
        )

        self.assertEqual(scheduler.user_id, 'custom_user')

    def test_default_refresh_interval_from_env(self) -> None:
        """Test that default refresh interval is read from environment variable."""
        import os

        # Save original value
        original_value = os.environ.get('WATCHLIST_REFRESH_INTERVAL_HOURS')

        try:
            # Set environment variable
            os.environ['WATCHLIST_REFRESH_INTERVAL_HOURS'] = '12'

            # Create scheduler without specifying refresh_interval_hours
            scheduler = WatchListIndicatorScheduler(
                repo=self.mock_repo,
                indicators_service=self.mock_indicators_service,
            )

            # Should use value from environment variable
            self.assertEqual(scheduler.refresh_interval_hours, 12)
        finally:
            # Restore original value
            if original_value is None:
                os.environ.pop('WATCHLIST_REFRESH_INTERVAL_HOURS', None)
            else:
                os.environ['WATCHLIST_REFRESH_INTERVAL_HOURS'] = original_value

    def test_default_refresh_interval_when_env_not_set(self) -> None:
        """Test that default refresh interval is 8 when env variable not set."""
        import os

        # Save original value
        original_value = os.environ.get('WATCHLIST_REFRESH_INTERVAL_HOURS')

        try:
            # Remove environment variable
            os.environ.pop('WATCHLIST_REFRESH_INTERVAL_HOURS', None)

            # Create scheduler without specifying refresh_interval_hours
            scheduler = WatchListIndicatorScheduler(
                repo=self.mock_repo,
                indicators_service=self.mock_indicators_service,
            )

            # Should use default value of 8
            self.assertEqual(scheduler.refresh_interval_hours, 8)
        finally:
            # Restore original value
            if original_value is not None:
                os.environ['WATCHLIST_REFRESH_INTERVAL_HOURS'] = original_value

    def test_explicit_refresh_interval_overrides_env(self) -> None:
        """Test that explicit refresh_interval parameter overrides environment variable."""
        import os

        # Save original value
        original_value = os.environ.get('WATCHLIST_REFRESH_INTERVAL_HOURS')

        try:
            # Set environment variable to a different value
            os.environ['WATCHLIST_REFRESH_INTERVAL_HOURS'] = '12'

            # Create scheduler with explicit refresh_interval_hours
            scheduler = WatchListIndicatorScheduler(
                repo=self.mock_repo,
                indicators_service=self.mock_indicators_service,
                refresh_interval_hours=6,
            )

            # Should use explicit value, not environment variable
            self.assertEqual(scheduler.refresh_interval_hours, 6)
        finally:
            # Restore original value
            if original_value is None:
                os.environ.pop('WATCHLIST_REFRESH_INTERVAL_HOURS', None)
            else:
                os.environ['WATCHLIST_REFRESH_INTERVAL_HOURS'] = original_value


if __name__ == '__main__':
    unittest.main()
