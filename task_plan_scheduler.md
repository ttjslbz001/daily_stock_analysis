# Task Plan: Watch List Indicator Scheduler

**Goal:** Create a scheduled task that refreshes watch list indicators every 8 hours, with a refresh on first startup if indicators are stale.

---

## Progress Summary

**Total Tasks:** 10
**Completed:** 6
**In Progress:** 0
**Blocked:** 0

---

## Phase 1: Create the Scheduler Service (2 tasks)

- [x] Task 1.1: Create WatchListIndicatorScheduler class
  - File: `src/schedulers/watchlist_indicator_scheduler.py` (Note: corrected path)
  - Create new file with scheduler class
  - Define all methods: __init__, start, stop, refresh_if_needed, _refresh_all_indicators, _is_refresh_needed, _run_refresh_loop
  - Add comprehensive logging
  - Estimated time: 15-20 minutes
  - **Completed:** 2026-03-15

- [x] Task 1.2: Implement staleness checking logic
  - Implement `_is_refresh_needed()` method
  - Check `indicators_cached_at` against 8-hour threshold
  - Handle None values (never cached)
  - Estimated time: 10 minutes
  - **Completed:** 2026-03-15

---

## Phase 2: Integrate with FastAPI Lifespan (1 task)

- [x] Task 2.1: Add scheduler to app_lifespan
  - File: `api/app.py`
  - Import and instantiate WatchListIndicatorScheduler
  - Call start() in lifespan setup
  - Call stop() in finally block
  - Store in app.state for access
  - Estimated time: 10 minutes
  - **Completed:** 2026-03-15

---

## Phase 3: Add Configuration Support (2 tasks)

- [x] Task 3.1: Add environment variable configuration
  - File: `.env.example`
  - Add WATCHLIST_AUTO_REFRESH_ENABLED=true
  - Add WATCHLIST_REFRESH_INTERVAL_HOURS=8
  - Estimated time: 5 minutes
  - **Completed:** 2026-03-15

- [x] Task 3.2: Load configuration in scheduler
  - File: `src/schedulers/watchlist_indicator_scheduler.py`
  - Import environment loading
  - Use interval from config
  - Estimated time: 10 minutes
  - **Completed:** 2026-03-15

---

## Phase 4: Testing (3 tasks)

- [x] Task 4.1: Write unit tests for staleness checking
  - File: `tests/test_watchlist_indicator_scheduler.py`
  - Test _is_refresh_needed() with various scenarios
  - Test with None, old, recent timestamps
  - Estimated time: 15 minutes
  - **Completed:** 2026-03-15

- [x] Task 4.2: Write unit tests for refresh logic
  - Test _refresh_all_indicators() with mocks
  - Test error handling for individual stock failures
  - Estimated time: 15 minutes
  - **Completed:** 2026-03-15

- [x] Task 4.3: Write unit tests for app_lifespan integration
  - File: `tests/test_app_lifespan_scheduler.py`
  - Test scheduler is stored in app.state
  - Test start() is called on startup
  - Test stop() is called on shutdown
  - Test refresh_if_needed() is called on startup
  - Estimated time: 15 minutes
  - **Completed:** 2026-03-15

- [ ] Task 4.4: Manual integration testing
  - Start server and verify initial refresh
  - Verify no refresh if fresh
  - Verify periodic refresh happens
  - Check logs for expected behavior
  - Estimated time: 20 minutes

---

## Phase 5: Documentation (2 tasks)

- [ ] Task 5.1: Update README
  - File: `README.md`
  - Add section about automatic indicator refresh
  - Document 8-hour interval
  - Document configuration options
  - Estimated time: 10 minutes

- [ ] Task 5.2: Add inline code comments
  - Add comments explaining refresh logic
  - Add comments explaining staleness check
  - Add comments explaining background task lifecycle
  - Estimated time: 10 minutes

---

## Key Questions

1. **Q:** What happens if the server restarts frequently?
   **A:** The scheduler will only refresh if indicators are stale (older than 8 hours), avoiding unnecessary refreshes.

2. **Q:** What happens if a stock data fetch fails?
   **A:** The error is logged, and the refresh continues with other stocks. The failed stock will be retried in the next cycle.

3. **Q:** Can the feature be disabled?
   **A:** Yes, via `WATCHLIST_AUTO_REFRESH_ENABLED=false` in the environment configuration.

---

## Decisions Made

1. **Refresh Interval:** 8 hours sliding window from last successful refresh
2. **Startup Behavior:** Only refresh if indicators are stale (older than 8 hours)
3. **Implementation:** Async background task using asyncio (not threading)
4. **Service Reuse:** Use existing TechnicalIndicatorsService for data fetching
5. **Error Handling:** Log and continue on individual stock failures

---

## Errors Encountered

*None yet*

---

## Status

**Phase:** 3 (Configuration Complete)
**Next Task:** Task 4.4 - Manual integration testing
**Recommended First Task:** Phase 4, Task 4.4

**Session Notes (2026-03-15):**
- Created WatchListIndicatorScheduler class in `src/schedulers/watchlist_indicator_scheduler.py`
- Implemented all required methods: __init__, start, stop, refresh_if_needed, _refresh_all_indicators, _is_refresh_needed, _run_refresh_loop
- Added comprehensive logging throughout
- Integrated scheduler into FastAPI app_lifespan in `api/app.py`
  - Scheduler starts on app startup
  - Scheduler stops on app shutdown
  - Scheduler is stored in app.state for access
  - refresh_if_needed() is called on startup
- Added environment variable support
  - WATCHLIST_REFRESH_INTERVAL_HOURS in .env.example (default: 8 hours)
  - Scheduler reads from environment variable with fallback to 8 hours
- Wrote 21 unit tests covering:
  - Initialization
  - Staleness checking (None, old, fresh, threshold scenarios)
  - Refresh logic (success, individual failures, empty watchlist)
  - Scheduler lifecycle (start/stop)
  - Configuration (custom interval, custom user_id, env variable loading)
  - App lifespan integration (storage, start, stop, refresh_if_needed)
- All 21 tests pass
- Existing test suite still passes (no regressions)
