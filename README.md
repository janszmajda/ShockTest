# ShockTest

**Prediction markets overreact. We proved it. Now you can trade it.**

ShockTest is a live trading signal system for Polymarket. It detects sudden probability shocks, uses AI to analyze whether they're overreactions, and gives traders interactive tools to size and execute fade positions backed by real statistical data. Built in 24 hours at YHack Spring 2026.

**Live at [shocktest.us](https://shocktest.us)**

---

## The Finding

**Polymarket markets partially mean-revert after large probability shocks.** 58.4% of shocks reverted toward the pre-shock price over the following 6 hours (95% CI: 54.6%–62.2%, cluster-robust z = +4.37, n = 635 shocks across 74 markets). Mean reversion was +4.06 pp. All confidence intervals and z-stats below are clustered by market — shocks on the same market are autocorrelated, so treating every shock as independent (the naive approach) inflates significance by up to 3×.

**Headline numbers (6h horizon, cluster-robust):**

| Source | Shocks w/ 6h outcome | Markets (G) | Win Rate | 95% CI | Mean Reversion | z |
|---|---|---|---|---|---|---|
| Polymarket | 635 | 74 | 58.4% | [54.6%, 62.2%] | +4.06 pp | +4.37 |
| Manifold | 664 | 25 | 61.3% | [52.8%, 69.8%] | +2.86 pp | +2.62 |
| Combined | 1,299 | 99 | 59.9% | [55.2%, 64.6%] | +3.45 pp | +4.12 |

Under the naive (no clustering) assumption, the combined z is +7.13 — but that assumes 1,299 independent observations when the data actually comes from only 99 markets. Use the clustered numbers for any claim you want to defend.

**Data coverage:** we've detected 4,926 shocks across 909 markets total. Only 1,299 of those have 6-hour post-shock data available — Polymarket shocks have 6h completion at 14.9% (635/4,254) because our live feed only recently caught up, while Manifold is 98.8% complete (664/672). Expect the Polymarket sample (and effect-size estimates) to shift as more shocks age past their 6-hour window.

**By category (6h, cluster-robust, Polymarket + Manifold combined):**

| Category | Markets (G) | n | Win Rate | 95% CI | z | Robust? |
|----------|-------------|---|----------|--------|---|---------|
| Geopolitics | 16 | 351 | 70.7% | [62.1%, 79.2%] | +4.74 | YES |
| Sports | 18 | 87 | 57.5% | [46.2%, 68.7%] | +1.31 | no |
| Politics | 15 | 150 | 54.7% | [47.8%, 61.6%] | +1.32 | no |
| Crypto | 16 | 325 | 53.5% | [49.9%, 57.2%] | +1.89 | marginal |
| Elections | 7 | 173 | 60.7% | [48.3%, 73.1%] | +1.69 | marginal |
| Other | 13 | 88 | 52.3% | [41.4%, 63.1%] | +0.41 | no |

Finance, tech, and esports are omitted — each has fewer than 10 distinct markets in the 6h sample, so their category-level estimates are not trustworthy (e.g., finance's n=81 comes from only 3 markets).

**Geopolitics is the only category where the effect is clearly robust** after clustering. Crypto, politics, sports, and "other" look flat once we stop double-counting correlated shocks from the same market.

### Caveats you should read before trading

- **In-sample backtest only**, no out-of-sample validation.
- **Transaction costs, slippage, and Polymarket's order-book liquidity are not modeled.** A +4 pp average reversion does not mean +$0.04 per $1 in realized P&L after the spread.
- **Mechanical regression-to-the-mean is not controlled for.** Our shock detector fires at the bar where |Δp| crosses 8pp — this preferentially picks local peaks/troughs, so some of the observed reversion is a sampling artifact, not an exploitable inefficiency. We have not run a placebo control (random-timestamp reversion) to quantify this.
- **1-minute resampling with time-interpolation (limit 10)** is applied to sparse raw observations. This smoothing can introduce artificial autocorrelation; the clustered SEs partially but not fully account for it.
- Cluster-robust SEs assume clusters (markets) are independent of each other. Related markets (e.g. two different "Will X win the election?" contracts on the same event) likely violate this — effective significance may be somewhat lower still.

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