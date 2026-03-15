# chronos-core-oss — TODO

## MVP Vision

Turn a strategy template into a venue-aware, risk-disciplined, replayable trade decision
for a single underlying, with full visibility into what was taken, skipped, and why.

**MVP structure scope:** single-stock trades and two-leg options structures only.

**MVP product sequence:** Manual Trade Workbench first. Bot Studio stays behind it.

**MVP data rule:** no paid data. Stock candles come from Yahoo Finance. Options chain data also comes from Yahoo Finance for now.

**MVP architecture rule:** all external dependencies are adapter-first.
At minimum: `PriceAdapter`, `OptionChainAdapter`, `VenueAdapter`, `ExecutionAdapter`, `AccountStateAdapter`.
Yahoo Finance is just the first implementation, not the product contract.

**Cleanup rule:** if a file would require more than 80% rewrite to fit this direction, delete it instead of carrying it forward.

---

## Current Codebase Gap Map

### Reuse as foundation

- [x] `stocks`, `stock_ohlcv`, `stock_signals`, `stock_price_cache`
- [x] Yahoo-backed price adapter shape in `api/services/provider_registry.py`
- [x] Yahoo data fetch implementation in `api/services/providers/yahooquery_adapter.py`
- [x] OHLCV persistence in `api/ohlcv.py`
- [x] TA computation in `api/services/ta/*`
- [x] Basic `StrategyTemplate` CRUD path

### Repurpose, not preserve as-is

- [ ] `ScanRun` -> `EvaluationRun`
- [ ] `TradeCandidate` -> `Candidate`
- [ ] `refresh_stock_prices()` survives, but not the universe-driven refresh loop
- [ ] Frontend page shell can survive, but not the current universe/scan workflow

### Hard gaps against the new product

- [ ] No manual-trade evaluation flow centered on `template + underlying`
- [ ] No options chain contract or persistence shape
- [ ] No adapter boundary for options chain, execution, venue rules, or account state
- [ ] No `DecisionLedger`
- [ ] No `PositionLifecycle`
- [ ] No reason-code stage records
- [ ] No typed `MarketSnapshot`, `RegimeSnapshot`, or `PortfolioSnapshot`
- [ ] No execution intent model

### Nuke in cleanup pass

- [ ] Delete `api/chronos.db` and recreate the schema from the corrected MVP model
- [ ] Delete `Universe`, `UniverseMember`, and the universe-first API/UI flow
- [ ] Delete `TemplateKind` enum and move to strategy-only templates
- [ ] Delete universe-batch candidate generation in `api/services/candidate_engine.py`
- [ ] Delete scan-first naming and endpoints as the primary product surface
- [ ] Delete or archive tests that assert universe-scan behavior as the happy path

---

## Cleanup Pass

### Schema + backend deletion tasks

- [ ] **C-01** Remove `api/chronos.db` from the working tree and verify startup recreates a fresh DB
- [ ] **C-02** Delete `Universe`, `UniverseMember`, and related Pydantic request/response models from `api/models.py`
- [ ] **C-03** Delete `api/repositories/universes.py`
- [ ] **C-04** Delete universe membership helpers from `api/repositories/stocks.py` and keep only canonical stock helpers
- [ ] **C-05** Delete `api/routers/universes.py` and remove the router from `api/main.py`
- [ ] **C-06** Delete `UniverseScanRequest`, `UniverseScanResponse`, `ScanStatus`, and `ScanRun`
- [ ] **C-07** Delete `api/services/scan.py`
- [ ] **C-08** Delete universe-batch logic from `api/services/candidate_engine.py`
- [ ] **C-09** Remove `TemplateKind` and make `StrategyTemplate` strategy-only in model, repo, and router contracts
- [ ] **C-10** Delete the universe-driven background refresh model from `api/services/refresh_prices.py`, preserving only on-demand per-underlying refresh helpers

### Frontend deletion tasks

