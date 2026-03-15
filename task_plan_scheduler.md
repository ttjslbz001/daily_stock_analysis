# Task Plan: Watch List Indicator Scheduler

**Goal:** Create a scheduled task that refreshes watch list indicators every 8 hours, with a refresh on first startup if indicators are stale.

---

## Progress Summary

**Total Tasks:** 10
**Completed:** 3
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

- [ ] Task 2.1: Add scheduler to app_lifespan
  - File: `api/app.py`
  - Import and instantiate WatchListIndicatorScheduler
  - Call start() in lifespan setup
  - Call stop() in finally block
  - Store in app.state for access
  - Estimated time: 10 minutes

---

## Phase 3: Add Configuration Support (2 tasks)

- [ ] Task 3.1: Add environment variable configuration
  - File: `.env.example`
  - Add WATCHLIST_AUTO_REFRESH_ENABLED=true
  - Add WATCHLIST_REFRESH_INTERVAL_HOURS=8
  - Estimated time: 5 minutes

- [ ] Task 3.2: Load configuration in scheduler
  - File: `src/services/watchlist_indicator_scheduler.py`
  - Import environment loading
  - Check enabled flag before starting
  - Use interval from config
  - Estimated time: 10 minutes

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

- [ ] Task 4.3: Manual integration testing
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

**Phase:** 1 (Scheduler Service Complete - Testing Complete)
**Next Task:** Task 2.1 - Add scheduler to app_lifespan
**Recommended First Task:** Phase 2, Task 2.1

**Session Notes (2026-03-15):**
- Created WatchListIndicatorScheduler class in `src/schedulers/watchlist_indicator_scheduler.py`
- Implemented all required methods: __init__, start, stop, refresh_if_needed, _refresh_all_indicators, _is_refresh_needed, _run_refresh_loop
- Added comprehensive logging throughout
- Wrote 14 unit tests covering:
  - Initialization
  - Staleness checking (None, old, fresh, threshold scenarios)
  - Refresh logic (success, individual failures, empty watchlist)
  - Scheduler lifecycle (start/stop)
  - Configuration (custom interval, custom user_id)
- All 14 tests pass
- Existing test suite still passes (no regressions)
