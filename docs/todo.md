# chronos-core-oss — TODO

## MVP Vision

Turn a strategy template into a venue-aware, risk-disciplined, replayable trade decision
for a single underlying, with full visibility into what was taken, skipped, and why.

**MVP structure scope:** single-stock trades and two-leg options structures (e.g. put credit spread).
No multi-leg structures (iron condors, butterflies) in MVP.

**MVP product sequence:** Manual Trade Workbench first → Bot Studio layered on top.

---

## Current Architecture Status

### Salvageable
- [x] `StrategyTemplate` model + CRUD (`entry_rules`, `config_json`)
- [x] `TradeCandidate` model + basic pipeline
- [x] `ScanRun` lifecycle tracking
- [x] OHLCV ingestion via `yahooquery`
- [x] TA signal computation (RSI, MACD, EMA, BB)
- [x] Frontend workflow panels

### Misaligned with MVP — must change
- [ ] `Universe` is the primary UX organizer → should be a supporting input concept only
- [ ] `Candidate` tied to `universe_id` → should be tied to strategy + underlying + run
- [ ] No options chain data model (IV rank, strikes, DTE)
- [ ] No `PositionLifecycle` model
- [ ] No `DecisionLedger` / reason-code infrastructure
- [ ] No `RegimeSnapshot` contract
- [ ] No execution intent / adapter layer

### Nuke / archive
- `Universe` as primary UX entry point in frontend and backend (keep model as a watchlist helper)
- `TemplateKind` enum (`risk` / `trade` / `strategy`) — premature, not meaningful
- `candidate_engine.py` universe-batch scan loop → replace with single-underlying evaluation pipeline
- `scan` router (as primary named surface) → repurpose to `evaluate`

---

## Phase 0 — Domain Model Correction
*Get the data model right before building more product.*

- [ ] **0.1 Extend `StrategyTemplate` schema**
  - `config_json` to support: `entry_rules`, `exit_rules`, `leg_selection_policy`, `risk_hooks`
  - Deprecate `TemplateKind` enum; settle on `strategy` as the single concept
  - Done when: a put credit spread (two-leg) can be fully described in the template schema

- [ ] **0.2 Refactor `Candidate`** (rename from `TradeCandidate`)
  - Drop `universe_id`; add `underlying`, `run_id`, `proposed_legs_json` (max two legs in MVP), `reason_codes`, `stage_results_json`
  - Done when: a candidate is self-describing without needing a universe lookup

- [ ] **0.3 Add `EvaluationRun` model** (extends `ScanRun`)
  - Fields: `underlying`, `trigger_source` (manual / scheduled), `template_id`, `status`, `started_at`, `ended_at`
  - Done when: every evaluation produces a traceable run record

- [ ] **0.4 Add `DecisionLedger` model**
  - Fields: `run_id`, `stage`, `outcome`, `reason_codes`, `snapshot_refs_json`, `input_hash`, `timestamp`
  - Done when: every run writes ledger entries for each pipeline stage

- [ ] **0.5 Add `PositionLifecycle` model** (stub — fleshed out in Phase 2)
  - Fields: `underlying`, `legs_json` (max two), `open_fill`, `status`, `close_reason`, `opened_at`, `closed_at`
  - Done when: an open position (single-stock or two-leg options) can be recorded and queried

---

## Phase 1 — Evaluation Pipeline (Engine Core)
*A single underlying can be evaluated through the full pipeline, producing a candidate or a reason-coded no-action result.*

- [ ] **1.1 `MarketSnapshot` assembly**
  - For single-stock: OHLCV + TA signals (reuse existing infra)
  - For two-leg options: IV rank, chain structure, DTE — can be mocked/stubbed initially
  - Done when: a snapshot can be assembled for SPY with a clear, typed schema

- [ ] **1.2 `RegimeSnapshot` contract**
  - Define interface: `label`, `confidence`, `posture` (`normal` / `reduced` / `blocked`)
  - Default to neutral posture with explicit warning when service unavailable
  - Done when: evaluation pipeline can consume a regime context without coupling to an implementation

- [ ] **1.3 Qualification stage**
  - Evaluate `entry_rules` from template against `MarketSnapshot`
  - Emit `QualificationResult`: PASS / FAIL + reason codes (e.g. `IV_RANK_BELOW_THRESHOLD`, `RSI_OUT_OF_RANGE`)
  - Done when: rules produce deterministic PASS/FAIL with named reason codes

