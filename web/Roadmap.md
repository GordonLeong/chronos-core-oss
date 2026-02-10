# The following document sets the northstar and strategic direction for the project, low level details are subject to change

Full PRD v2

Dorado Trading Platform — Product Requirements Document

Version: 0.2 Author: Calico Technologies Date: February 2026

1. Problem Statement

Systematic retail traders face a fragmented toolchain: signal generation lives in TradingView, execution is manual through broker UIs, risk management is a spreadsheet, and macro regime awareness is gut feel. This fragmentation causes three failure modes:

Execution drift — signals fire but manual execution introduces delay, emotional override, or outright skipped trades

Risk blindness — no unified view of portfolio heat, correlation clustering, or drawdown trajectory across venues and asset classes

Regime ignorance — strategies designed for one volatility regime run unmodified through regime transitions, destroying edge

Dorado solves this by providing a unified orchestration layer: universe definition → candidate generation → risk gating → human selection → execution → position management → outcome measurement, with quantitative regime awareness and adaptive ML modulating the entire pipeline across options, FX, and crypto.

User Persona

Primary (Dogfood): Solo systematic trader (you). Finance background, Python-literate, running defined-risk options strategies on IBKR with $5–50k deployed capital. Expanding into FX position trading and crypto momentum on 3–7 day horizons. Not HFT — latency tolerance is seconds to minutes. Needs automation of execution and lifecycle management, intelligence on regime and risk aggregation, and a measured feedback loop that improves decision quality over time.

Secondary (Future SaaS): Sophisticated retail/semi-pro traders who want institutional-grade risk infrastructure without building it themselves. Willing to pay $50–200/mo for regime signals + execution automation + forward-testing infrastructure.

1. Core Architectural Concepts

2.1 Universe-First Design

The universe is the foundational constraint. All data pipelines, strategy templates, bot creation, risk calculations, and ML models operate within the defined universe. Nothing exists outside it.

universe:
  id: "calico-core"
  underlyings:
    # Options + Equities (IBKR)
    - symbol: "SPY"
      asset_class: "equity_options"
      venue: "ibkr"
    - symbol: "TLT"
      asset_class: "equity_options"
      venue: "ibkr"
    - symbol: "GLD"
      asset_class: "equity_options"
      venue: "ibkr"
    # FX (IBKR or OANDA, Phase 2)
    - symbol: "USDJPY"
      asset_class: "fx"
      venue: "ibkr"
    - symbol: "AUDUSD"
      asset_class: "fx"
      venue: "ibkr"
    # Crypto (Hyperliquid/Deribit, Phase 2)
    - symbol: "BTC"
      asset_class: "crypto"
      quote_currency: "USDC"
      venue: "hyperliquid"
    - symbol: "ETH"
      asset_class: "crypto"
      quote_currency: "USDC"
      venue: "hyperliquid"
  data_config:
    ohlcv: true
    option_chains: true          # only for equity_options
    fetch_frequency: "eod"       # end-of-day for all; intraday polling for open position monitoring

Why universe-first:

Data economics — only fetch, store, and maintain chains/OHLCV for instruments you actually trade. A 7-instrument universe means 7 data pipelines, not 500.

Risk boundary enforcement — the universe is the portfolio. Concentration limits, correlation clustering, and heat calculations are scoped to a known, small set. Cross-asset correlation matrices are precomputed daily.

Cognitive discipline — you don't trade everything. The platform enforces this mechanically.

On universe save:

Validate all symbols exist on target venues

Initialize data fetch jobs (OHLCV, chains if options-enabled, funding rates if crypto)

Compute baseline cross-asset correlation matrix

Universe becomes the constraint for all bot creation

2.2 Bot Abstraction

Each bot binds to a single underlying, not a single instrument. This is critical because multi-leg strategies (wheel, iron condor) use multiple instrument types across their lifecycle — puts, stock, calls — on the same underlying.

Universe: [SPY, TLT, GLD, USDJPY, BTC]     ← defined once
Bot:      bound to SPY                       ← one underlying
Strategy: iron_condor                        ← defines which instruments are used and when

The strategy template knows which instrument types it needs. The bot knows which underlying. The universe gates what underlyings are available.

bot:
  id: "spy-ic-01"
  universe: "calico-core"
  underlying: "SPY"
  venue: "ibkr"
  venue_mode: "paper"              # "simulation", "paper", "live"
  strategy_template: "iron_condor"
  signal_mode: "scan"              # "scan", "webhook", "both"
  signal_source:
    type: "scheduled"
    schedule: "daily_market_open"
  approval_mode: "human_required"  # "human_required", "auto_execute"
  sizing:
    method: "fixed_risk_pct"
    risk_pct: 2.0
  regime_filter:
    allowed: ["risk_on", "goldilocks"]
    min_regime_confidence: 0.60
  timeout_hours: 4

1. Component Architecture

┌──────────────────────────────────────────────────────────────────────────┐
│                           DORADO PLATFORM                                │
│                                                                          │
│  ┌────────────┐  ┌────────────┐  ┌─────────────┐  ┌──────────────────┐  │
│  │   CORE     │  │   RISK     │  │   REGIME    │  │   ML LAYER       │  │
│  │   ENGINE   │  │   RADAR    │  │   RADAR     │  │                  │  │
│  │            │  │            │  │             │  │ Asset-class      │  │
│  │ Universe   │←→│ Trade-level│  │ Macro HMM   │  │ regime models    │  │
│  │ Bot Mgmt   │  │ Portfolio  │  │ FX Regime   │  │ Adaptive sizing  │  │
│  │ Candidate  │  │ Circuit Brk│  │ Crypto Trend│  │ Allocation       │  │
│  │ Generation │  │ Adaptive   │  │ Correlation │  │ bandit           │  │
│  │ Template   │  │ Sizing     │  │ Regime (PCA)│  │ Exit model       │  │
│  │ Resolver   │  │ Policy Cfg │  │             │  │ Parameter bandit │  │
│  │ State Mach │  │            │  │             │  │                  │  │
│  │ Order Exec │  │            │  │             │  │                  │  │
│  └─────┬──────┘  └─────┬──────┘  └──────┬──────┘  └────────┬─────────┘  │
│        │               │                │                   │            │
│        └───────┬───────┘────────────────┘───────────────────┘            │
│                │                                                         │
│      ┌─────────▼───────────────────────────────────────────────────┐     │
│      │                     DATA LAYER                               │     │
│      │  PostgreSQL + TimescaleDB (trades, positions, features, ML)  │     │
│      │  Redis (state, regime cache, locks, quotes)                  │     │
│      └─────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────────────┘

3.1 Core Engine

The Core Engine orchestrates two flows: scan-based candidate generation (daily, systematic) and webhook-based reactive execution (event-driven). Both converge into the same risk and approval pipeline.

Signal Modes

Mode

Use Case

Flow

Scan

Daily systematic pipeline. All bots in scan mode generate candidates simultaneously. Portfolio-level selection.

Scan → candidates per underlying → ranking → portfolio-aware selection → approval

Webhook

Reactive signals from TradingView or external systems. Single-bot execution.

Webhook → single bot → risk check → approval → execution

Both

Bot participates in daily scans AND responds to external webhooks

Combines both flows

Template Resolver

The Template Resolver is the central abstraction. It takes a strategy template + three data sources (venue adapter, data pipeline, regime radar) and produces fully resolved trade candidates or a rejection with reason.

┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Venue Adapter   │     │  Data Pipeline    │     │  Regime Radar   │
│  (Broker API)    │     │  (TimescaleDB)    │     │  (Redis cache)  │
│                  │     │                   │     │                 │
│  • Option chain  │     │  • IV history     │     │  • Current      │
│  • Greeks        │     │  • OHLCV          │     │    regime       │
│  • Quotes        │     │  • Computed TA    │     │  • Confidence   │
│  • Account state │     │  • Macro features │     │  • Transition   │
│  • Positions     │     │  • Hurst exponent │     │    alert        │
└────────┬────────┘     └────────┬──────────┘     └────────┬────────┘
         │                       │                          │
         └───────────┬───────────┘──────────────────────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │   Template Resolver   │
          │                      │
          │  Maps template params │
          │  to concrete values   │
          │  from all 3 sources   │
          └──────────┬───────────┘
                     │
                     ▼
              Gate cascade →
              Candidate generation →
              Scoring / Ranking →
              Portfolio-aware selection →
              Approval payload

