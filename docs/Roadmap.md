1. Executive Summary

Chronos is a trading decision platform for structured, repeatable strategies. It is designed to turn strategy templates into venue-aware, risk-disciplined, replayable trade decisions with a complete record of what was taken, skipped, rejected, overridden, and why.

The product is not primarily a broker interface, a universe scanner, or an autonomous agent. Its foundation is a canonical decision engine that supports two connected operating modes:

Manual decision support for traders who want structured candidate generation, review, execution, and lifecycle tracking.

Persistent strategy bots for traders who want standing mandates that evaluate on schedule, manage lifecycle state, and produce action or no-action outcomes with explicit explanations.

The roadmap prioritizes trust, determinism, and state correctness ahead of breadth. The earliest product slice is deliberately narrow: one venue, one account, one options strategy template, one underlying per bot, strong lifecycle management, and full decision logging.

The long-term product direction remains intact: multi-bot supervision, stronger portfolio-level governance, venue-aware replay, research tooling, and eventually crowdsourced optimization and externalized regime intelligence. Those capabilities are retained in the architecture but deferred in the product sequence.

2. Product Thesis

2.1 Problem Statement

Most retail and prosumer trading products are strong in one of three areas and weak in the others:

screening and charting,

execution and broker connectivity,

post-trade journaling and analytics.

Few products provide a reliable, auditable path from structured strategy logic to live decision-making with integrated risk controls, position lifecycle tracking, and explicit explanations for both action and inaction.

Users do not primarily lack more indicators. They lack:

a consistent way to encode repeatable strategy behavior,

portfolio-aware risk controls that operate above the level of a single order,

regime-aware gating and operating posture,

a trustworthy path from manual execution to automation,

a structured decision ledger that supports diagnostics, replay, optimization, and later pooled learning.

2.2 Product Thesis

Chronos wins by being unusually strong at the following narrow promise:

Turn structured rules into venue-aware, risk-disciplined, replayable trade decisions with full visibility into what was taken, what was skipped, and why.

2.3 Strategic Positioning

Chronos is differentiated by:

a single canonical decision engine across manual, bot, paper, live, and replay contexts,

explicit reason-code infrastructure,

first-class lifecycle tracking for options structures,

portfolio-aware risk as an engine rather than a checklist,

venue abstraction based on profiles and adapters rather than bespoke strategy logic,

a trust-building progression from manual decision support to supervised automation.

3. Foundational Product Principles

3.1 Universe-first is not the correct foundation

Universe management is an input and eligibility concern. It is not the conceptual center of the product.

The core product is organized around:

strategy templates,

manual trade setups and bot instances,

market, regime, and portfolio state,

deterministic evaluation stages,

execution intents,

position lifecycle tracking,

decision ledgering.

Universe selection remains important, but it should constrain and feed the engine rather than define the engine or the primary user experience.

3.2 One canonical decision engine

The same core logic must power:

manual scans,

bot runs,

simulation,

broker paper execution,

live execution,

replay,

post-mortem analysis.

There should be no duplicated strategy logic across these contexts.

3.3 Data-oriented architecture

Chronos is designed around explicit data contracts and processing stages, not object-heavy business logic.

The architectural model is:

typed artifacts,

deterministic stages,

cached intermediates,

replayable inputs and outputs,

schedulable and later parallelizable workloads.

This is the principal architectural implication of the data-oriented design approach.

3.4 Risk is a first-class system

Risk is not a boolean check attached to order submission. It is a portfolio-aware evaluation system over candidate structures, current exposure, venue constraints, and operating posture.

3.5 Explanation is a primary product feature

Chronos must explain:

what action was taken or proposed,

what was considered but rejected,

what did not trigger,

which stage or policy blocked progression,

what changed between runs.

3.6 Narrow scope, durable contracts

The early product is intentionally narrow, but its contracts must be compatible with later expansion into:

additional strategy templates,

multiple one-underlying bots,

broader asset-class support,

venue-aware replay,

external regime products,

research and optimization layers.

3.7 Adapter-first external boundaries

Every external dependency that can change over time must sit behind a narrow adapter contract.

This applies at minimum to:

price data,

options chain data,

venue rules and profiles,

execution,

account and position state.

For MVP, Chronos should use Yahoo Finance-backed adapters for stock candles and options chain data because the product is not paying for market data yet.