- [ ] **C-11** Delete `web/src/features/universe/UniversePanel.tsx`
- [ ] **C-12** Delete `web/src/features/universe/UniverseFormPanel.tsx`
- [ ] **C-13** Delete `web/src/features/scan/RunScanPanel.tsx`
- [ ] **C-14** Delete `web/src/features/candidates/CandidatesPanel.tsx`
- [ ] **C-15** Delete universe/scan actions from `web/src/app/actions.ts`
- [ ] **C-16** Remove universe/scan types and client calls from `web/src/lib/api.ts`
- [ ] **C-17** Replace the current homepage composition in `web/src/app/page.tsx` with a manual workbench shell

### Test cleanup tasks

- [ ] **C-18** Delete universe-scan tests in `api/tests/test_scan_flow.py`
- [ ] **C-19** Add a minimal startup smoke test that only checks `GET /healthz`

### Migration foundation tasks

- [ ] **C-20** Add a real migration toolchain for the API schema instead of relying on `metadata.create_all()`
- [ ] **C-21** Add an initial baseline migration for the post-cleanup schema
- [ ] **C-22** Refactor app startup so schema changes run through migrations, not automatic table creation
- [ ] **C-23** Add a documented local workflow for `upgrade`, `downgrade`, and creating new revisions
- [ ] **C-24** Add a test path that boots a fresh database through migrations only

---

## MVP Phase 0 — Pre-Brokerage Manual Trade Workbench

Goal: one user can pick a strategy template, type one underlying, evaluate it, inspect the reasons,
approve a simulated open, and see the resulting position state.

This phase stops at a trustworthy local sim loop.
Do not start brokerage automation or Bot Studio work until this loop is complete.

### Adapter boundaries

- [ ] **P0-01** Create a typed `PriceAdapter` contract for bar history reads
- [ ] **P0-02** Create a typed `OptionChainAdapter` contract for normalized chain snapshots
- [ ] **P0-03** Create a typed `VenueAdapter` contract for venue profile and order-rule lookups
- [ ] **P0-04** Create a typed `ExecutionAdapter` contract for `open` intents in sim mode
- [ ] **P0-05** Create a typed `AccountStateAdapter` contract for buying power, cash, and open positions
- [ ] **P0-06** Refactor the existing Yahoo price provider to implement the new `PriceAdapter` contract cleanly
- [ ] **P0-07** Add a Yahoo Finance options chain adapter that returns a normalized, adapter-owned schema
- [ ] **P0-08** Add a local sim execution adapter stub that can accept an `ExecutionIntent` and emit a fill result

### Template + domain model

- [ ] **P0-09** Redefine template config schema to include `entry_rules`, `exit_rules`, `leg_selection_policy`, and `risk_hooks`
- [ ] **P0-10** Update template validation so the API accepts only the new strategy schema
- [ ] **P0-11** Add `EvaluationRun` model with `underlying`, `trigger_source`, `template_id`, `status`, `started_at`, `ended_at`
- [ ] **P0-12** Add `Candidate` model with `run_id`, `underlying`, `proposed_legs_json`, `reason_codes_json`, `stage_results_json`
- [ ] **P0-13** Add `DecisionLedgerEntry` model with `run_id`, `stage`, `outcome`, `reason_codes_json`, `snapshot_refs_json`, `input_hash`
- [ ] **P0-14** Add `ExecutionIntent` model or typed artifact for `open` and `no_action`
- [ ] **P0-15** Add minimal `PositionLifecycle` model for open/close tracking of one stock or one two-leg options structure

### Postgres-ready schema discipline

- [ ] **P0-16** Define database conventions for IDs, timestamps, foreign keys, indexes, and nullable rules before adding new tables
- [ ] **P0-17** Decide which payload columns remain JSON strings in SQLite now but should become `JSONB` on Postgres later
- [ ] **P0-18** Add indexes for the expected hot paths: runs, ledger entries, positions, orders, and fills
- [ ] **P0-19** Make enum and status modeling portable so it can move cleanly from SQLite to Postgres
- [ ] **P0-20** Add explicit `created_at` and `updated_at` rules for mutable operational tables