Mapping complexity is tiered:

Tier 1 — Direct mapping: strike prices, bid/ask, position quantity, fill price (broker returns it)

Tier 2 — Derived from broker data: delta at strike, DTE, spread width, credit, max loss, breakeven (simple computation)

Tier 3 — Computed from pipeline data: IV rank/percentile, ATR, ADX, SMA, S/R levels, Hurst exponent, funding rates (your data pipeline, not broker)

Venue Adapter Interface

class VenueAdapter(ABC):
    """Uniform interface across all brokers/venues."""

    @abstractmethod
    async def get_account_state(self) -> AccountState: ...

    @abstractmethod
    async def place_order(self, order: Order) -> OrderResult: ...

    @abstractmethod
    async def get_positions(self) -> list[Position]: ...

    @abstractmethod
    async def cancel_order(self, order_id: str) -> CancelResult: ...

    @abstractmethod
    async def get_quotes(self, symbols: list[str]) -> list[Quote]: ...

class OptionsVenueAdapter(VenueAdapter):
    """Extended interface for options-capable venues."""

    @abstractmethod
    async def get_chain(self, underlying: str, expiry: date) -> OptionChain: ...

class FXVenueAdapter(VenueAdapter):
    """Extended interface for FX venues."""

    @abstractmethod
    async def get_swap_rates(self, pair: str) -> SwapRates: ...

class CryptoVenueAdapter(VenueAdapter):
    """Extended interface for crypto venues."""

    @abstractmethod
    async def get_funding_rate(self, symbol: str) -> FundingRate: ...

Normalized chain data schema for options:

@dataclass
class OptionContract:
    symbol: str
    underlying: str
    strike: float
    expiration: date
    right: Literal["put", "call"]
    bid: float
    ask: float
    mid: float
    delta: float | None
    gamma: float | None
    theta: float | None
    vega: float | None
    implied_vol: float | None
    open_interest: int
    volume: int

@dataclass
class OptionChain:
    underlying: str
    underlying_price: float
    expirations: list[date]
    contracts: list[OptionContract]
    timestamp: datetime               # chain freshness

    def filter_by_dte(self, min_dte: int, max_dte: int) -> "OptionChain": ...
    def filter_by_delta(self, min_d: float, max_d: float, right: str) -> list[OptionContract]: ...
    def nearest_delta(self, target: float, right: str, expiration: date) -> OptionContract: ...

Phase 1: IBKRAdapter (wraps TWS API via ib_insync), PaperAdapter (simulates fills against live market data) Phase 2: FX via IBKR or OANDA, crypto via Hyperliquid/Deribit Deferred: Alpaca (SaaS equities), Kalshi (event contracts), DeFi yield adapters

Chain Data Quality Handling

IBKR chain data has five known quality issues that require defensive handling:

Stale Greeks — Greeks are snapshots, not streaming. After strike selection, re-request fresh quotes for selected contracts. If delta diverges > 0.02 from chain data, re-resolve.

Wide bid/ask on illiquid strikes — Compute spread quality ((ask - bid) / mid). Flag spreads > 15% in approval payload. Let human decide.

Partial chain returns — Validate chain completeness before resolver runs. If > 10% of contracts missing Greeks, retry with backoff (60s, 120s, 300s). After 3 failures, alert human.

IBKR's IV model dependency — Store raw option prices alongside model-derived Greeks. Phase 2: recompute IV from prices independently.

Rate limits (50 msg/sec) — Cache chains with 2-minute TTL for gate evaluation. Only fetch fresh for final strike selection. Stagger requests across underlyings.

def validate_chain(chain: OptionChain, requirements: dict) -> ChainValidation:
    target_expiry = select_expiration(chain, requirements["dte_range"])
    relevant = chain.filter_by_expiration(target_expiry)

    missing_greeks = [c for c in relevant if c.delta is None]
    missing_quotes = [c for c in relevant if c.bid == 0 and c.ask == 0]

    if len(missing_greeks) / len(relevant) > 0.10:
        return ChainValidation(valid=False, reason="Too many missing Greeks, retry")

    clean = [c for c in relevant if c.delta is not None and c.bid > 0]
    return ChainValidation(valid=True, clean_chain=clean)

Bot State Machine (Illustrative)

stateDiagram-v2
    [*] --> IDLE
    IDLE --> SIGNAL_RECEIVED : signal ingested
    SIGNAL_RECEIVED --> RISK_CHECK : validate signal
    RISK_CHECK --> REJECTED : risk check fails
    RISK_CHECK --> AWAITING_APPROVAL : risk check passes
    REJECTED --> IDLE : log & notify
    AWAITING_APPROVAL --> EXECUTING : human approves
    AWAITING_APPROVAL --> CANCELLED : human rejects / timeout
    CANCELLED --> IDLE : log & notify
    EXECUTING --> MONITORING : order filled
    EXECUTING --> FAILED : order rejected / partial fill
    FAILED --> IDLE : log, alert, cleanup
    MONITORING --> SIGNAL_RECEIVED : adjustment signal
    MONITORING --> CLOSING : exit signal / expiration / management trigger
    CLOSING --> IDLE : position closed

AWAITING_APPROVAL has a configurable timeout (default: 4 hours). Stale signals auto-cancel.

MONITORING is the steady state. Polls every 15 min (live) or 60 min (paper). Tracks per-side P&L for multi-leg structures.

Re-entry from MONITORING to SIGNAL_RECEIVED handles rolls and adjustments without spawning new bots.

State transitions persisted to PostgreSQL. Redis holds ephemeral state.

Monitoring Frequency

Check

Frequency

Rationale

P&L tracking (live)

Every 15 min market hours

Profit target / stop loss need timely execution

P&L tracking (paper)

Every 60 min

Paper P&L precision not critical; preserves rate limits

Short strike breach detection

Every 15 min

Intraday moves can test strikes in hours

DTE exit trigger

Daily

Calendar math

IV rank spike (vol exit)

2–3x/day (open, midday, close)

IV rank moves intraday but not tick-by-tick

Regime change

Daily

Macro regimes don't shift intraday

Circuit breakers

Every 15 min

Must halt before losses compound

FX/Crypto position check

Every 60 min (EOD data horizon)

3–7 day holds, sub-hourly monitoring unnecessary

3.2 Candidate Generation and Selection Pipeline

This is the core innovation. The flow inverts from "engine picks one answer, human approves" to "engine produces a ranked candidate list, human selects, engine enforces portfolio constraints."

Daily Scan Flow

Universe: [SPY, TLT, GLD, USDJPY, BTC, ETH]
     │
     ▼ (for each underlying, parallel)

┌─ SPY ─────────────────────────────┐
│  Template: Iron Condor             │
│  Gate 1 (Regime): ✓ Goldilocks    │
│  Gate 2 (Vol): ✓ IV rank 42      │
│  Gate 3 (TA): ✓ ADX 19, in range │
│  Chain fetch + validate            │
│  → 4 candidates generated          │
└────────────────────────────────────┘

┌─ TLT ─────────────────────────────┐
│  Template: Short Put               │
│  Gate 1: ✓                         │
│  Gate 2: ✗ IV rank 18 (< 30 min)  │
│  → SKIP                            │
└────────────────────────────────────┘

┌─ USDJPY ──────────────────────────┐
│  Template: FX Momentum             │
│  FX Regime Model: "carry" (68%)    │
│  Hurst: 0.58 (trending)           │
│  → 2 candidates (long carry)       │
└────────────────────────────────────┘

┌─ BTC ─────────────────────────────┐
│  Template: Crypto Momentum         │
│  Trend exists: ✓ (LogReg 0.72)    │
│  Hurst: 0.62 (strong trend)       │
│  → 2 candidates (long BTC)         │
└────────────────────────────────────┘

Gate Cascade (per underlying)

Gates are binary pass/fail evaluated in order. If any gate fails, the underlying is skipped for this scan. No candidates are generated.

Gate 1: REGIME (checked first, cheapest, broadest filter)
  → Query Regime Radar from Redis cache
  → Check allowed regimes + minimum confidence
  → For FX: query FX Regime Model
  → For Crypto: query Crypto Trend Model (trend exists?)