The decision engine, strategy templates, risk logic, and lifecycle logic must not call Yahoo Finance directly.

This is non-negotiable because the product is expected to swap in tastytrade broker data and potentially paid market data later without rewriting strategy or risk code.

4. Product Surfaces

Chronos comprises three product surfaces. Only the first two are primary within the MVP.

4.1 Manual Trade Workbench

Purpose:

generate structured candidates,

support manual review and execution,

track position lifecycle,

support post-trade review.

Primary objects:

Candidate,

Trade Proposal,

Position Lifecycle.

4.2 Bot Studio

Purpose:

define standing strategy mandates,

activate one-underlying bots,

evaluate on schedule,

surface action and no-action outcomes,

support iterative refinement.

Primary objects:

Strategy Template,

Bot Instance,

Bot Run,

Execution Intent.

4.3 Desk Control Tower

Purpose:

supervise multiple bots,

review portfolio posture,

inspect shared constraints,

review action queues,

later support higher-order desk workflows.

Primary objects:

Portfolio Snapshot,

Governor Policy,

Action Queue,

Desk Analytics.

This surface is intentionally lightweight until after the foundational loops are proven.

5. Product Architecture Overview

5.1 Canonical decision flow

Strategy Template
    -> Manual Trade Setup or Bot Instance
    -> Snapshot Assembly (market, regime, portfolio)
    -> Evaluation Pipeline
    -> Execution Intent
    -> Execution Adapter
    -> Position Lifecycle Update
    -> Decision Ledger


5.2 Trigger sources

The trigger source is not the decision engine. All trigger sources must converge into the same canonical pipeline.

Supported trigger classes over time:

scheduled evaluation,

manual invocation,

webhook events,

internal system events.

Scheduled Run ──┐
Manual Action ──┼──> RunTrigger / SignalEvent -> Canonical Evaluation Pipeline
Webhook Event ──┘


5.3 High-level architecture

                   ┌──────────────────────────────┐
                   │       STRATEGY TEMPLATE      │
                   │ entry, exits, policy schema  │
                   └──────────────┬───────────────┘
                                  │
                   ┌──────────────▼───────────────┐
                   │ BOT INSTANCE / MANUAL SETUP  │
                   │ underlying, mode, schedule   │
                   └──────────────┬───────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
┌───────▼────────┐      ┌─────────▼─────────┐     ┌────────▼────────┐
│ Market Snapshot│      │ Regime Context     │     │ Portfolio State  │
│ bars, chain,   │      │ label, confidence  │     │ positions, cash, │
│ liquidity, EVT │      │ transition signal  │     │ pending orders   │
└───────┬────────┘      └─────────┬─────────┘     └────────┬────────┘
        └─────────────────────────┴─────────────────────────┘
                                  │
                       ┌──────────▼──────────┐
                       │ Evaluation Pipeline │
                       │ qualify, construct, │
                       │ risk, intent        │
                       └──────────┬──────────┘
                                  │
                       ┌──────────▼──────────┐
                       │  Execution Adapter  │
                       │ sim / paper / live  │
                       └──────────┬──────────┘
                                  │
                       ┌──────────▼──────────┐
                       │ Position Lifecycle  │
                       │ open/manage/close   │
                       └──────────┬──────────┘
                                  │
                       ┌──────────▼──────────┐
                       │  Decision Ledger    │
                       │ taken/skipped/why   │
                       └─────────────────────┘


6. Canonical Domain Model

6.1 StrategyTemplate

Defines the static playbook for a strategy family.

Responsibilities:

parameter schema,

entry qualification rules,

leg selection policy,

exit and adjustment policies,

supported instrument and venue constraints,

risk hooks,

explanation metadata.

Examples over time:

put credit spread,

covered call,

cash-secured put,

wheel,

equity breakout.

6.2 ManualTradeSetup

Represents a one-time operator-driven evaluation context derived from a strategy template.

Responsibilities:

choose underlying,

choose parameter set,

generate candidate structure,

request execution.

6.3 BotInstance

Represents a persistent deployed mandate.

Responsibilities:

template selection,

one underlying in early versions,

schedule,

approval mode,

risk budget,

regime policy,

entry and management policy,

cooldown and concurrency policy.

6.4 Candidate

Represents a concrete possible structure before approval.

Contains:

underlying,

strategy template reference,

market and regime snapshot references,

proposed legs,

quality and liquidity metrics,

