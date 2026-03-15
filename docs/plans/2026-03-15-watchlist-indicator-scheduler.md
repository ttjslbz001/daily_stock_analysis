# Implementation Plan: Watch List Indicator Scheduler

**Goal:** Create a scheduled task that refreshes watch list indicators every 8 hours, with a refresh on first startup if indicators are stale.

**Date:** 2026-03-15

**Approach:**
- Sliding window: 8 hours from last successful refresh
- Refresh on startup only if stale (older than 8 hours)
- Reuse existing `TechnicalIndicatorsService` for batch operations

---

## Architecture Overview

The solution will use FastAPI's `lifespan` events to:
1. **Startup:** Check if indicators are stale and trigger an initial refresh if needed
2. **Runtime:** Use `asyncio` to run a background task that refreshes every 8 hours

### Components

1. **WatchListIndicatorScheduler** - New service class in `src/services/`
   - Manages the 8-hour refresh cycle
   - Handles initial refresh on startup
   - Uses `TechnicalIndicatorsService` for actual data fetching

2. **FastAPI Lifespan Integration** - In `api/app.py`
   - Start the scheduler on app startup
   - Cancel the background task on app shutdown

3. **Configuration** - In `.env` or system config
   - `WATCHLIST_REFRESH_INTERVAL_HOURS` (default: 8)
   - `WATCHLIST_AUTO_REFRESH_ENABLED` (default: true)

---

## Implementation Tasks

### Phase 1: Create the Scheduler Service

#### Task 1.1: Create WatchListIndicatorScheduler class
**File:** `src/services/watchlist_indicator_scheduler.py`

**Steps:**
1. Create the new file with proper docstrings
2. Define the scheduler class with:
   - `__init__()` - Initialize with configurable interval
   - `start()` - Start the background refresh loop
   - `stop()` - Cancel the running background task
   - `refresh_if_needed()` - Check staleness and refresh if needed
   - `_refresh_all_indicators()` - Refresh all watched stocks in batch
   - `_is_refresh_needed()` - Check if any stock needs refresh
   - `_run_refresh_loop()` - Async loop that refreshes every 8 hours
3. Add comprehensive logging

**Verification:**
- The file is created with proper Python syntax
- All methods have docstrings
- Logging is configured

---

### Phase 2: Integrate with FastAPI Lifespan

#### Task 2.1: Add scheduler to app_lifespan
**File:** `api/app.py`

**Steps:**
1. Import `WatchListIndicatorScheduler`
2. In `app_lifespan()`, create scheduler instance and call `start()`
3. In the `finally` block, call `stop()` on the scheduler
4. Store scheduler in `app.state` for potential access

**Verification:**
- Scheduler starts on app startup
- Scheduler stops cleanly on app shutdown
- No errors in logs

---

### Phase 3: Add Configuration Support

#### Task 3.1: Add environment variable configuration
**File:** `.env.example`

**Steps:**
1. Add `WATCHLIST_AUTO_REFRESH_ENABLED=true`
2. Add `WATCHLIST_REFRESH_INTERVAL_HOURS=8`

**Verification:**
- Configuration is documented in `.env.example`

#### Task 3.2: Load configuration in scheduler
**File:** `src/services/watchlist_indicator_scheduler.py`

**Steps:**
1. Import environment variable loading from existing config
2. Check `WATCHLIST_AUTO_REFRESH_ENABLED` before starting
3. Use `WATCHLIST_REFRESH_INTERVAL_HOURS` for interval

**Verification:**
- Configuration is read from environment
- Can disable via environment variable

---

### Phase 4: Testing

#### Task 4.1: Write unit tests for scheduler
**File:** `tests/test_watchlist_indicator_scheduler.py`

**Steps:**
1. Test `_is_refresh_needed()` logic
2. Test `_refresh_all_indicators()` with mocked dependencies
3. Test scheduler start/stop lifecycle
4. Test configuration loading

**Verification:**
- All tests pass
- Coverage is reasonable

#### Task 4.2: Manual integration testing
**Steps:**
1. Start the server and check logs for initial refresh
2. Verify indicators are refreshed if stale
3. Verify no refresh if indicators are fresh
4. Wait for 8-hour interval (or simulate by changing config to short interval)
5. Verify periodic refresh happens

**Verification:**
- Initial refresh works correctly
- Periodic refresh works correctly
- Logs show expected behavior

---

### Phase 5: Documentation

#### Task 5.1: Update README
**File:** `README.md`

**Steps:**
1. Add section about automatic indicator refresh
2. Document the 8-hour interval
3. Document configuration options

**Verification:**
- README is updated
- Feature is documented

#### Task 5.2: Add inline code comments
**Steps:**
1. Add comments explaining the refresh logic
2. Add comments explaining the staleness check
3. Add comments explaining the background task lifecycle

**Verification:**
- Code is well-commented

---

## File Structure

```
daily_stock_analysis/
├── api/
│   ├── app.py                          # [MODIFY] Add scheduler to lifespan
├── src/
│   ├── services/
│   │   ├── watchlist_indicator_scheduler.py  # [NEW] Scheduler service
│   │   └── technical_indicators_service.py   # [EXISTING] Used by scheduler
│   └── repositories/
│       └── watched_stocks_repo.py      # [EXISTING] Used by scheduler
├── tests/
│   └── test_watchlist_indicator_scheduler.py  # [NEW] Unit tests
├── .env.example                        # [MODIFY] Add config
└── README.md                           # [MODIFY] Add documentation
```

---

## Design Decisions

### Why asyncio instead of threading?
- FastAPI is async-native
- Cleaner integration with FastAPI lifespan events
- Better resource management
- No risk of blocking the event loop (we use `asyncio.create_task()`)

### Why separate scheduler service?
- Separation of concerns
- Testable in isolation
- Reusable if needed in other contexts
- Clear ownership of the refresh logic

### Why use existing TechnicalIndicatorsService?
- Avoid code duplication
- Leverages existing optimizations
- Benefits from future improvements
- Consistent data format with API endpoints

---

## Error Handling Strategy

1. **Individual stock refresh failures:**
   - Log the error
   - Continue with other stocks
   - Don't fail the entire batch

2. **Repository failures:**
   - Log and return early
   - Don't start scheduler if DB is unavailable

3. **Scheduler loop failures:**
   - Catch and log exceptions
   - Continue the loop (don't crash)
   - Back off exponentially on repeated failures (optional enhancement)

---

## Future Enhancements (Out of Scope)

1. **Webhook notifications** when refresh completes
2. **Custom refresh intervals per stock** (e.g., more volatile stocks refresh more often)
3. **Parallel refresh with rate limiting** for large watch lists
4. **Metrics/monitoring** for refresh performance
5. **Manual trigger endpoint** for admin use