Gate 2: VOLATILITY (checked second, options and FX)
  → IV rank > minimum threshold
  → Term structure check (options)
  → VIX within bounds (options)
  → For FX: vol regime appropriate for strategy type
  → For Crypto: realized vol within tradeable range

Gate 3: TECHNICAL (checked third, requires computation)
  → ADX range-bound check (options income)
  → ATR channel confirmation (options income)
  → Hurst exponent check (FX/crypto momentum)
  → S/R level identification (passed to strike/entry selection)

TA computation module:

class TAEngine:
    """Computes technical indicators for gating and entry selection."""

    def compute(self, underlying: str, requirements: dict) -> TAResult:
        ohlcv = self.data_store.get_ohlcv(underlying, lookback=252)
        return TAResult(
            adx=self._adx(ohlcv, requirements.get("adx_lookback", 14)),
            atr=self._atr(ohlcv, requirements.get("atr_lookback", 20)),
            sma=self._sma(ohlcv, requirements.get("reference_ma", 20)),
            support_resistance=self._pivots(ohlcv),
            hurst=self._hurst_exponent(ohlcv, max_lag=30),
            rsi=self._rsi(ohlcv, 14),
            in_range=self._check_range(ohlcv, requirements),
        )

Candidate Scoring and Ranking

After gates pass and candidates are generated, they're scored by a weighted scoring function (Phase 1, manually tuned) or ML-driven ranking (Phase 2+).

Phase 1: Weighted scoring function

scoring:
  weights:
    data_quality: 0.30          # penalize stale/missing Greeks
    credit_to_width: 0.25       # higher credit relative to spread width
    sr_alignment: 0.20          # short strikes at S/R levels
    dte_preference: 0.15        # prefer middle of DTE range
    spread_tightness: 0.10      # tighter bid/ask = better fill quality
  exclude:
    spread_quality_above: 0.20  # >20% spread-to-mid = excluded
    missing_greeks: true

Weights are reviewed quarterly using paper trading outcome data.

Phase 2+: Contextual bandit scoring (see Section 7: ML Layer)

Portfolio-Aware Selection Loop

Candidates across all underlyings are merged into a single ranked list. The engine iterates in rank order, simulating each addition to the portfolio and checking all portfolio-level limits:

async def select_candidates(
    candidates: list[RankedCandidate],
    portfolio: PortfolioState,
    risk_policy: RiskPolicy,
) -> tuple[list[RankedCandidate], list[RankedCandidate]]:
    """
    Returns (selected_for_live, remaining_for_paper).
    All non-selected candidates run in paper automatically.
    """
    selected = []
    paper = []

    for candidate in candidates:  # already sorted by score desc
        simulated = portfolio.simulate_add(candidate)
        check = risk_engine.check_portfolio(simulated, risk_policy)

        if check.passed:
            selected.append(candidate)
            portfolio = simulated  # update running state for next iteration
        else:
            candidate.rejection_reason = check.reason
            paper.append(candidate)  # runs in paper for data collection

    return selected, paper

Key property: the loop is order-dependent. Higher-ranked candidates get allocated first. The ranking function implicitly determines capital allocation priority.

LLM Risk Commentary

After ranking and before presentation to human, an LLM call synthesizes non-obvious context:

(Illustrative)
RISK_COMMENTARY_SYSTEM_PROMPT = """
You are a risk analyst for a systematic multi-asset trading desk.
You receive candidate trades, portfolio state, regime data, and
historical performance.

Your job:

1. Flag non-obvious risks (concentration, regime trends, earnings proximity,
   correlated exposures, cross-asset dynamics)
2. Contextualize with historical performance in similar conditions
3. Assign confidence tag per candidate: HIGH / MEDIUM / LOW
4. Flag regime transition probability trends explicitly

NOT your job: make recommendations, override rankings, provide disclaimers.
Be concise. 3-5 sentences per candidate group. One paragraph portfolio-level.
"""

The LLM assigns confidence tags and produces narrative context. If the API call fails, the flow continues without commentary — the LLM is advisory, not load-bearing.

Human Selection (Dogfood Mode)

📋 Trade Candidates — 2026-02-10

SPY Iron Condor (4 candidates)
TLT Short Put — skipped (IV rank too low)
USDJPY Long — carry regime (2 candidates)
BTC Long — momentum (2 candidates)

SPY Candidates:
                                          Data   Risk

# Expiry   Strikes              Credit   Qual   Conf

1  Apr 25   569/564P 596/601C    $2.01    ✓✓✓   HIGH
2  Apr 18   570/565P 595/600C    $1.85    ✓✓✓   MED
3  Apr 25   567/562P 598/603C    $1.78    ✓✓✓   MED
4  Apr 18   568/563P 597/602C    $1.62    ⚠     LOW

USDJPY Candidates:
5  Long 148.50 / SL 146.80 / TP 151.20   —     HIGH
6  Long 148.50 / SL 147.50 / TP 150.00   —     MED

BTC Candidates:
7  Long $97,200 / SL $93,500 / TP $105,000  —   HIGH
8  Long $97,200 / SL $95,000 / TP $101,500  —   MED