### Snapshot assembly

- [ ] **P0-21** Define a typed `MarketSnapshot` contract for one underlying
- [ ] **P0-22** Build stock snapshot assembly from Yahoo bars + existing TA signals
- [ ] **P0-23** Define a typed `OptionChainSnapshot` contract with expiries, strikes, bid/ask, mid, IV, and DTE
- [ ] **P0-24** Build option chain snapshot assembly through the Yahoo chain adapter
- [ ] **P0-25** Define a stub `RegimeSnapshot` contract with `label`, `confidence`, and `posture`
- [ ] **P0-26** Define a stub `PortfolioSnapshot` contract using the account-state adapter

### Evaluation pipeline

- [ ] **P0-27** Implement qualification-stage rule evaluation with deterministic PASS/FAIL outputs
- [ ] **P0-28** Introduce named reason codes for qualification failures
- [ ] **P0-29** Implement candidate construction for a single-stock long/short candidate
- [ ] **P0-30** Implement candidate construction for a two-leg put credit spread candidate
- [ ] **P0-31** Implement basic trade-level risk checks: max width, min credit, liquidity floor
- [ ] **P0-32** Implement basic portfolio checks: cash floor and max open-position count
- [ ] **P0-33** Emit a final `ExecutionIntent` or explicit `no_action` result
- [ ] **P0-34** Persist stage-by-stage ledger entries for one evaluation run

### Backend API

- [ ] **P0-35** Add `POST /evaluate` for manual `template + underlying` runs
- [ ] **P0-36** Add `GET /runs/{run_id}` for evaluation run detail
- [ ] **P0-37** Add `GET /runs/{run_id}/ledger` for stage-by-stage trace output
- [ ] **P0-38** Add `POST /runs/{run_id}/approve` to convert an approved intent into a sim execution request
- [ ] **P0-39** Add `GET /positions` for open position listing
- [ ] **P0-40** Add `GET /positions/{position_id}` for lifecycle detail
- [ ] **P0-41** Add `POST /positions/{position_id}/close` for manual close in sim mode

### Frontend manual workbench

- [ ] **P0-42** Build a new `ManualTradeWorkbench` page shell
- [ ] **P0-43** Add template picker + underlying symbol input
- [ ] **P0-44** Add an Evaluate action wired to `POST /evaluate`
- [ ] **P0-45** Render qualification result and reason codes
- [ ] **P0-46** Render proposed structure details for stock and two-leg options candidates
- [ ] **P0-47** Render risk decision and final intent state
- [ ] **P0-48** Add an Approve button wired to sim execution
- [ ] **P0-49** Add a per-run decision trace panel
- [ ] **P0-50** Add an open positions panel
- [ ] **P0-51** Add a position detail panel with lifecycle status and close action

### Verification

- [ ] **P0-52** Add backend tests for `POST /evaluate` no-action cases
- [ ] **P0-53** Add backend tests for `POST /evaluate` candidate cases
- [ ] **P0-54** Add backend tests for ledger persistence across all stages
- [ ] **P0-55** Add backend tests for approve -> simulated fill -> open position
- [ ] **P0-56** Add one frontend smoke test or manual QA checklist for the workbench flow

---

## Phase 1 — Brokerage Integration

Goal: replace the local sim-only execution loop with a real broker-backed paper execution and reconciliation loop,
while keeping the same manual workbench and the same canonical decision engine.

Brokerage integration comes before Bot Studio because execution correctness, fill handling, and position reconciliation
are higher-risk foundations than scheduling.

### Broker selection + contracts