qualification results,

reason codes,

score and diagnostic metadata.

6.5 ExecutionIntent

Represents a proposed action.

Supported intent types:

open,

close,

roll,

reduce,

hedge,

cancel/replace,

hold/no-action.

6.6 PositionLifecycle

Represents the full state of a live or historical position.

Responsibilities:

opening structure,

fills,

mark history,

Greeks snapshots,

adjustments,

close reason,

expiry and assignment handling,

linkage to bot runs and decisions.

6.7 DecisionLedgerEntry

Represents a stage-level record of what the system decided and why.

Contains:

bot or manual context reference,

run ID,

stage,

subject type and subject ID,

outcome,

reason codes,

snapshot references,

input hash,

timestamps.

The decision ledger is a foundational asset for debugging, auditability, diagnostics, replay, and future optimization.

7. Data-Oriented Processing Model

7.1 Rationale

Chronos should be implemented as a sequence of typed stages operating on explicit artifacts. This approach is more durable than object-heavy orchestration and better aligned with future batch processing, caching, replay, and partitioned computation.

7.2 Core artifacts

Representative artifact families:

MarketSnapshot,

PortfolioSnapshot,

RegimeSnapshot,

FeatureBatch,

QualificationBatch,

CandidateBatch,

RiskDecisionBatch,

OrderIntentBatch,

FillBatch,

PositionBatch,

LedgerBatch.

7.3 Core stage pipeline

[Snapshot Assembly]
    -> MarketSnapshot
    -> PortfolioSnapshot
    -> RegimeSnapshot

[Feature Computation]
    -> FeatureBatch

[Qualification]
    -> QualificationBatch + reason codes

[Trade Construction]
    -> CandidateBatch

[Risk Evaluation]
    -> RiskDecisionBatch

[Intent Generation]
    -> OrderIntentBatch

[Execution Routing]
    -> FillBatch / OrderStatus

[Lifecycle Update]
    -> PositionBatch
    -> LedgerBatch


7.4 Caching and reusable state

The engine should avoid unnecessary recomputation of expensive intermediates.

High-value cache candidates include:

normalized chain snapshots,

feature batches,

qualification results,

regime context outputs,

replay inputs,

venue profile lookups.

The intent is the same as object pooling in a data-oriented system: reuse expensive state rather than reconstructing it gratuitously.

7.5 Parallelizability

The stage model should remain schedulable and partitionable from the start, even when initial execution is single-threaded.

Natural parallel workloads include:

feature computation across dates or underlyings,

rule evaluation across historical partitions,

replay over multiple windows,

venue comparison over shared candidates,

risk evaluation over candidate batches.

8. MVP Definition

8.1 MVP boundary

The MVP spans v0 through v2.

8.2 MVP objective

The MVP must prove that Chronos can:

express a strategy cleanly,

evaluate it deterministically,

support manual execution,

support persistent bot execution on schedule,

manage lifecycle state correctly,

explain both action and non-action outcomes,

preserve structured telemetry for replay and optimization.

8.3 MVP non-goals

The MVP is not intended to prove:

broad cross-asset portfolio allocation,

large strategy template catalogs,

autonomous self-modifying agents,

heavy ML ranking,

multi-broker live breadth,

advanced social or marketplace features.

9. v0 — Minimum Viable Product (MVP)

9.1 Objective

Deliver the smallest coherent product that is immediately useful to Calico’s desk and establishes the correct architecture for later retail expansion.

9.2 v0 value proposition

Deploy or manually trade a narrow options strategy on a single underlying, understand exactly why it did or did not act, and refine it over time using evidence rather than guesswork.

9.3 Scope

In scope

one venue profile,

one account,

one strategy template,

one underlying per bot,

options-first lifecycle support,

manual execution support,

daily scheduled bot evaluation,

simulation and broker paper modes,

decision ledger,

no-action diagnostics,

adapter-first market and execution boundaries,

Yahoo Finance adapters for stock candles and options chain data in MVP,

basic AI-assisted configuration diagnosis and explanation.

Out of scope

multi-underlying bots,

broad cross-asset candidate board,

portfolio allocator,

fully autonomous live execution,

multiple venues,

research workbench,

strategy marketplace,

full regime productization.

9.4 Recommended initial strategy and underlying

Initial template:

Put Credit Spread / Bull Put Spread

Initial underlying:

SPY

Rationale:

aligned with current trading behavior,

forces correct multi-leg lifecycle design,

narrow enough for reliable implementation,

liquid enough to simplify initial constraints.

9.5 v0 user experience

Manual Trade Workbench

User flow:

select strategy template,

select underlying,

generate current candidate structure,

inspect rationale, pricing, and risk,

approve execution,

track lifecycle.

Bot Studio

User flow:

select strategy template,

select underlying,

configure entry, exit, risk, and regime rules,

preview expected trigger frequency,

activate bot,

review action or no-action outcomes,

refine configuration.

Bridge flow

Support Create Bot from Current Candidate.

This is a product bridge between manual discovery and persistent automation. It is not the primary bot creation model, but it is an important operator workflow.

9.6 v0 run model

Each scheduled bot run should execute in the following order:

load bot config,

reconcile account and position state,

load market and chain snapshots,

load current regime context,

evaluate management of existing positions,

if policy allows, evaluate new entry qualification,

construct candidate,

run risk evaluation,

emit intent or no-action result,

persist decision ledger entries,

surface result to operator.

The system must prioritize state reconciliation and lifecycle management before new entry generation.

9.7 v0 risk model

Trade-level checks

maximum width,

minimum credit,

chain quality and liquidity,

stale data guard,

buying power validation,

expiry and event restrictions.

Portfolio-level checks

one-underlying exposure cap,

maximum heat,

available cash floor,

drawdown circuit breaker,

halt-new-trades mode,

reduced-size mode.

Risk actions

The risk engine should support:

approve,

resize,

reject,

force-review.

9.8 v0 regime role

Chronos should consume a Regime Context Service rather than directly embedding a large regime product into the hot path.

In v0, regime is used to:

gate new entries,

modify operating posture,

support explanation and diagnostics.

It should not directly choose trades or own strike selection.

If the regime service is unavailable, the system should fall back to:

neutral posture,

reduced size,

explicit warning to the operator and ledger.

9.9 v0 why-not infrastructure

This is a mandatory feature, not an enhancement.

Every run must produce either:

an action or proposed action,

or a no-action result with explicit reason codes.

Representative reason codes:

REGIME_BLOCKED_NEW_ENTRY

EXISTING_POSITION_ALREADY_OPEN

CANDIDATE_CREDIT_TOO_LOW

IV_RANK_BELOW_THRESHOLD

COOLDOWN_ACTIVE

RISK_HEAT_LIMIT_REACHED

CHAIN_DATA_STALE

NO_VALID_STRIKES_FOUND

Required bot dashboard outputs:

last run result,

last 10 run outcomes,

top blocker reasons over a recent window,

what changed since the previous run,

suggested configuration adjustments.

9.10 v0 AI role

AI should operate only as a deterministic-data-backed advisor.

Permitted uses:

configuration diagnosis,

natural-language explanation,

over-restrictiveness detection,

run summary generation.

Not permitted in v0 hot path:

autonomous config mutation,

hidden ranking logic,

risk authority,

system-of-record decisions.

9.11 v0 key screens

Strategy Workbench

template picker,

underlying selector,

candidate card,

risk explanation,

execute action.

Create Bot

template,

underlying,

entry rules,

management rules,

regime rules,

schedule,

trigger preview,

activate.

Bot Dashboard

status,

mode,

current position,

last and next run,

recent actions,

recent non-actions,

blocker analysis,

suggestions.

Position Detail

lifecycle timeline,

fills,

Greeks,

DTE,

exit conditions,

event/risk flags.

Decision Ledger View

stage-by-stage records,

reason codes,

snapshot references,

replay entry point.

9.12 v0 success criteria

v0 is successful when the system can:

generate valid SPY put credit spread candidates from current data,

support manual execution end-to-end,

run one-underlying bots daily without state corruption,

track full multi-leg lifecycle correctly,

explain every no-action event,

replay a prior run deterministically,

operate safely in simulation and paper modes.

9.13 v0 earliest deliverable slice

The narrowest useful implementation is:

SPY only,

put credit spread only,

manual workbench,

bot creation from template,

daily bot run,

one open position max,

human approval required,

decision ledger,

no-action diagnostics,

simulation and/or broker paper execution.

10. v1 — Trust, Operations, and Execution Maturity

10.1 Objective

Strengthen the single-underlying bot product so it can support real supervised use with higher operator trust.

10.2 Primary additions