💬 Risk Commentary:
Candidate #1 is the cleanest IC — short strikes at pivot S/R with
49 DTE. Watch regime trend: Goldilocks at 72% but Transition
probability tripled from 8% to 23% this week. Portfolio is 76%
short vol. USDJPY carry trade (#5) provides diversification — low
correlation to SPY at current regime. BTC momentum trade (#7) adds
crypto exposure but current SPY-BTC 30d correlation is 0.45 —
moderate, not independent.

Portfolio budget: 3 trades before heat limit
Cross-asset correlation regime: diversified (4 PCs for 80%)

[1] [2] [3] [5] [7] [Skip all]

Non-selected candidates automatically run in paper for data collection.

One-Tap Annotation

After selection, capture stated reasoning:

You selected #1, #5, #7. Quick tag for each:

# 1 SPY IC:   [Best credit] [S/R alignment] [Bandit rec] [Gut feel]
# 5 USDJPY:   [Carry setup] [Diversification] [Bandit rec] [Gut feel]
# 7 BTC:      [Strong trend] [Hurst signal] [Bandit rec] [Gut feel]

One tap per selection. Builds labeled dataset of stated reasoning vs. revealed preference for model calibration.

3.3 Paper Trading and Canary Release

Paper trading is not a feature — it's a venue adapter. Three modes, configured per-bot:

Mode

Implementation

Use Case

Simulation (PaperAdapter)

Pure in-process, simulates fills against live market data. No broker connection.

Development, initial testing

Broker Paper (IBKR paper account)

Same IBKRAdapter, different port (4002 vs 4001). Realistic fills.

Pipeline validation, end-to-end testing

Live

Real account, real capital

Production

bot:
  venue_mode: "paper"    # "simulation", "paper", "live"

Automatic Paper Trading of Non-Selected Candidates

Every candidate generated by the daily scan that is NOT selected for live execution automatically runs in paper. This transforms the partial feedback problem into full feedback:

Daily scan: 8 candidates across all underlyings
  → 3 selected live (portfolio limit)  → real P&L
  → 5 run in paper automatically       → simulated P&L
  → All 8 produce reward signals       → model updates 3x faster

Paper positions use the same state machine, same monitoring loop, same management rules. The only difference is the venue adapter and the polling frequency (60 min vs 15 min).

Resource constraint: cap concurrent paper positions at 30. If exceeded, stop papering lowest-scored candidates first — least informative.

Canary Release (Promotion Ladder)

Four-stage deployment pipeline for any new strategy template:

Stage 1: Simulation (PaperAdapter, no broker)
  Duration: Until 5+ full lifecycle completions without error
  Gate:     Zero state machine errors

Stage 2: Broker Paper (IBKR paper account)
  Duration: 2–4 weeks
  Gate:     All trades reconcile, no orphaned orders, no missed signals

Stage 3: Canary (paper + live simultaneously, live at 50% target size)
  Duration: 4–8 weeks
  Gate:     Paper-live divergence < 20%, no circuit breaker triggers

Stage 4: Full Live (target sizing)
  Duration: Ongoing
  Gate:     Continuous monitoring, paper control bot remains active

Stage 4 does not kill the paper bot. It remains as a permanent control group. If live performance degrades relative to paper beyond measured slippage, something changed.

Paper-to-Live Discount Factor

The canary phase empirically measures the paper-to-live discount per strategy per underlying:

Canary Report: spy-ic-01 (2026-02-01 to 2026-03-15)
                    Paper       Live        Delta
Trades executed:    8           8           0
Avg P&L/trade:     $142        $121        -$21 (-15%)
Avg slippage:       —           $0.03/contract
Fill rate:          100%        100%

Measured discount: 15% for SPY iron condors

This discount feeds back into the ML layer's paper_discount parameter, calibrating paper reward signals for model training. Don't guess 10% — measure it.

3.4 Risk Radar

Risk Radar operates at two levels and enforces user-defined policy, not hardcoded rules.

Trade-Level Risk

Check

Description

Asset Classes

Position sizing

Fixed risk %, vol-adjusted, or adaptive (ML-driven)

All

Max loss per trade

Absolute dollar cap per individual position

All

Strategy constraints

Max DTE, min delta, spread width, stop distance

Per-template

Buying power / margin check

Ensure sufficient capital before approval

All

Regime filter

Block trades in disallowed regimes

All

Data quality gate

Reject if chain data incomplete / stale

Options

Spread quality check

Flag wide bid-ask in approval payload

Options

Portfolio-Level Risk

Check

Description

Portfolio heat

Max % of portfolio at risk simultaneously across all asset classes

Concentration guard

Max exposure to single underlying or asset class

Correlation clustering

Flag correlated positions using PCA correlation regime

Cross-asset exposure

Net long/short vol, net directional, carry exposure

Cash drag

Alert when deployed capital drops below threshold

Greeks aggregation

Portfolio delta, gamma, theta, vega (options only)

Circuit Breakers

circuit_breakers:
  daily_loss_limit:
    threshold_pct: 2.0
    action: "halt_new_trades"
  weekly_loss_limit:
    threshold_pct: 5.0
    action: "halt_all_bots"
  vol_regime_adjustment:
    high_vol_sizing_multiplier: 0.5
    crisis_regime: "halt_new_trades"
  drawdown_from_peak:
    threshold_pct: 10.0
    action: "reduce_all_sizing_50pct"

Adaptive Sizing (Rules → ML)

Starts as rules-based, graduates to XGBoost at month 6+ when sufficient data exists:

def adaptive_sizing(
    base_risk_pct: float,
    regime_confidence: float,
    iv_rank: float,
    recent_win_rate_20: float,
    portfolio_heat: float,
    drawdown_from_peak: float,
) -> float:
    """Rules-based Phase 1. XGBoost replaces this at month 6+."""
    size = base_risk_pct

    if regime_confidence < 0.60:
        size *= 0.5
    if iv_rank > 60:
        size *= 0.75
    elif iv_rank < 25:
        size *= 0.5
    if recent_win_rate_20 < 0.45:
        size *= 0.5
    if drawdown_from_peak > 0.10:
        size *= 0.5

    remaining_heat = 30 - portfolio_heat
    size = min(size, remaining_heat * 0.5)
    return max(0.5, min(size, 4.0))

Risk Policy Configuration

risk_policy:
  version: "2.0"
  portfolio:
    max_heat_pct: 30
    max_single_underlying_pct: 10
    max_asset_class_pct:
      equity_options: 60
      fx: 30
      crypto: 20
    max_correlated_cluster_pct: 20
    min_cash_pct: 20
  sizing:
    default_method: "adaptive_rules"
    base_risk_pct: 2.0
  circuit_breakers:
    daily_loss_halt_pct: 2.0
    weekly_loss_halt_pct: 5.0
    drawdown_halt_pct: 10.0

3.5 Regime Radar — Multi-Layer Regime Intelligence

Regime intelligence operates at three levels: macro (shared across all asset classes), asset-class-specific, and cross-asset correlation.

3.5.1 Macro Regime Radar (HMM)

Answers: "What macro regime are we in?"

Table is illustrative

State

Characteristics

Strategy Implications

Risk-On

Expanding economy, tight spreads, low vol

Full sizing, sell premium, trend-follow, carry trades

Goldilocks

Moderate growth, contained inflation

Selective premium, carry, moderate momentum

Transition

Mixed signals, rising uncertainty

Reduce sizing, defined-risk only, tighten stops

Risk-Off

Deteriorating conditions, widening spreads

Defensive only, no new carry, reduce exposure

Crisis

Dislocation, correlation spike

Halt new trades, manage existing

Recovery

Early regime improvement

Cautious re-entry, smaller size

Feature engineering from free sources (Not exhaustive)

FRED: 2s10s spread, BAA-AAA spread, initial claims z-score, NFCI, breakeven rates

Market data: VIX + VIX/VIX3M ratio, SPY 50/200 MA ratio, XLK/XLU ratio, LQD/TLT ratio

CFTC: Net speculative positioning in ES, NQ, VX futures

Derived: Rolling z-scores (63/126/252d), rate of change, cross-feature interactions

class RegimeRadar:
    def __init__(self, n_regimes: int = 5):
        self.hmm = GaussianHMM(n_components=n_regimes, covariance_type="full", n_iter=200)
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=10)

    def predict_regime(self, features: pd.DataFrame) -> RegimeOutput:
        scaled = self.scaler.transform(features)
        reduced = self.pca.transform(scaled)
        probs = self.hmm.predict_proba(reduced)
        return RegimeOutput(
            current_regime=self._label_regime(probs[-1]),
            probabilities=dict(zip(self.regime_labels, probs[-1])),
            feature_importances=self._compute_importances(features),
            confidence=max(probs[-1]),
            transition_alert=self._detect_transition(probs),
            probability_trend_3d=self._compute_trend(probs, days=3),
        )

Training: expanding window, retrained monthly. PCA reduces 15–20 features to 8–10 components.

Regime Radar runs as an independent service publishing to Redis. The Core Engine reads regime state but never calls Regime Radar synchronously during trade execution. If Regime Radar is offline, the engine defaults to neutral/allow-all.

3.5.2 FX Regime Model (XGBoost Classifier)

Answers: "Which FX factor is currently dominant?"

Labels: carry, momentum, mean_reversion, risk_off_unwind

class FXRegimeModel:
    def __init__(self):
        self.model = XGBClassifier(
            n_estimators=100, max_depth=4,
            min_child_weight=10, subsample=0.8,
            colsample_bytree=0.8,
        )

    FEATURES = [
        "us_2y_yield", "rate_differential", "rate_diff_momentum_20d",
        "fx_implied_vol_1m", "vol_of_vol_20d", "vix",
        "pair_return_20d", "pair_return_60d", "dxy_return_20d",
        "deviation_from_sma_200", "rsi_14", "zscore_60d",
        "credit_spread_zscore", "gold_return_20d",
        "equity_fx_correlation_30d",
    ]

Output feeds position construction: if regime = carry → rank pairs by carry/vol ratio; if momentum → rank by return; if risk_off_unwind → reduce/hedge.

Training: 10 years daily data (~2500 samples). Retrained monthly.

3.5.3 Crypto Trend Model (Two-Stage)

Answers: "Is there a tradeable trend, and how strong?"

class CryptoTrendModel:
    def __init__(self):
        # Stage 1: Trend exists? (logistic regression — robust, interpretable)
        self.trend_classifier = LogisticRegression(penalty="l1", C=0.1)
        # Stage 2: Trend strength (XGBoost regressor)
        self.strength_model = XGBRegressor(n_estimators=80, max_depth=3)

    FEATURES = [
        # Momentum
        "return_7d", "return_14d", "return_30d", "return_7d_minus_30d",
        # Trend quality
        "adx_14", "price_above_sma_20", "sma_20_above_sma_50",
        "hurst_exponent_30d",
        # Volatility
        "realized_vol_14d", "vol_zscore_60d",
        # Crypto-specific
        "funding_rate_7d_avg", "exchange_reserve_change_7d",
        "stablecoin_supply_change_7d", "btc_dominance_change_7d",
        # Cross-asset
        "btc_return_7d", "spy_return_7d", "dxy_return_7d",
    ]

Two-stage because the critical decision in crypto isn't direction — it's "is there a tradeable trend at all?" Logistic regression for stage 1 (binary, robust). XGBoost for stage 2 (non-linear interactions for strength estimation).

Hurst exponent is the key feature: H > 0.55 = trending (momentum works), H < 0.45 = mean-reverting (fade or stay flat), H ≈ 0.5 = random walk (don't trade).

3.5.4 Correlation Regime (PCA)

Answers: "How diversified is the portfolio right now?"

def correlation_regime(returns_matrix: pd.DataFrame, threshold: float = 0.80):
    corr = returns_matrix.corr()
    eigenvalues = np.linalg.eigvalsh[corr](::-1)
    explained = np.cumsum(eigenvalues) / np.sum(eigenvalues)
    n_components = int(np.searchsorted(explained, threshold) + 1)
    first_pc_share = eigenvalues[0] / np.sum(eigenvalues)

    return {
        "n_components_for_80pct": n_components,
        "first_pc_share": first_pc_share,
        "regime": "concentrated" if n_components <= 2 else "diversified",
    }

When correlation regime is "concentrated" (few PCs explain most variance), diversification benefit has collapsed. The allocation layer should favor defensive positions regardless of individual asset-class signals. This is a direct input to the allocation bandit.

3.6 Strategy Templates

Strategy templates are declarative YAML specs. The engine's Template Resolver maps abstract parameters to concrete broker/data attributes. Templates support regime-conditional parameter overrides.

Example: Iron Condor (Options)

strategy:
  name: "Iron Condor"
  type: "options_income"
  underlying_class: "equity_options"
  legs: 4
  structure:
    - { role: "short_put", position: "sell" }
    - { role: "long_put", position: "buy" }
    - { role: "short_call", position: "sell" }
    - { role: "long_call", position: "buy" }

  regime_requirements:
    allowed_regimes: ["goldilocks", "risk_on"]
    min_regime_confidence: 0.60

  volatility_requirements:
    iv_rank:
      min: 30
      lookback_days: 252
    term_structure:
      max_contango_ratio: 1.05
    vix_regime:
      min: 14
      max: 35

  technical_requirements:
    range_confirmation:
      method: "atr_channel"
      lookback: 20
      atr_multiplier: 1.5
      reference_ma: 20
    trend_filter:
      method: "adx"
      max_adx: 25
      lookback: 14

  entry:
    short_put:
      method: "delta_and_support"
      delta_target: [-0.20, -0.15]
      support_buffer: "at_or_below"
    long_put:
      method: "fixed_width"
      width: 5
    short_call:
      method: "delta_and_resistance"
      delta_target: [0.15, 0.20]
      resistance_buffer: "at_or_above"
    long_call:
      method: "fixed_width"
      width: 5
    dte_range: [30, 50]
    strike_selection_priority: "support_resistance_first"

  management:
    profit_target_pct: 50
    stop_loss_pct: 200
    dte_exit: 14
    breach_action:
      trigger: "short_strike_tested"
      action: "close_tested_side"
    vol_exit:
      trigger: "iv_rank_spike"
      threshold: 70
      action: "close_full"
    roll:
      enabled: false

# Regime-conditional parameter overrides

  regime_overrides:
    goldilocks:
      entry:
        short_put:
          delta_target: [-0.20, -0.15]
    risk_on:
      entry:
        short_put:
          delta_target: [-0.25, -0.18]
      management:
        profit_target_pct: 65

  sizing:
    method: "from_bot_config"

When strike selection produces a conflict between delta target and S/R level, the approval notification shows both options and lets the human decide.

Multi-leg monitoring tracks per-side P&L:

@dataclass
class ICMonitorState:
    put_spread_pnl: float
    call_spread_pnl: float
    aggregate_pnl: float
    put_side_breached: bool
    call_side_breached: bool
    current_iv_rank: float
    dte_remaining: int
    regime: str

Example: FX Momentum (FX)

strategy:
  name: "FX Momentum"
  type: "fx_directional"
  underlying_class: "fx"

  regime_requirements:
    fx_regime_allowed: ["momentum", "carry"]
    min_regime_confidence: 0.60

  technical_requirements:
    trend_confirmation:
      hurst_min: 0.55
      adx_min: 20
    entry_method: "breakout_of_20d_range"

  entry:
    direction: "from_model"          # FX regime model determines long/short
    order_type: "limit"
    entry_offset_atr: 0.1            # limit order 0.1 ATR from current price

  management:
    stop_loss:
      method: "atr_multiple"
      multiplier: 2.0
    profit_target:
      method: "atr_multiple"
      multiplier: 3.0
    time_exit_days: 7
    trailing_stop:
      enabled: true
      activation_atr: 1.5
      trail_distance_atr: 1.0

  sizing:
    method: "from_bot_config"

Example: Crypto Momentum (Crypto)

strategy:
  name: "Crypto Momentum"
  type: "crypto_directional"
  underlying_class: "crypto"

  regime_requirements:
    trend_exists: true
    hurst_min: 0.55
    min_trend_confidence: 0.65

  entry:
    direction: "from_model"
    order_type: "market"

  management:
    stop_loss:
      method: "atr_multiple"
      multiplier: 2.5               # wider for crypto vol
    profit_target:
      method: "atr_multiple"
      multiplier: 4.0
    time_exit_days: 7
    vol_exit:
      trigger: "vol_zscore_above"
      threshold: 2.0                 # exit if vol spikes >2 std
      action: "close_full"
    hurst_exit:
      trigger: "hurst_below"
      threshold: 0.45                # trend broken, exit
      action: "close_full"

  sizing:
    method: "from_bot_config"
    hard_cap_pct: 3.0               # max 3% of portfolio per crypto token

1. Data Architecture

Data Sources & Cost

Source

Data

Frequency

Cost

Phase

FRED API

Macro indicators, rates, yield curves

Daily/Weekly

Free

Phase 1

Yahoo Finance

OHLCV (equities, FX, crypto), VIX

Daily

Free

Phase 1

CFTC COT

Positioning data

Weekly

Free

Phase 1

IBKR TWS API

Option chains, fills, positions, FX quotes

Real-time

Broker account

Phase 1

TradingView

Signal webhooks

Event-driven

Free / $15/mo

Phase 1

CBOE

VIX term structure

Daily

Free (delayed)

Phase 1

CoinGecko

Crypto OHLCV, market cap

Daily

Free (rate limited)

Phase 2

Binance/Hyperliquid API

Funding rates, open interest

Daily

Free

Phase 2

CryptoQuant/Glassnode free tier

Exchange reserves, flows

Daily

Free (limited)

Phase 2

DeFi Llama

Stablecoin supply

Daily

Free

Phase 2

Total Phase 1

$0–15/mo

Total Phase 2

$0–15/mo

Polygon.io

Historical equity data

Backfill

$29/mo

Phase 3

Storage Architecture

PostgreSQL + TimescaleDB (primary persistence)
├── trades              — full trade lifecycle, fills, P&L, bandit feature snapshots
├── positions           — current open positions, Greeks/price snapshots
├── signals             — all signals received, action taken
├── candidates          — all candidates generated, scored, selected/skipped
├── risk_events         — circuit breaker activations, risk check results
├── regime_history      — daily regime classifications + probabilities (all models)
├── bot_configs         — bot definitions, strategy templates
├── bandit_state        — per-template A matrix + b vector + observation count
├── bandit_decisions    — per-scan scoring log (context, scores, selection, outcome)
├── fill_quality        — expected vs actual fill, slippage tracking
├── annotations         — human selection reasoning tags
├── audit_log           — all state transitions, approvals, config changes
│
├── [TimescaleDB hypertables]
│   ├── ohlcv           — price time-series for all universe instruments
│   ├── macro_features  — FRED/derived features for Regime Radar
│   ├── iv_history      — implied vol history per underlying (IV rank computation)
│   ├── funding_rates   — crypto perpetual swap funding rates
│   └── hurst_series    — rolling Hurst exponent per instrument
│
└── [user_id on every table for SaaS-readiness]

Redis (ephemeral state)
├── bot:state:{id}            — current state machine state
├── regime:macro:current      — latest macro regime classification
├── regime:fx:current         — latest FX regime classification
├── regime:crypto:current     — latest crypto trend classification
├── regime:correlation        — latest correlation regime (PCA)
├── quotes:{symbol}           — price cache
├── locks:order:{id}          — distributed locking for order execution
└── circuit_breaker:*         — daily/weekly loss accumulators

Data Pipeline

FRED ──────┐
Yahoo ─────┤
CFTC ──────┤──→ Feature Engineering ──→ TimescaleDB
CBOE ──────┤                               │
CoinGecko ─┤                               ├──→ Macro Regime Radar (HMM)   ──→ Redis
Binance ───┘                               ├──→ FX Regime Model (XGBoost)  ──→ Redis
                                           ├──→ Crypto Trend Model (LogReg+XGB) ──→ Redis
                                           └──→ Correlation Regime (PCA)    ──→ Redis

TradingView ──→ Webhook ──┐
Scheduler ──→ Cron ────────┤──→ Core Engine ──→ Template Resolver
CLI/Dashboard ─────────────┘        │               │
                                    │          ┌────┘
                                    ▼          ▼
                              PostgreSQL   Venue Adapters (IBKR, OANDA, Hyperliquid)

1. Technical Architecture

Stack

Layer

Technology

Rationale

Backend

FastAPI (Python 3.12+)

Async-native, Python quant ecosystem

Task Queue

Celery + Redis

Scheduled jobs, monitoring loops

Database

PostgreSQL 16 + TimescaleDB

Relational + time-series in one engine

Cache/State

Redis 7

Bot state, regime cache, pub/sub

ML

hmmlearn, scikit-learn, xgboost

HMM, classifiers, regressors — all lightweight

Quant

numpy, pandas, pandas-ta

Feature engineering, TA computation

Broker

ib_insync

Mature async Python wrapper for TWS API

Notifications

python-telegram-bot

Approval flow, alerts, annotations

LLM

Anthropic API (Sonnet)

Risk commentary, weekly digest

Deployment

Docker Compose

Single-node deployment

Project Structure

dorado/
├── core/
│   ├── engine.py                  # Bot lifecycle orchestrator
│   ├── state_machine.py           # State transition logic
│   ├── signal.py                  # Signal schema + ingestion
│   ├── order.py                   # Order construction + execution
│   ├── scanner.py                 # Daily scan orchestrator
│   ├── candidate.py               # Candidate generation + ranking
│   └── resolver.py                # Template resolver (params → broker attributes)
├── universe/
│   ├── manager.py                 # Universe CRUD + validation
│   └── data_pipeline.py           # Per-underlying data fetch orchestration
├── venues/
│   ├── base.py                    # VenueAdapter ABCs
│   ├── ibkr/
│   │   ├── adapter.py             # IBKRAdapter (options + equities + FX)
│   │   ├── chain.py               # Option chain parsing + validation
│   │   └── connection.py          # TWS connection management
│   ├── paper.py                   # PaperAdapter (simulation)
│   ├── oanda.py                   # OANDA FX adapter (Phase 2)
│   └── hyperliquid.py             # Hyperliquid crypto adapter (Phase 2)
├── risk/
│   ├── engine.py                  # Risk check orchestrator
│   ├── trade_level.py             # Per-trade checks
│   ├── portfolio.py               # Portfolio-level aggregation (cross-asset)
│   ├── circuit_breaker.py         # Circuit breaker state machine
│   └── sizing.py                  # Position sizing (rules → ML)
├── regime/
│   ├── macro_radar.py             # HMM-based macro regime
│   ├── fx_regime.py               # XGBoost FX factor classifier
│   ├── crypto_trend.py            # LogReg + XGBoost crypto trend model
│   ├── correlation_regime.py      # PCA-based correlation regime
│   ├── features.py                # Shared feature engineering pipeline
│   └── sources/
│       ├── fred.py
│       ├── yahoo.py
│       ├── cftc.py
│       ├── coingecko.py
│       └── exchange_data.py       # Funding rates, reserves
├── ml/
│   ├── bandit.py                  # LinUCB contextual bandit (~80 lines)
│   ├── allocation_bandit.py       # Cross-asset allocation bandit
│   ├── parameter_bandit.py        # Strategy parameter adaptation
│   ├── exit_model.py              # Random forest exit timing
│   ├── features.py                # ML feature extraction
│   ├── rewards.py                 # Reward computation (final + intermediate)
│   └── diagnostics.py             # Model inspection + weekly reporting
├── ta/
│   ├── engine.py                  # TA computation module
│   ├── indicators.py              # ADX, ATR, SMA, RSI, pivots
│   └── hurst.py                   # Hurst exponent computation
├── api/
│   ├── main.py                    # FastAPI app
│   └── routes/
│       ├── signals.py             # Webhook endpoint
│       ├── bots.py                # Bot CRUD
│       ├── universe.py            # Universe management
│       ├── risk.py                # Risk dashboard data
│       ├── regime.py              # Regime status endpoints
│       └── candidates.py          # Candidate list + selection
├── notifications/
│   ├── telegram.py                # Approval flow, alerts, annotations
│   └── base.py                    # Notification ABC
├── tasks/
│   ├── data_fetch.py              # Scheduled data collection
│   ├── regime_update.py           # Daily regime classification (all models)
│   ├── daily_scan.py              # Daily candidate generation + ranking
│   ├── monitoring.py              # Position monitoring loop
│   ├── reconciliation.py          # Broker position reconciliation
│   ├── bandit_update.py           # Weekly bandit batch update + decay
│   ├── weekly_digest.py           # Saturday morning summary report
│   └── model_retrain.py           # Monthly model retraining
├── config/
│   ├── risk_policy.yaml
│   ├── universe.yaml
│   ├── scoring_weights.yaml
│   ├── bots/
│   └── strategies/
├── db/
│   ├── models.py
│   ├── migrations/
│   └── session.py
├── tests/
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml

Key Architectural Decisions

1. IBKR TWS API via ib_insync

TWS API wins over Client Portal for options (full chain access, combo orders), Python ecosystem maturity, and reliability. Requires IB Gateway running in Docker (acceptable for personal use). For SaaS, would be replaced by Alpaca/Tradier for equities or Client Portal with managed auth.

1. YAML DSL with code hook escape hatch

YAML covers ~80% of strategies. Edge cases (conditional rolls based on compound P&L + DTE + delta conditions) use a code_hook field pointing to a sandboxed Python callable. Don't build the code hook in Phase 1 — leave the schema slot open.

1. Regime Radar as async publisher

All regime models publish to Redis independently. Core Engine reads cached state. No synchronous dependency during trade execution. If any regime model is offline, engine defaults to neutral/allow-all.

1. Paper trading as venue adapter, not feature

Same code path for live and paper. venue_mode per bot. Enables simultaneous live and paper execution for canary release and full-feedback data collection.

1. user_id on every table from day 1

Cheapest SaaS insurance. Zero runtime cost, prevents full migration later. Don't add user routing, auth, or multi-tenancy logic — just the column.

1. ML Layer — Detailed Design Ideas

6.1 Priority Stack

LAYER 0: Feature engineering pipeline (shared infrastructure)
  FRED, Yahoo, CoinGecko, exchange APIs → TimescaleDB
  Cost: $0. Build: Phase 1.

LAYER 1: Regime classification (per asset class)
  Macro:  HMM (hmmlearn)
  FX:     XGBoost classifier
  Crypto: Logistic regression + XGBoost (two-stage)
  Correlation: PCA on cross-asset returns
  Cost: $0. Trains in seconds. Build: Phase 1 (macro), Phase 2 (FX, crypto).

LAYER 2: Adaptive sizing (rules → XGBoost)
  How much capital per trade, conditioned on regime + vol + performance.
  Build: Rules Phase 1, XGBoost month 6+.

LAYER 3: Allocation bandit (portfolio level)
  How to distribute risk budget across asset classes.
  Monthly cadence. Portfolio-level Sharpe as reward.
  Build: Month 6+.

LAYER 4: Exit model (random forest)
  Hold vs close decision for open positions.
  Build: Month 9+.

LAYER 5: Parameter adaptation bandit
  Which parameter bundle per strategy in current conditions.
  Build: Month 9+.

LAYER 6: Candidate ranking bandit
  Scoring individual candidates within an underlying.
  Build: Month 9+. Marginal value at personal scale.
  Primary value: instrumentation forces measurement discipline.

6.2 Contextual Bandit Implementation

LinUCB implementation. ~80 lines, numpy only, no external dependencies.

class TradeBandit:
    def __init__(self, n_features: int, alpha: float = 1.5,
                 paper_discount: float = 0.7, paper_weight: float = 0.5,
                 decay: float = 0.995, regularization: float = 1.0):
        self.n_features = n_features
        self.alpha = alpha
        self.paper_discount = paper_discount
        self.paper_weight = paper_weight
        self.decay = decay
        self.reg = regularization
        self.models = {}   # template -> {"A": ndarray, "b": ndarray, "n": int}

    def score(self, template, candidate_features):
        """Score (candidate_id, feature_vector) pairs. Returns sorted by UCB score."""
        if template not in self.models:
            self._init_model(template)
        m = self.models[template]
        A, b = m["A"], m["b"]
        effective_alpha = self._adaptive_alpha(m["n"])
        results = []
        for cid, x in candidate_features:
            theta = np.linalg.solve(A, b)
            expected = float(theta @ x)
            unc = float(effective_alpha * np.sqrt(x @ np.linalg.solve(A, x)))
            results.append(ScoredCandidate(cid, expected, unc, expected + unc, x))
        results.sort(key=lambda r: r.total_score, reverse=True)
        return results

    def update(self, template, features, reward, source="live"):
        """Update model with observed reward."""
        if template not in self.models:
            self._init_model(template)
        m = self.models[template]
        if source == "paper":
            reward *= self.paper_discount
            w = self.paper_weight
        elif source == "intermediate":
            w = 0.3
        else:
            w = 1.0
        m["A"] += w * np.outer(features, features)
        m["b"] += w * reward * features
        m["n"] += 1

    def apply_decay(self):
        """Weekly. Decays old observations so model adapts."""
        for m in self.models.values():
            d = self.n_features
            m["A"] = self.decay * m["A"] + (1 - self.decay) * self.reg * np.eye(d)
            m["b"] = self.decay * m["b"]

Delayed Reward Handling

Trades take 3–45 days to resolve. Three mechanisms:

1. Intermediate reward signals — Checkpoint rewards at day 7 and day 14 of open position, weighted at 30% of full update. Uses entry-time feature snapshot (no future leakage).

def compute_intermediate_reward(trade, days_open):
    pnl_pct = trade.unrealized_pnl / abs(trade.max_loss)
    if days_open == 7:
        if pnl_pct > 0.10: return 0.15
        elif pnl_pct < -0.30: return -0.20
    if days_open == 14:
        if pnl_pct > 0.25: return 0.30
        elif pnl_pct < -0.50: return -0.40
    return None

1. Weekly batch updates — Reward buffer collects resolved trades, flushed every Saturday with decay application.

2. Entry-time feature snapshots — All bandit features frozen at trade entry time and stored in the trades table. The bandit learns "given this context at decision time, what reward resulted?" — never uses resolution-time features.

Reward Function

def compute_reward(trade):
    """Normalized to [-1, +1]. Comparable across trade structures."""
    if trade.max_loss == 0: return 0.0
    raw = trade.realized_pnl / abs(trade.max_loss)
    return max(-1.0, min(1.0, raw))

Allocation Bandit

The highest-value bandit application. Operates at portfolio level, monthly cadence.

ALLOCATION_ARMS = {
    "equity_heavy":     {"options": 0.60, "fx": 0.25, "crypto": 0.15},
    "balanced":         {"options": 0.35, "fx": 0.30, "crypto": 0.35},
    "crypto_momentum":  {"options": 0.20, "fx": 0.20, "crypto": 0.60},
    "defensive":        {"options": 0.60, "fx": 0.30, "crypto": 0.10},
    "anti_equity":      {"options": 0.10, "fx": 0.40, "crypto": 0.50},
    # ... 10-15 bundles
}

Context: regime outputs from all models + cross-asset correlations + PCA correlation regime. Reward: portfolio-level Sharpe over 30-day window (higher signal-to-noise than individual trade P&L). Paper trading all non-recommended allocations gives full feedback — 12 months × 10 bundles = 120 observations/year.

6.3 Exit Model (Random Forest)

class ExitModel:
    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=100, max_depth=5, min_samples_leaf=20,
        )

    FEATURES = [
        "days_open", "unrealized_pnl_pct", "pnl_velocity_3d",
        "regime_at_entry", "regime_now", "regime_changed_since_entry",
        "vol_change_since_entry", "underlying_move_since_entry",
        "hurst_current", "distance_to_profit_target",
        "distance_to_stop_loss", "time_to_expiry_pct",
    ]

Random forest over XGBoost for interpretability — you can print decision paths and verify exit logic makes sense. Learns patterns like "regime changed + vol expanding → close early."

Build at month 9+ when sufficient live + paper trade data exists.

6.4 Convergence Timeline (Accounting for Delayed Rewards)

                    Scans    Resolved    ML Status
Month 1-2           40       0           No updates. Manual picks. Collecting data.
Month 3-4           80       40-50       First theta forming. Inspect weekly.
Month 5-6           120      100-120     Patterns emerging. Activate adaptive sizing (XGBoost).
Month 7-8           160      160-180     Bandit informative. Start comparing vs manual weights.
Month 9-10          200      220-250     Activate allocation bandit. Exit model viable.
Month 12+           300      350-400     Models calibrated. Auto-selection available (with human veto).

Intermediate rewards roughly double effective observation rate. Paper trading all non-selected candidates triples data accumulation. Combined: ~600+ effective observations in Year 1 despite only ~200 live trades.

1. Research Integration (Deferred, Architecture Hooks Only)

Paper-Forward Testing as Research Engine

The paper trading pipeline IS the walk-forward testing engine. No backtesting engine needed initially.

After 6 months of paper data: "Iron condors in Goldilocks with IV rank 35–50 have a 68% win rate across 47 paper + 12 live observations." This is walk-forward validation emerging organically.

Scotch Integration (Phase 3–4)

Scotch (fundamental analysis)
  → "underlying attractiveness" scores
    → feeds bot signal generation as filter
      → Core Engine executes

New signal source type in strategy YAML:

signal_source: "scotch"
scotch_config:
  min_variant_score: 0.7
  refresh_frequency: "weekly"

Full Research Workbench (Phase 4–5, SaaS)

Strategy ideation + historical backtesting (requires Polygon.io, ~$29/mo). Parameter optimization with walk-forward cross-validation. Direct strategy-to-bot deployment.

Minimum Viable Hook

Add research_context JSONB column to signals table now. Costs nothing, captures provenance chain when research eventually generates signals.

1. Phase Breakdown

## Foundation Phase (Pre-Phase 1): OSS Core

__Scope lock:__ No IBKR/live execution work in this phase.

### Deliverables

1. Data spine hardening
   - Universe -> stocks -> OHLCV -> signals endpoints stable
   - Refresh/status semantics finalized for UI polling
2. Strategy templates
   - Risk/Trade/Strategy template schemas + CRUD
   - Validation rules + versioned config payloads
3. Candidate engine (rules-first)
   - Deterministic signal filters over persisted TA features
   - Candidate scoring/ranking (non-LLM baseline)
4. Risk layer (pre-trade)
   - Position sizing constraints, capital caps, reject reasons
5. Operator UI (Next.js)
   - Universe selection, candles/signals views
   - Template editor + candidate list + risk gate explanations
6. Journaling baseline
   - Log selected + skipped candidates with reason codes

### Exit Criteria

- End-to-end: select universe -> load candles/signals -> generate candidates -> apply risk gates -> persist decision log
- Stable API contract consumed by frontend
- No broker adapter dependency for core workflow

Phase 1: Dogfood — Options Core

Component

Deliverable

Universe Manager

Define universe, validate symbols, initialize data pipelines

Core Engine

Scan-based candidate generation for IBKR options

Venue Adapters

IBKRAdapter + PaperAdapter

Template Resolver

Maps YAML params to broker chain data with quality validation

TA Engine

ADX, ATR, SMA, pivots, IV rank computation

Strategy Templates

Iron condor, short put wheel, put vertical, covered call

Signal Ingestion

TradingView webhook + scheduled scan + manual CLI

State Machine

Full lifecycle with per-side tracking for multi-leg

Risk Radar

Trade-level sizing, portfolio heat, circuit breakers, adaptive sizing (rules)

Regime Radar

Macro HMM (V0, 4 states, FRED + VIX features)

Candidate Pipeline

Gate cascade → generation → weighted scoring → portfolio selection

Paper Trading

All non-selected candidates auto-paper. Canary release workflow.

Human-in-the-Loop

Telegram: candidate list, approval, annotations, alerts

Persistence

PostgreSQL + TimescaleDB + Redis. Bandit feature snapshots in trades table.

Deployment

Docker Compose

Phase 2: Multi-Asset + ML Foundation

Component

Deliverable

FX Support

FX venue adapter (IBKR or OANDA), FX momentum template, carry/vol sizing

Crypto Support

Crypto venue adapter (Hyperliquid), momentum template, funding rate features

FX Regime Model

XGBoost classifier (carry/momentum/MR/risk_off)

Crypto Trend Model

LogReg + XGBoost two-stage (trend exists + strength)

Correlation Regime

PCA on cross-asset returns, "concentrated" vs "diversified"

Hurst Exponent

Rolling computation per FX/crypto instrument

Adaptive Sizing

XGBoost replacing rules-based sizing

LLM Commentary

Risk analyst narrative in candidate notifications

Weighted Scoring Calibration

Quarterly review using paper + live outcome data

Fill Quality Tracking

Expected vs actual fill, slippage per underlying/strategy

Phase 3: ML Maturity

Component

Deliverable

Allocation Bandit

Cross-asset allocation optimization, monthly cadence

Parameter Bandit

Regime-conditional parameter adaptation per template

Candidate Bandit

LinUCB ranking (shadow mode, compare to weighted scoring)

Exit Model

Random forest hold/close classifier

Weekly Digest

LLM-summarized performance report with bandit diagnostics

Canary Automation

Measured paper-to-live discount per template per underlying

Scotch Integration

Fundamental attractiveness scores as signal filter

Phase 4: SaaS Preparation

Component

Deliverable

Web Dashboard

Candidate selection UI, portfolio view, regime visualization

Multi-tenant Auth

User registration, API keys, session management

Strategy Builder

Form wizard mapping 1:1 to battle-tested YAML schema

Billing

Template tiers, regime signal access as premium

Research Workbench

Backtesting + parameter optimization

Success Criteria

Phase 1: Execute ≥10 trades end-to-end. Zero unintended executions. Full audit trail. Regime classification daily. Circuit breaker tested. System runs unattended 2+ weeks. All non-selected candidates paper traded.

Phase 2: FX and crypto trades executing through same pipeline. Cross-asset correlation regime computed daily. Adaptive sizing XGBoost trained and active. Measured paper-to-live discount for 2+ templates.

Phase 3: Allocation bandit producing monthly recommendations. Exit model demonstrating value (comparison to fixed rules). 500+ total observations (live + paper). ML diagnostics in weekly report.

1. Implementation Priority (Recommended Build Order)

Week 1–2:   Database schema + models + migrations (with bandit columns,
            candidate table, fill quality table, annotations table)
            Universe manager + validation
            YAML schemas: universe, bot config, strategy templates, risk policy

Week 3–4:   IBKRAdapter — connection, account state, option chains, orders
            PaperAdapter — simulation against live market data
            Chain data quality validation module

Week 5–6:   State machine implementation + persistence
            Signal ingestion (webhook + scheduled scan + manual CLI)
            TA Engine (ADX, ATR, SMA, pivots, IV rank computation)

Week 7–8:   Risk Radar — trade-level sizing + portfolio heat + circuit breakers
            Gate cascade implementation (regime → vol → TA)
            Template Resolver (YAML params → broker attributes)

Week 9–10:  Candidate generation pipeline (scan → gates → resolve → score → rank)
            Portfolio-aware selection loop
            Telegram bot — candidate list, approve/reject, annotations

Week 11–12: Position monitoring loop (live: 15 min, paper: 60 min)
            Per-side P&L tracking for multi-leg structures
            Reconciliation job (broker positions vs. local state)

Week 13–14: Regime Radar V0 — macro HMM feature pipeline + training + Redis publish
            Regime filter integration into gate cascade

Week 15–16: Auto-paper-trading of non-selected candidates
            Canary release workflow (simulation → paper → canary → live)
            Fill quality tracking (expected vs actual)

Week 17–18: Docker Compose deployment
            Paper trading end-to-end testing (2+ weeks)
            Bug fixes, edge case handling

Week 19–20: Go live with real capital (small size, 2-3 bots, reduced sizing)
            Begin data collection for ML layers

Month 5–6:  FX venue adapter + FX regime model + FX templates
Month 6–7:  Crypto venue adapter + crypto trend model + crypto templates
Month 7–8:  Correlation regime (PCA) + adaptive sizing (XGBoost)
Month 8–9:  LLM risk commentary + weekly digest
Month 9+:   Allocation bandit + exit model + parameter bandit

1. Open Questions for Technical Spikes

Spike 1: IBKR TWS Connection Reliability

IB Gateway in Docker: version pinning, auto-restart, reconnection logic in ib_insync, order state recovery after disconnects. Rate limit testing under monitoring + order flow load.

Spike 2: HMM Feature Selection & Training

8–10 initial features, compare 4-state vs 5-state models on 2000–2025 data. Evaluate regime stability (average duration). Label post-hoc against known macro environments. Monthly expanding window retraining.

Spike 3: Strategy DSL Expressiveness

Enumerate Phase 1 strategies (iron condor, wheel, vertical, covered call). Map to YAML. Identify edge cases. Reserve code_hook schema slot.

Spike 4: Hurst Exponent Stability

Validate Hurst exponent reliability for FX/crypto trend detection. Compare R/S estimation vs DFA method. Test sensitivity to lookback period (20 vs 30 vs 60 days). Determine minimum data requirements for stable estimates.

Spike 5: FX/Crypto Venue Selection

FX: OANDA (REST, well-documented) vs IBKR (already integrated, less FX-focused). Crypto: Hyperliquid (on-chain, transparent) vs Deribit (options future). Evaluate API quality, fill simulation capability for paper trading.

Spike 6: Cross-Asset Correlation Stability

How frequently does the PCA correlation regime flip? If it flips daily, it's noise. Backtest on 2015–2025 cross-asset returns to determine update cadence and threshold for "concentrated" classification.

1. Risk Register

Risk

Impact

Likelihood

Mitigation

IBKR connection instability

Missed fills, orphaned orders

Medium

Auto-reconnect, reconciliation job, paper trading first month

HMM produces unstable regimes

Useless signals, false confidence

Medium

Spike 2 validation, manual override, default to allow-all

Scope creep into ML before core works

Delays Phase 1

High

ML layers explicitly deferred. Phase 1 = gates + rules + paper trading.

Chain data quality worse than expected

Bad strike selection, poor fills

Medium

Quality validation + retry + human override. Measured fill quality tracking.

Paper trading gives false confidence

Over-optimistic performance

Medium

Empirically measured paper-to-live discount via canary. Never trust paper P&L at face value.

Bandit never converges at personal scale

Wasted engineering effort

Medium

Bandit is 80 lines of numpy. Primary value is instrumentation, not optimization.

FX/crypto venue API instability

Missed trades, data gaps

Medium

Defensive error handling, graceful degradation to options-only

Over-engineering for SaaS

Delays dogfood delivery

High

SaaS hooks are columns and parameters only. Zero routing logic.

Free data source deprecation

Yahoo Finance has broken APIs before

Medium

Abstracted data source clients, fallback sources identified

Model overfitting on small datasets

Degraded ML performance

Medium

Conservative regularization, shallow trees, expanding windows, hold-out validation

1. Budget Summary

Infrastructure:
  VPS (4GB RAM, 2 CPU):                $10–20/mo
  PostgreSQL + TimescaleDB + Redis:      self-hosted, included
  Docker:                                free

Data:
  FRED, Yahoo, CFTC, CBOE:              free
  CoinGecko, Binance/Hyperliquid APIs:   free
  CryptoQuant/Glassnode free tier:        free
  DeFi Llama:                             free
  TradingView (optional):                $0–15/mo
  IBKR market data:                       included with account

ML:
  scikit-learn, xgboost, hmmlearn, numpy: free
  Training compute:                        seconds per model on VPS

LLM:
  Anthropic API (Sonnet):                 ~$1–5/mo

Total: $15–30/month
