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

---

## MVP Phase 0 — Manual Trade Workbench Initial Slice

Goal: one user can pick a strategy template, type one underlying, evaluate it, inspect the reasons,
approve a simulated open, and see the resulting position state.

Do not start Bot Studio work until this loop is complete.

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

### Snapshot assembly
- [ ] **P0-16** Define a typed `MarketSnapshot` contract for one underlying
- [ ] **P0-17** Build stock snapshot assembly from Yahoo bars + existing TA signals
- [ ] **P0-18** Define a typed `OptionChainSnapshot` contract with expiries, strikes, bid/ask, mid, IV, and DTE
- [ ] **P0-19** Build option chain snapshot assembly through the Yahoo chain adapter
- [ ] **P0-20** Define a stub `RegimeSnapshot` contract with `label`, `confidence`, and `posture`
- [ ] **P0-21** Define a stub `PortfolioSnapshot` contract using the account-state adapter

### Evaluation pipeline
- [ ] **P0-22** Implement qualification-stage rule evaluation with deterministic PASS/FAIL outputs
- [ ] **P0-23** Introduce named reason codes for qualification failures
- [ ] **P0-24** Implement candidate construction for a single-stock long/short candidate
- [ ] **P0-25** Implement candidate construction for a two-leg put credit spread candidate
- [ ] **P0-26** Implement basic trade-level risk checks: max width, min credit, liquidity floor
- [ ] **P0-27** Implement basic portfolio checks: cash floor and max open-position count
- [ ] **P0-28** Emit a final `ExecutionIntent` or explicit `no_action` result
- [ ] **P0-29** Persist stage-by-stage ledger entries for one evaluation run

### Backend API
- [ ] **P0-30** Add `POST /evaluate` for manual `template + underlying` runs
- [ ] **P0-31** Add `GET /runs/{run_id}` for evaluation run detail
- [ ] **P0-32** Add `GET /runs/{run_id}/ledger` for stage-by-stage trace output
- [ ] **P0-33** Add `POST /runs/{run_id}/approve` to convert an approved intent into a sim execution request
- [ ] **P0-34** Add `GET /positions` for open position listing
- [ ] **P0-35** Add `GET /positions/{position_id}` for lifecycle detail
- [ ] **P0-36** Add `POST /positions/{position_id}/close` for manual close in sim mode

### Frontend manual workbench
- [ ] **P0-37** Build a new `ManualTradeWorkbench` page shell
- [ ] **P0-38** Add template picker + underlying symbol input
- [ ] **P0-39** Add an Evaluate action wired to `POST /evaluate`
- [ ] **P0-40** Render qualification result and reason codes
- [ ] **P0-41** Render proposed structure details for stock and two-leg options candidates
- [ ] **P0-42** Render risk decision and final intent state
- [ ] **P0-43** Add an Approve button wired to sim execution
- [ ] **P0-44** Add a per-run decision trace panel
- [ ] **P0-45** Add an open positions panel
- [ ] **P0-46** Add a position detail panel with lifecycle status and close action

### Verification
- [ ] **P0-47** Add backend tests for `POST /evaluate` no-action cases
- [ ] **P0-48** Add backend tests for `POST /evaluate` candidate cases
- [ ] **P0-49** Add backend tests for ledger persistence across all stages
- [ ] **P0-50** Add backend tests for approve -> simulated fill -> open position
- [ ] **P0-51** Add one frontend smoke test or manual QA checklist for the workbench flow

---

## Phase 1 — Bot Studio (Leave High-Level For Now)

- [ ] Add `BotInstance` model
- [ ] Add bot CRUD + activation endpoints
- [ ] Add scheduler that reuses the same evaluation pipeline as manual runs
- [ ] Add bot creation UI
- [ ] Add bot dashboard UI
- [ ] Add broker paper execution adapter
- [ ] Add reconciliation before each bot run

---

## Phase 2 — Desk Control / Multi-Bot Supervision (Leave High-Level For Now)

- [ ] Add portfolio snapshot and shared governor policy model
- [ ] Add action queue and blocker analysis views
- [ ] Add multi-bot supervision UX
- [ ] Add portfolio-level analytics and replay support

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
