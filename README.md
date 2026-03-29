# ShockTest

**Prediction markets overreact. We proved it. Now you can trade it.**

ShockTest is a live trading signal system for Polymarket. It detects sudden probability shocks, uses AI to analyze whether they're overreactions, and gives traders interactive tools to size and execute fade positions backed by real statistical data. Built in 24 hours at YHack Spring 2026.

**Live at [shocktest.us](https://shocktest.us)**

---

## The Finding

**59.9% of large Polymarket probability shocks revert within 6 hours** (z = +7.13, p < 0.001).

| Metric | Value |
|--------|-------|
| Markets Analyzed | 1,300+ (Polymarket + Manifold) |
| Total Shocks Detected | 1,500+ |
| 6h Reversion Rate | 59.9% |
| Mean 6h Reversion | +3.45 pp |
| Fade Strategy Win Rate (6h) | 59.9% |
| Avg P&L per $1 Risked (6h) | +$0.035 |

**By category (6h):**

| Category | Win Rate | Avg P&L | Sample Size |
|----------|----------|---------|-------------|
| Politics | 64.7% | +$0.040 | 662 |
| Crypto | 53.5% | +$0.018 | 302 |
| Sports | 56.1% | +$0.048 | 90 |
| Science | 60.6% | +$0.030 | 33 |
| Other | 53.9% | +$0.039 | 145 |

Political markets show the strongest edge at 64.7%, suggesting political shocks are most often overreactions to headlines. Crypto markets revert less reliably at 53.5%.

---

## What It Does

ShockTest is a complete trading workflow: **Detect, Analyze, Trade.**

### Detect
A Python monitor polls Polymarket every 2 minutes, detects large probability moves, and fires live alerts. K2-Think auto-categorizes each market (politics, sports, crypto, etc.). Only shocks from the last hour are shown on the dashboard, keeping the feed focused on actionable signals.

### Analyze
An AI agent (powered by Claude) searches the web for what caused each shock and assesses whether it's an overreaction or legitimate new information. Each shock also gets interactive analysis tools: P&L heatmaps inspired by [optionsprofitcalculator.com](https://www.optionsprofitcalculator.com/), payoff curves, scenario analysis with time-decay modeling, and a trade simulator backed by real backtest data showing win rates and expected P&L for similar shocks.

### Trade
A portfolio builder lets you select multiple shocks, size positions with AI-powered Kelly criterion optimization (via K2-Think), and see combined portfolio payoff graphs with diversification benefits. A Chrome extension overlays shock data directly on Polymarket, highlighting shock bands on the price chart and showing reversion statistics in a floating panel.

---

## How to Use It

1. Open [shocktest.us](https://shocktest.us) and browse the live shock feed
2. Shocks from the last hour are displayed with AI analysis explaining what caused each move
3. Click a shock to see the full probability chart with the shock highlighted
4. Use the P&L heatmap to see your profit/loss across every probability and time-to-resolution combination
5. Use the trade simulator to input a position size and see expected P&L, win rate, and historical distribution
6. Build a portfolio of multiple fade positions and see the combined payoff with diversification benefits
7. Click "Trade on Polymarket" to execute

---

## Architecture

```
Polymarket Gamma API ──┐
Polymarket CLOB API  ──┤
                       ├──> Python scripts ──> MongoDB Atlas ──> Next.js API routes ──> Dashboard
Manifold Markets API ──┘    + live_monitor.py   (shocktest)     (dashboard/api/)       + Chrome Extension
                            + analysis/                                                 + Portfolio Builder
                                │                                                       + Trade Simulator
                                ├──> K2-Think (categorization)
                                └──> Claude (shock analysis via web search)
```

## Tech Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| Data | Polymarket Gamma + CLOB APIs | Market listings and price history |
| Supplemental Data | Manifold Markets API | Additional market diversity |
| Storage | MongoDB Atlas (free M0) | Cloud database for time series, shocks, backtest results |
| Analysis | pandas + numpy | Shock detection, post-shock stats, fade strategy backtest |
| AI Categorization | K2-Think | Auto-classify markets by category |
| AI Shock Analysis | Claude + web search | Explain what caused each shock, assess overreaction likelihood |
| AI Portfolio Optimization | K2-Think | Kelly criterion position sizing |
| Frontend | Next.js 14 + TypeScript + Tailwind CSS + Recharts | Interactive dashboard with trade simulator |
| Browser Extension | Chrome Extensions API | Overlay shock data on Polymarket |
| Deployment | Vercel | Production hosting |
| Domain | Porkbun | shocktest.us |

---

## Team

**Person 1 (Data Pipeline):** Python scripts fetching from Polymarket's Gamma + CLOB APIs, shock detection algorithm, live monitor polling every 2 minutes, K2-Think for market categorization. All data stored in MongoDB Atlas.

**Person 2 (Analysis + AI Agents):** Post-shock reversion analysis, statistical significance testing, backtest engine, Claude-powered web search agent for shock explanation, K2-Think AI for portfolio optimization, and the full Chrome extension.

**Person 3 (Dashboard):** Next.js 14 App Router with TypeScript, Tailwind CSS, and Recharts. Single-page dashboard with featured shock carousel, interactive filtering, shock detail pages with payoff curves and scenario panels, portfolio builder page.

---

## Methodology

### Shock Detection

A shock occurs when the absolute change in implied probability exceeds a threshold within a time window:

```
|p(t2) - p(t1)| >= theta    where t2 - t1 <= T
```

Default parameters (user-configurable):
- **theta** = 0.08 (8 percentage point move)
- **T** = 1 hour

### Post-Shock Measurement

```
shock_size  = p(t2) - p(t1)
post_move   = p(t2 + h) - p(t2)    for h in {1h, 6h, 24h}
reversion   = -sign(shock_size) * post_move
```

Positive reversion = price moved back toward pre-shock level.

### Fade Strategy

```
Entry:  Buy opposite direction at p(t2)
Exit:   Close at p(t2 + h)
P&L:    position_size * reversion
```

### Caveats

- In-sample backtest only, no out-of-sample validation
- Ignores transaction costs, slippage, and liquidity constraints
- Small sample size in some categories
- Not investment advice

---

## Running Locally

```bash
# Environment variables
export MONGODB_URI="your_mongodb_connection_string"

# Fetch data
python scripts/fetch_polymarket.py
python scripts/fetch_manifold.py
python scripts/resample.py

# Run analysis
python analysis/run_all.py

# Compute trade simulator data
python scripts/add_fade_pnl.py
python scripts/compute_distribution.py
python scripts/flag_recent_shocks.py

# Start live monitor (separate terminal)
python scripts/live_monitor.py

# Start dashboard (separate terminal)
cd dashboard && npm install && npm run dev
```

---

## Acknowledgments

- **Polymarket** — Prediction Markets track sponsor, primary data source
- **MongoDB Atlas** — Cloud database (MLH partner)
- **GoDaddy** — Domain registration (MLH partner)
- **K2-Think** — Market categorization and portfolio optimization
- **Claude** — AI shock analysis with web search
- **Vercel** — Dashboard hosting

---

Built at YHack Spring 2026. 151 commits in 24 hours.