- [ ] **1.4 Candidate construction stage**
  - Given qualification pass, construct proposed trade structure
  - Single-stock: direction + size
  - Two-leg options: short leg + long leg (width, expiry selection)
  - Output: `Candidate` with `proposed_legs_json` (1–2 legs)
  - Done when: a valid SPY put credit spread candidate can be constructed from live or mocked chain data

- [ ] **1.5 Risk evaluation stage**
  - Trade-level: max width, min credit (options) or position size (stock), chain quality, buying power
  - Portfolio-level stubs: exposure cap, heat limit, cash floor
  - Emit `RiskDecision`: approve / reject / resize + reason codes
  - Done when: risk stage can block a candidate and emit a reason code

- [ ] **1.6 `ExecutionIntent` emission**
  - Approval → emit `open` intent with legs, quantities, limits
  - Rejection → emit `no-action` with reason codes
  - Done when: every pipeline run terminates in either an intent or a no-action result

- [ ] **1.7 Decision ledger persistence**
  - Write `DecisionLedgerEntry` per stage per run
  - Done when: a full run leaves a queryable trace at each stage

---

## Phase 2 — Manual Trade Workbench (First Product Surface)
*Users can evaluate a strategy manually, review the rationale, approve execution, and track positions.*

- [ ] **2.1 Backend: Manual evaluation endpoint**
  - `POST /evaluate` — runs the pipeline for a given template + underlying
  - Returns: candidate or no-action result + reason codes
  - Done when: one API call produces an explainable evaluation result

- [ ] **2.2 Backend: Position lifecycle CRUD**
  - Open, update, close a position (single-stock or two-leg options)
  - Done when: position state is queryable and transitions are recorded

- [ ] **2.3 Backend: Decision Ledger query endpoint**
  - `GET /runs/{run_id}/ledger` — stage-by-stage trace
  - Done when: a full run trace is accessible via API

- [ ] **2.4 Frontend: Strategy Workbench screen**
  - Template picker → Underlying input → Generate candidate → Inspect rationale + risk → Approve / Reject
  - Done when: a user can walk from template selection to candidate review and approval in one screen

- [ ] **2.5 Frontend: Position Tracker**
  - List open positions; select to view lifecycle detail (fills, DTE, exit conditions, status)
  - Done when: a user can see what is open and why it was entered

- [ ] **2.6 Frontend: Decision Ledger view**
  - Per-run stage-by-stage records, reason codes
  - Done when: a user can inspect the full trace of any manual evaluation run

- [ ] **2.7 Sim execution adapter**
  - Fill simulated at mid or market on candidate legs
  - Done when: approving a candidate in sim mode produces fills and updates position state

---

## Phase 3 — Bot Studio (Scheduled Automation)
*Layered on top of the working manual evaluation pipeline.*

- [ ] **3.1 Add `BotInstance` model**
  - Fields: `template_id`, `underlying`, `mode` (sim/paper/live), `schedule`, `approval_mode`, `risk_budget`, `regime_policy`, `cooldown`
  - Done when: a bot can be created, activated, and deactivated via API

- [ ] **3.2 Backend: Bot CRUD + activation**
  - `POST /bots`, `GET /bots/{id}`, `PATCH /bots/{id}`, `DELETE /bots/{id}`
  - Done when: a bot can be created and queried via API

- [ ] **3.3 Backend: Bot scheduler**
  - Daily scheduled run per active bot via APScheduler or equivalent
  - Reuses the same evaluation pipeline as manual runs
  - Done when: bots evaluate on schedule without manual invocation

- [ ] **3.4 Frontend: Create Bot screen**
  - Template, underlying, entry rules, regime rules, schedule, approval mode, activate
  - Done when: a bot can be created and activated from the UI

- [ ] **3.5 Frontend: Bot Dashboard screen**
  - Status, current position, last/next run, recent actions, recent no-actions, blocker analysis, suggestions
  - Done when: a user can see what the bot did and why it did or did not act

- [ ] **3.6 Broker paper execution adapter**
  - Connect execution intent → broker paper account (IBKR or equivalent)
  - Done when: a bot run in paper mode places a paper order and receives a fill

- [ ] **3.7 Reconciliation**
  - On bot run: reconcile actual account/position state before evaluating new entries
  - Done when: position state mismatch is detected and surfaced with an explicit warning

---

## Deferred / Non-Goals (MVP)

- Multi-leg structures beyond two legs (iron condors, butterflies)
- Multi-underlying bots
- Broad cross-asset screener / candidate board as primary UX
- Autonomous live execution without approval
- Multiple venues simultaneously
- Research workbench / parameter sweep
- Strategy marketplace
- Full regime productization (consume a stub contract only in MVP)
- Heavy ML ranking
