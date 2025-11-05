# DEVLOG — Chronos Core OSS v0.01 

## Session 2 — 6 Nov 2025

Completed Phase 0.01 backend foundations.
 • Added repositories/stocks.py with get_or_create_stock, add_stock_to_universe, list_universe_stocks, remove_stock_from_universe.
 • Extended routers/universes.py with POST, GET, and DELETE for /universes/{id}/stocks.
 • Switched DELETE to operate by ticker instead of internal stock_id.
 • Verified full universe ↔ stock lifecycle: create universe → add ticker → list → unlink → delete universe.
 • UniverseMember now cleanly separates membership from canonical Stock, enabling shared data fetch and deduped OHLCV.

Next: introduce StockData cache + yahooquery fetcher for Phase 0.02.

## Session 1

Backend scaffold (Phase 0.01)

Initialized FastAPI app with lifespan startup that runs DB init.

Async SQLAlchemy 2.0 setup: DeclarativeBase, aiosqlite engine, async_sessionmaker, and shared get_session() dependency.

Core domain models:

Universe (id-only addressing; name not unique).

Stock (unique ticker normalized to uppercase).

UniverseMember (unique (universe_id, stock_id) join; cascade delete).

Pydantic v2 DTOs: UniverseCreate, UniverseRead (from_attributes=True).

Repositories:

universes: create, get_by_id, list, delete (awaited async delete).

API:

/universes: POST create, GET list, GET by id, DELETE by id.

Mounted router; Swagger/Redoc confirmed.

Tooling:

uv only (no venvs); added greenlet.

.gitignore hardened for Python/SQLite/caches/envs.

Notes vs Roadmap

This matches Phase 0.01 goals: define universes and start the data model needed for ticker membership.

Next logical slice: ticker ingestion path (repo + router under /universes/{id}/stocks) and a deduped data fetch layer.

Data source candidate: yahooquery for local-only EOD/metadata; add small cache and retries. No redistribution.

Open items / Next session

Add repositories/stocks.py: get_or_create_stock, add_stock_to_universe, list_universe_stocks.

Add /universes/{id}/stocks endpoints (POST add ticker, GET list, DELETE unlink).

Introduce yahooquery with a fetch service and on-disk cache keyed by (ticker, interval, window); ensure dedupe so TSLA isn’t re-downloaded for multiple users.
