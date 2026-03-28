# ShockTest

**Do Prediction Markets Overreact? Find the Edge. Size the Trade.**

ShockTest is a trading signal and analysis tool for prediction markets. It detects large probability shocks ("overreactions") in Polymarket data, measures whether they systematically mean-revert, and gives traders an interactive simulator to size fade-the-shock positions with historical edge statistics. Built in 24 hours at YHack Spring 2026.

## The Hypothesis

Prediction markets are often described as efficient, but they can overreact to headlines, herd during high-attention moments, or temporarily misprice due to low liquidity.

We test a single, falsifiable question:

> **H0 (null):** After a large probability shock, future price changes are random.
> **H1 (alt):** After a large shock, probabilities systematically mean-revert.

We quantify which is more common, how strong the effect is, and whether it differs by market category. Then we turn that finding into a **trading tool**.

## Results

| Metric | Value |
|--------|-------|
| Markets Analyzed | 1,069 (1,009 Polymarket + 60 Manifold) |
| Total Shocks Detected | 1,337 |
| Live Signals (last 48h) | 198 |
| 1h Reversion Rate | 60.7% |
| 6h Reversion Rate | 59.9% |
| 24h Reversion Rate | 57.5% |
| Mean 6h Reversion | +3.45 pp |
| Fade Strategy Win Rate (6h) | 59.9% |
| Avg P&L per $1 Risked (6h) | +$0.035 |

**By category (6h):**
| Category | Win Rate | Avg P&L | Sample Size |
|----------|----------|---------|-------------|
| Politics | 64.7% | +$0.040 | 662 |
| Crypto | 53.5% | +$0.018 | 302 |
| Other | 53.9% | +$0.039 | 145 |
| Sports | 56.1% | +$0.048 | 90 |
| Science | 60.6% | +$0.030 | 33 |

**Finding:** Across 1,337 probability shocks detected in 1,069 Polymarket and Manifold markets, 59.9% showed mean reversion within 6 hours. A simulated fade-the-shock strategy produced a 60% win rate with +$0.035 expected return per dollar risked. Political markets showed the strongest edge at 64.7% win rate — suggesting political shocks are most often overreactions to headlines, while crypto markets (53.5%) revert less reliably.

## How to Use It

1. Browse detected shocks in the table — filter by category, adjust the shock threshold
2. Look for LIVE signals — shocks from the last 48 hours that are still tradeable
3. Click a shock to see the full probability chart with the shock highlighted
4. Use the Trade Simulator to input a position size and see expected P&L, win rate, and the historical distribution of outcomes
5. Adjust the time horizon (1h/6h/24h) to see how the edge changes over time

## What We Built

### Shock Detection Engine
Scans 1,069 markets for large, fast probability moves using a configurable threshold. Users can dynamically adjust the shock threshold and time horizon.

### Post-Shock Analysis & Backtest
Measures what happens at 1h, 6h, and 24h after each shock. Computes reversion rates, fade strategy P&L, win rates, and expected value — overall and by market category.

### Interactive Trade Simulator
For any detected shock, input a position size and horizon to see:
- Expected P&L based on historical reversion data
- Win rate and best/worst case scenarios
- Payoff distribution chart with historical outcomes

### Live Signal Detection
Shocks from the last 48 hours are flagged as potentially actionable — transforming the tool from retrospective research into a forward-looking trading signal desk.

### Interactive Dashboard
Next.js web app with configurable controls (threshold slider, horizon picker, category filter), sortable shocks table, per-shock detail pages with probability charts, and aggregate statistics.

## Methodology

### Shock Detection

```
|p(t2) - p(t1)| >= theta    where t2 - t1 <= T
```

- **theta** = 0.08 (8 percentage point move) — adjustable via slider from 0.03 to 0.20
- **T** = 1 hour

### Fade Strategy Backtest

For each shock, simulate taking the opposite position:

```
Entry:  Buy opposite direction at p(t2)
Exit:   Close at p(t2 + h) for horizon h
P&L:    position_size * reversion
```

**Caveats** (displayed in the tool):
- In-sample backtest only — no out-of-sample validation
- Ignores transaction costs, slippage, and liquidity constraints
- Not investment advice — exploratory analysis tool

## Tech Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| Data Fetching | `requests` + Polymarket Gamma API + CLOB API | Fetch market listings and price history |
| Supplemental Data | Manifold Markets API | Additional market diversity |
| Storage | **MongoDB Atlas** (free M0) | Cloud database for time series, shocks, backtest results |
| Analysis | `pandas` + `numpy` | Shock detection, post-shock stats, fade strategy backtest |
| Categorization | **Google Gemini 2.5 Flash** | Auto-classify markets by category from titles |
| Frontend | **Next.js 14** + TypeScript + Tailwind CSS + Recharts | Interactive dashboard with trade simulator |
| Deployment | **Vercel** | Production hosting |
| Domain | **GoDaddy** (via MLH) | Custom domain |

## Architecture

```
Polymarket API ──┐
                 ├──> Python scripts ──> MongoDB Atlas ──> Next.js API routes ──> Dashboard
Manifold API ────┘     (scripts/)         (shocktest)      (dashboard/api/)    + Trade Simulator
                       + analysis/
```

- **Person 1** (`scripts/`): Data pipeline — fetch, clean, normalize, compute backtest data
- **Person 2** (`analysis/`): Shock detection, post-shock analysis, Gemini categorization
- **Person 3** (`dashboard/`): Interactive frontend with trade simulator and configurable controls

## Running Locally

```bash
# Set environment variables
export MONGODB_URI="your_mongodb_connection_string"
export GEMINI_API_KEY="your_gemini_key"  # Person 2 only

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

# Start dashboard
cd dashboard && npm install && npm run dev
```

## Team

Built at YHack Spring 2026 by a team of three.

## Acknowledgments

- **Polymarket** — Prediction Markets track sponsor, primary data source
- **MongoDB Atlas** — Cloud database
- **Google Gemini** — Market categorization
- **Vercel** — Dashboard hosting
- **GoDaddy** — Domain registration via MLH