- [ ] **P1-01** Pick the first brokerage target for MVP paper execution and freeze the initial venue profile
- [ ] **P1-02** Extend `VenueAdapter` to cover contract specs, tick sizes, order constraints, and session rules
- [ ] **P1-03** Extend `ExecutionAdapter` to support broker paper order submission, cancel, and status refresh
- [ ] **P1-04** Extend `AccountStateAdapter` to support broker cash, buying power, open positions, and open orders
- [ ] **P1-05** Define normalized broker payload contracts for order acknowledgements, fills, rejects, and position snapshots

### SQLite-backed persistence for broker state

- [ ] **P1-06** Add `BrokerAccount` model for venue, account mode, account reference, and connection metadata
- [ ] **P1-07** Add `BrokerOrder` model linked to `ExecutionIntent` and `EvaluationRun`
- [ ] **P1-08** Add `BrokerFill` model linked to `BrokerOrder` and `PositionLifecycle`
- [ ] **P1-09** Add `BrokerPositionSnapshot` model for periodic broker-truth snapshots
- [ ] **P1-10** Add `BrokerSyncRun` model for import and reconciliation telemetry
- [ ] **P1-11** Add storage for raw broker payload JSON on orders, fills, rejects, and sync runs

### Postgres migration cutover

- [ ] **P1-12** Add Postgres driver and environment wiring alongside the existing local SQLite setup
- [ ] **P1-13** Create the first Postgres target configuration and verify the full schema builds from migrations
- [ ] **P1-14** Convert payload-heavy columns to their intended Postgres types where needed
- [ ] **P1-15** Verify indexes and constraints on Postgres for run, ledger, position, order, and fill hot paths
- [ ] **P1-16** Run a clean SQLite -> Postgres data migration for representative local data
- [ ] **P1-17** Make Postgres the default database for brokerage integration work

### Broker execution flow

- [ ] **P1-18** Implement the chosen broker paper adapter behind the existing execution contract
- [ ] **P1-19** Implement approval -> broker paper order submission from the manual workbench
- [ ] **P1-20** Persist broker order acknowledgements and map them back to local intents
- [ ] **P1-21** Persist fill events and update `PositionLifecycle` from broker fills
- [ ] **P1-22** Handle broker reject and cancel states with explicit reason codes
- [ ] **P1-23** Add manual refresh endpoint to pull latest broker order and fill state

### Reconciliation

- [ ] **P1-24** Build one-shot broker account sync for positions, orders, and balances
- [ ] **P1-25** Compare broker-truth positions against local `PositionLifecycle`
- [ ] **P1-26** Write reconciliation mismatches into the decision ledger and sync telemetry
- [ ] **P1-27** Add mismatch states such as `BROKER_POSITION_MISSING`, `LOCAL_POSITION_MISSING`, `QTY_MISMATCH`, `STATUS_MISMATCH`
- [ ] **P1-28** Add a manual reconciliation action in the workbench

### Frontend manual workbench upgrades

- [ ] **P1-29** Add broker mode and account display to the workbench
- [ ] **P1-30** Show broker order status, fill progress, and rejection state on approved runs
- [ ] **P1-31** Show broker-vs-local reconciliation status on each open position
- [ ] **P1-32** Add a broker sync history panel for the current account

### Verification

- [ ] **P1-33** Add tests for broker paper order submission success paths
- [ ] **P1-34** Add tests for broker reject and partial-fill handling
- [ ] **P1-35** Add tests for reconciliation mismatch detection and persistence
- [ ] **P1-36** Add an end-to-end manual QA checklist: evaluate -> approve -> broker paper order -> fill -> position reconcile

---

## Deferred Until Immediate Scope Is Complete

- Bot Studio
- Regime enrichment beyond the current stub contract
- Portfolio governor and other desk-control features
- Multi-bot supervision
- Replay and research expansion

---

## Deferred / Non-Goals

- Multi-leg options structures beyond two legs
- Multi-underlying bots
- Broad screener or universe board as the primary UX
- Autonomous live execution without approval
- Multiple venues simultaneously
- Paid market data in MVP
- Research workbench / parameter sweeps
- Strategy marketplace
- Full regime productization
- Heavy ML ranking