broker paper integration hardened,

selected small live execution path,

second underlying or second template,

stronger reconciliation,

forced-review flows,

improved lifecycle handling,

notifications and operator alerts,

polished create-bot-from-candidate workflow,

baseline journal capture.

10.3 Execution maturity

Execution modes should be formalized as:

simulation,

broker paper,

canary,

full live.

Canary belongs here rather than in v0 core identity. It becomes meaningful once lifecycle management, reconciliation, and monitoring are already dependable.

10.4 Backtesting and replay in v1

v1 should add:

deterministic replay over recent historical windows,

forensic debugging using stored artifacts,

paper-forward validation metrics.

The emphasis remains on replay and validation rather than a full historical research workbench.

11. v2 — Multi-Bot Supervision and MVP Completion

11.1 Objective

Graduate from isolated one-bot workflows to a small governed desk while preserving the same engine and lifecycle model.

11.2 Primary additions

multiple one-underlying bots,

simple portfolio governor,

shared risk budgets,

action queue,

desk-level dashboard,

trigger-frequency analytics across bots,

stronger operator controls and comparisons,

paper/live comparison views.

11.3 Portfolio governor model

The portfolio governor is a supervisory policy layer, not a strategy bot.

Responsibilities:

set shared risk posture,

impose pause or resize policies,

enforce desk-level budgets,

force review under stressed conditions,

coordinate bot constraints.

Relationship to regime:

regime context informs the governor,

the governor sets policy envelopes,

bots generate actions within those policy constraints.

11.4 MVP completion criteria

The MVP is complete when Chronos supports:

manual execution,

persistent one-underlying bots,

options lifecycle management,

replayable decision paths,

reason-code analytics,

supervised multi-bot operation under a shared governance layer.

12. v3+ Strategic Direction

12.1 v3 — Venue-aware replay and broader structures

equities and simpler single-leg structures on the same engine,

additional venue models in replay and paper contexts,

stronger venue comparison,

broader lifecycle support,

more advanced governor logic,

deeper reason-code analytics.

12.2 v4 — Research and optimization layer

historical replay workbench,

parameter sweep tooling,

counterfactual analysis,

walk-forward evaluation,

journal-aware diagnostics,

regime-conditional defaults,

early pooled learning primitives.

12.3 v5 — Retail desk platform

multi-tenant productization,

strategy family analytics,

controlled presets or template marketplace,

stronger desk governance,

opt-in crowdsourced optimization,

externalized regime intelligence and proprietary data products.

13. Technical Design Requirements

13.1 Deterministic hot path

The canonical decision path must remain deterministic and inspectable. AI may advise, summarize, and diagnose, but it must not become the system of record for live decisioning.

13.2 Replayability by construction

Every stage must be replayable from stored inputs and references.

Replay should support:

re-running a specific historical decision,

stage-by-stage inspection,

comparison of alternative policy outcomes,

debugging of discrepancies between expectation and behavior.

13.3 Venue abstraction

Venue behavior must be modeled beneath the core engine through:

canonical execution intents,

venue profiles,

capability metadata,

fee, margin, fill, and assignment modules,

execution adapters.

The engine should remain venue-agnostic at the strategy layer.

13.4 Strategy templates with strict contracts

Strategy logic should be expressed through a small number of parameterized templates rather than bespoke one-off implementations.

Each template should define:

required inputs,

qualification rules,

structure construction rules,

lifecycle behaviors,

risk hooks,

explanation metadata.

13.5 Signal ingestion and webhooks

Signal webhooks, including TradingView or future external signals, belong in signal ingestion rather than in a separate architecture.

The correct model is:

signal source emits event,

event is normalized into a canonical SignalEvent or RunTrigger,

event enters the same evaluation pipeline as scheduled or manual runs.

13.6 Regime externalization

Chronos should depend on a Regime Context Service contract rather than on a hard-coded internal regime implementation.

This supports later extraction of Regime Radar into a separate product while preserving Chronos stability.

15. Explicit Non-Goals for Early Versions

Chronos will not attempt the following in early phases:

broad cross-asset ranked candidate board as the primary user experience,

autonomous self-modifying strategy agents,

large template catalogs,

heavy ML ranking before sufficient telemetry exists,

complex multi-broker live routing from day one,

overly elaborate regime systems in the hot path,

feature-heavy retail surfaces before the engine is trustworthy.
