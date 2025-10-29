# **Product Requirements Document — Chronos v0.01 (OSS)**

## **Overview**

Chronos v0.01 is the open-source prototype of Calico’s options strategy engine. It enables retail users and quant hobbyists to:

1. Define their trade universe (stocks under coverage).
2. Download and locally store recent price data.
3. Generate technical analysis (TA) signals.
4. Create structured templates for risk, trade, and strategy logic.
5. Use an LLM to rank and suggest candidate trades.

This version prioritizes architectural clarity, modularity, and local reproducibility — serving as the skeleton for future strategy automation and backtesting modules.

---

### **Objectives**

* Deliver a working **E2E pipeline**: from data ingestion → signal generation → strategy suggestion.
* Keep dependencies lightweight, self-hostable, and open-source compatible.
* Establish a clear **separation of concerns** between front-end (UI), backend (API), and data logic.
* Enable reproducibility for community contributors and model fine-tuning later.

---

### **Scope**

#### **In-Scope**

1. **Universe Management**

   * User adds/removes tickers to a “Universe.”
   * Persist universe in SQLite.
   * Basic CRUD via API and frontend interface.

2. **Data Pipeline (Candlesticks)**

   * Fetch last 90 days of OHLCV data for each ticker.
   * Store locally in SQLite.
   * Scheduled refresh (manual button trigger for v0.01).
   * Data source: YahooFinance or Alpaca free API.

3. **Technical Analysis Engine**

   * Use TA-Lib or `pandas-ta` to compute baseline indicators:

     * RSI, MACD, EMA(20/50), Bollinger Bands.
   * Persist signals to database with timestamps.
   * Expose via API endpoint for use by strategy logic and UI.

4. **Strategy and Risk Templates**

   * Users define JSON-based templates for:

     * **Risk Parameters**: max capital, max loss per trade, delta limits.
     * **Trade Parameters**: entry/exit conditions, DTE range, spread width.
     * **Strategy Templates**: combination of above, plus signal conditions (e.g., “RSI < 30 + bullish MACD crossover → Bull Put Spread”).
   * Templates stored in SQLite (Pydantic-validated models).

5. **LLM Trade Suggestion**

   * Connect to local LLM endpoint (OpenAI/DeepSeek compatible).
   * Feed universe + latest signals + template constraints.
   * Return ranked list of trade candidates with reasoning summary.

6. **Frontend (Next.js)**

   * Pages:

     * **Dashboard**: summary of universe + last refresh + LLM trade suggestions.
     * **Universe Manager**: CRUD for tickers.
     * **Templates**: create/edit strategy, risk, and trade templates.
     * **Signals View**: tabular or small-chart view of latest indicators per ticker.
   * Use API routes to connect to FastAPI backend.

---

### **Out-of-Scope (for v0.01)**

* Broker integration (IBKR/Tasty/Alpaca orders)
* Backtesting or performance tracking
* Authentication/multi-user system
* Persistent cloud DB (SQLite only)
* Advanced scheduling (manual refresh only)

---

### **Technical Design**

#### **Frontend (Next.js 14+)**

* Framework: Next.js App Router (TypeScript)
* State management: React Query or SWR
* UI: TailwindCSS + shadcn/ui components
* API integration: REST calls to FastAPI backend
* Charts: lightweight (e.g., `react-financial-charts` or `lightweight-charts`)

#### **Backend (FastAPI)**

* Database: SQLite
* ORM: SQLModel or Tortoise ORM (simple async ORM)
* Schema validation: Pydantic v2
* Background jobs: `APScheduler` (manual trigger for now)
* External dependencies:

  * `yfinance` or `alpaca-py`
  * `pandas`, `pandas-ta`
  * LLM: `openai` or compatible local endpoint client

#### **API Modules**

1. `/universe`

   * GET/POST/DELETE tickers
2. `/data/fetch`

   * GET: trigger refresh, fetch OHLCV for universe
3. `/signals`

   * GET: compute or retrieve last computed indicators
4. `/templates`

   * CRUD for risk/trade/strategy templates
5. `/llm/suggest`

   * POST: send context to LLM, return ranked trade ideas

---

### **Data Model (SQLite + Pydantic)**

| Table              | Fields                                                                            | Description                   |
| ------------------ | --------------------------------------------------------------------------------- | ----------------------------- |
| `universe`         | `id`, `ticker`, `name`, `sector`                                                  | Tracked stocks                |
| `candles`          | `id`, `ticker`, `date`, `open`, `high`, `low`, `close`, `volume`                  | 90-day OHLCV data             |
| `signals`          | `id`, `ticker`, `date`, `rsi`, `macd`, `ema_20`, `ema_50`, `bb_upper`, `bb_lower` | TA indicators                 |
| `templates`        | `id`, `type`, `name`, `config_json`                                               | Risk/Trade/Strategy templates |
| `trade_candidates` | `id`, `ticker`, `strategy_id`, `rank`, `rationale`                                | LLM-generated output          |

---
