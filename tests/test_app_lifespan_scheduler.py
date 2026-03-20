# -*- coding: utf-8 -*-
"""Unit tests for WatchListIndicatorScheduler integration with app_lifespan."""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from src.schedulers.watchlist_indicator_scheduler import WatchListIndicatorScheduler


class AppLifespanSchedulerTestCase(unittest.TestCase):
    """Test cases for scheduler integration in app_lifespan."""

    def test_scheduler_is_stored_in_app_state(self) -> None:
        """Test that scheduler instance is stored in app.state."""
        from api.app import create_app

        app = create_app()

        # Get the lifespan context
        lifespan = app.router.lifespan_context

        # Enter lifespan (startup) to initialize the scheduler
        async def run_lifespan():
            async with lifespan(app):
                # Check that scheduler is in app.state
                self.assertTrue(hasattr(app.state, 'watchlist_indicator_scheduler'))

                # Check that it's the correct type
                self.assertIsInstance(
                    app.state.watchlist_indicator_scheduler,
                    WatchListIndicatorScheduler
                )

        asyncio.run(run_lifespan())

    def test_scheduler_start_called_on_startup(self) -> None:
        """Test that scheduler.start() is called when app starts up."""
        from api.app import create_app

        # Mock the scheduler's start method
        with patch.object(
            WatchListIndicatorScheduler,
            'start',
            new_callable=AsyncMock
        ) as mock_start:
            # Create app and trigger lifespan
            app = create_app()

            # Get the lifespan context
            lifespan = app.router.lifespan_context

            # Enter lifespan (startup)
            async def run_lifespan():
                async with lifespan(app):
                    pass

            asyncio.run(run_lifespan())

            # Verify start was called
            mock_start.assert_called_once()

    def test_scheduler_stop_called_on_shutdown(self) -> None:
        """Test that scheduler.stop() is called when app shuts down."""
        from api.app import create_app

        # Mock the scheduler's stop method
        with patch.object(
            WatchListIndicatorScheduler,
            'stop',
            new_callable=AsyncMock
        ) as mock_stop:
            # Create app and trigger lifespan
            app = create_app()

            # Get the lifespan context
            lifespan = app.router.lifespan_context

            # Enter and exit lifespan (startup and shutdown)
            async def run_lifespan():
                async with lifespan(app):
                    pass

            asyncio.run(run_lifespan())

            # Verify stop was called
            mock_stop.assert_called_once()

    def test_scheduler_refresh_if_needed_called_on_startup(self) -> None:
        """Test that scheduler.refresh_if_needed() is called on startup.

        Since start() fires refresh_if_needed as a background task (non-blocking),
        we need to yield control to let the task run before asserting.
        """
        from api.app import create_app

        with patch.object(
            WatchListIndicatorScheduler,
            'refresh_if_needed',
            new_callable=AsyncMock
        ) as mock_refresh:
            app = create_app()
            lifespan = app.router.lifespan_context

            async def run_lifespan():
                async with lifespan(app):
                    # Yield control so background tasks (create_task) can execute
                    await asyncio.sleep(0)

            asyncio.run(run_lifespan())

            mock_refresh.assert_called_once()


if __name__ == '__main__':
    unittest.main()
