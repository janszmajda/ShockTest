# Person 3 (Frontend) — Full Playbook

Everything you need in one place. Follow this hour by hour.

---

## Your Role

You own **everything in `dashboard/`**. You build the Next.js frontend that reads
data from MongoDB and displays it as a polished analytics dashboard.

**Tech stack:** Next.js 16 (App Router), TypeScript, Tailwind CSS, Recharts, MongoDB

**Commit prefix:** `P3:`

---

## What You're Waiting On (from teammates)

| When       | From     | What you get                                          |
|------------|----------|-------------------------------------------------------|
| Minute 20  | Person 1 | MongoDB connection string (put in `.env.local`)       |
| Hour 6     | Person 2 | `shock_events` collection populated — `/api/shocks` works |
| Hour 14    | Person 2 | `shock_results` + categories populated — `/api/stats` works |
| Hour 18    | Person 2 | Findings paragraph text to display on dashboard       |

**You do NOT need to wait for any of this to start building.** Use dummy data
until real data flows in, then swap.

---

## HOUR 0–2 — Scaffold + API Routes + Dummy Data

### Minute 0–30 — Scaffold the App

```bash
npx create-next-app@latest dashboard --typescript --tailwind --app --eslint
cd dashboard
npm install recharts mongodb
```

Target structure:
```
dashboard/
├── app/
│   ├── layout.tsx
│   ├── page.tsx                    # Main dashboard
│   ├── globals.css
│   ├── api/
│   │   ├── shocks/route.ts        # GET /api/shocks
│   │   ├── markets/route.ts       # GET /api/markets?id=X
│   │   └── stats/route.ts         # GET /api/stats
│   └── shock/[id]/
│       └── page.tsx               # Per-shock detail page
├── components/
│   ├── Header.tsx
│   ├── StatsCards.tsx
│   ├── FindingsBlock.tsx
│   ├── ShocksTable.tsx
│   ├── PriceChart.tsx
│   ├── Histogram.tsx
│   ├── CategoryBreakdown.tsx
│   ├── LoadingSpinner.tsx
│   └── Footer.tsx
└── lib/
    ├── mongodb.ts                  # DB connection singleton
    ├── types.ts                    # Shared TypeScript interfaces
    └── dummyData.ts                # Fake data for building UI
```

✅ Done when: `npm run dev` works and shows the default Next.js page.

---

### Minute 30–60 — MongoDB Connection + API Routes

**1. Create `.env.local`** (🔗 get the connection string from Person 1):
```
MONGODB_URI=mongodb+srv://shocktest-admin:<password>@shocktest.xxxxx.mongodb.net/shocktest?retryWrites=true&w=majority
```

**2. Create `lib/mongodb.ts`** — a singleton that reuses the DB connection:
```typescript
import { MongoClient } from 'mongodb';

if (!process.env.MONGODB_URI) {
  throw new Error('Please add MONGODB_URI to .env.local');
}

const uri = process.env.MONGODB_URI;
const options = {};

let client: MongoClient;
let clientPromise: Promise<MongoClient>;

if (process.env.NODE_ENV === 'development') {
  let globalWithMongo = global as typeof globalThis & {
    _mongoClientPromise?: Promise<MongoClient>;
  };
  if (!globalWithMongo._mongoClientPromise) {
    client = new MongoClient(uri, options);
    globalWithMongo._mongoClientPromise = client.connect();
  }
  clientPromise = globalWithMongo._mongoClientPromise;
} else {
  client = new MongoClient(uri, options);
  clientPromise = client.connect();
}

export default clientPromise;
```

**3. Create `lib/types.ts`** — these match the MongoDB schemas exactly:
```typescript
export interface PricePoint {
  t: number;    // unix timestamp (seconds)
  p: number;    // probability 0-1
}

export interface Market {
  _id: string;
  market_id: string;
  source: "polymarket" | "manifold";
  question: string;
  token_id: string;
  volume: number;
  category: string | null;
  series?: PricePoint[];
}

export interface Shock {
  _id: string;
  market_id: string;
  source: string;
  question: string;
  category: string | null;
  t1: string;              // ISO timestamp
  t2: string;              // ISO timestamp
  p_before: number;
  p_after: number;
  delta: number;           // signed
  abs_delta: number;       // absolute value
  post_move_1h: number | null;
  post_move_6h: number | null;
  post_move_24h: number | null;
  reversion_1h: number | null;
  reversion_6h: number | null;
  reversion_24h: number | null;
}

export interface CategoryStats {
  count: number;
  reversion_rate_6h: number | null;
  mean_reversion_6h: number | null;
  sample_size_6h: number;
}

export interface AggregateStats {
  _id: string;
  total_shocks: number;
  total_markets: number;
  reversion_rate_1h: number | null;
  reversion_rate_6h: number | null;
  reversion_rate_24h: number | null;
  mean_reversion_1h: number | null;
  mean_reversion_6h: number | null;
  mean_reversion_24h: number | null;
  std_reversion_6h: number | null;
  sample_size_1h: number;
  sample_size_6h: number;
  sample_size_24h: number;
  by_category: Record<string, CategoryStats>;
}
```

**4. Create 3 API routes** — each reads from MongoDB:

`app/api/shocks/route.ts` — returns all shocks sorted by size:
```typescript
import { NextResponse } from 'next/server';
import clientPromise from '@/lib/mongodb';

export async function GET() {
  try {
    const client = await clientPromise;
    const db = client.db('shocktest');

    const shocks = await db
      .collection('shock_events')
      .find({})
      .sort({ delta: -1 })
      .limit(100)
      .toArray();

    return NextResponse.json(shocks);
  } catch (error) {
    return NextResponse.json({ error: 'Failed to fetch shocks' }, { status: 500 });
  }
}
```

`app/api/stats/route.ts` — returns the single aggregate stats document:
```typescript
import { NextResponse } from 'next/server';
import clientPromise from '@/lib/mongodb';

export async function GET() {
  try {
    const client = await clientPromise;
    const db = client.db('shocktest');

    const stats = await db
      .collection('shock_results')
      .findOne({ _id: 'aggregate_stats' });

    return NextResponse.json(stats || {
      total_shocks: 0,
      reversion_rate_1h: null,
      reversion_rate_6h: null,
      reversion_rate_24h: null,
      mean_reversion_6h: null,
      sample_size: 0
    });
  } catch (error) {
    return NextResponse.json({ error: 'Failed to fetch stats' }, { status: 500 });
  }
}
```

`app/api/markets/route.ts` — returns market list or single market with series:
```typescript
import { NextResponse } from 'next/server';
import clientPromise from '@/lib/mongodb';

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const marketId = searchParams.get('id');

    const client = await clientPromise;
    const db = client.db('shocktest');

    if (marketId) {
      // Return single market with full time series
      const market = await db
        .collection('market_series')
        .findOne({ market_id: marketId });
      return NextResponse.json(market);
    }

    // Return all markets (without full series for list view)
    const markets = await db
      .collection('market_series')
      .find({})
      .project({ series: 0 }) // exclude the big array for list queries
      .toArray();

    return NextResponse.json(markets);
  } catch (error) {
    return NextResponse.json({ error: 'Failed to fetch markets' }, { status: 500 });
  }
}
```

✅ Done when: API routes exist (they'll return errors until MongoDB is connected — that's fine).

---

### Minute 60–90 — Deploy Skeleton to Vercel

```bash
npm install -g vercel
vercel login
vercel --prod
```

- Vercel will ask about settings — accept defaults
- Add environment variable in Vercel dashboard: Settings → Environment Variables → add `MONGODB_URI`

✅ Done when: you have a live URL like `shocktest-dashboard.vercel.app` that loads (even if blank).

---

### Minute 90–120 — Build with Dummy Data

Since Person 1 is still populating MongoDB, build components using hardcoded dummy data that matches the expected schema:

```typescript
// lib/dummyData.ts
export const DUMMY_SHOCKS = [
  {
    market_id: "will-trump-win-2028",
    source: "polymarket",
    question: "Will Trump win the 2028 presidential election?",
    category: "politics",
    t1: "2026-03-15T14:00:00Z",
    t2: "2026-03-15T14:30:00Z",
    p_before: 0.42,
    p_after: 0.57,
    delta: 0.15,
    post_move_1h: -0.08,
    post_move_6h: -0.11,
    post_move_24h: -0.09,
    reversion_1h: 0.08,
    reversion_6h: 0.11,
    reversion_24h: 0.09,
  },
  {
    market_id: "btc-above-100k-june",
    source: "polymarket",
    question: "Will Bitcoin be above $100k on June 30?",
    category: "crypto",
    t1: "2026-03-20T09:00:00Z",
    t2: "2026-03-20T09:45:00Z",
    p_before: 0.65,
    p_after: 0.52,
    delta: -0.13,
    post_move_1h: 0.04,
    post_move_6h: 0.07,
    post_move_24h: 0.10,
    reversion_1h: 0.04,
    reversion_6h: 0.07,
    reversion_24h: 0.10,
  },
  // Add 5-8 more dummy shocks with varied categories, directions, magnitudes
];

export const DUMMY_STATS = {
  total_shocks: 47,
  reversion_rate_1h: 0.62,
  reversion_rate_6h: 0.68,
  reversion_rate_24h: 0.55,
  mean_reversion_6h: 0.034,
  std_reversion_6h: 0.021,
  sample_size: 47,
  by_category: {
    politics: { count: 18, reversion_rate_6h: 0.72 },
    crypto: { count: 15, reversion_rate_6h: 0.60 },
    sports: { count: 8, reversion_rate_6h: 0.63 },
    other: { count: 6, reversion_rate_6h: 0.67 },
  }
};

export const DUMMY_PRICE_SERIES = [
  // 100+ points simulating 2-min interval data around a shock
  // timestamps as ISO strings, prices as floats 0-1
  // Show: stable → sudden jump → partial reversion
];
```

- Use this dummy data to build all UI components before real data is ready
- When real data flows in during Hours 16–20, just remove the dummy imports and fetch from your API routes instead

✅ Done when: `npm run dev` serves a page at `localhost:3000` that shows dummy data.

---

## HOUR 2–6 — Core Components (Table + Chart)

**Goal:** Build the core UI components using dummy data. All components should be swappable to real data later by just changing the data source from dummy imports to fetch calls.

### Hour 2–4 — ShocksTable Component

```typescript
// components/ShocksTable.tsx
'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';

interface Shock {
  market_id: string;
  question: string;
  source: string;
  category: string | null;
  t1: string;
  t2: string;
  p_before: number;
  p_after: number;
  delta: number;
  abs_delta: number;
  reversion_6h?: number;
}

interface ShocksTableProps {
  shocks: Shock[];
}

export default function ShocksTable({ shocks }: ShocksTableProps) {
  const [sortBy, setSortBy] = useState<'abs_delta' | 't2' | 'category'>('abs_delta');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');

  const categories = useMemo(() => {
    const cats = new Set(shocks.map(s => s.category).filter(Boolean));
    return ['all', ...Array.from(cats)];
  }, [shocks]);

  const sorted = useMemo(() => {
    let filtered = categoryFilter === 'all'
      ? shocks
      : shocks.filter(s => s.category === categoryFilter);

    return filtered.sort((a, b) => {
      const mul = sortDir === 'desc' ? -1 : 1;
      if (sortBy === 'abs_delta') return mul * (a.abs_delta - b.abs_delta);
      if (sortBy === 't2') return mul * (new Date(a.t2).getTime() - new Date(b.t2).getTime());
      return 0;
    });
  }, [shocks, sortBy, sortDir, categoryFilter]);

  // Build this out with Claude Code — sortable headers, category filter dropdown,
  // color-coded delta values (green for positive, red for negative),
  // clickable rows that link to /shock/[market_id]

  return (
    <div>
      {/* Category filter buttons */}
      {/* Table with sortable headers */}
      {/* Each row links to /shock/[market_id] for detail view */}
    </div>
  );
}
```

### Hour 4–6 — PriceChart Component

```typescript
// components/PriceChart.tsx
'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ReferenceArea, ResponsiveContainer } from 'recharts';

interface PricePoint {
  t: string;  // ISO timestamp
  p: number;  // probability 0-1
}

interface PriceChartProps {
  series: PricePoint[];
  shockT1?: string;  // shock window start
  shockT2?: string;  // shock window end
}

export default function PriceChart({ series, shockT1, shockT2 }: PriceChartProps) {
  const data = series.map(point => ({
    time: new Date(point.t).toLocaleString(),
    timestamp: new Date(point.t).getTime(),
    probability: point.p * 100,  // display as percentage
  }));

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="time" tick={{ fontSize: 12 }} />
        <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
        <Tooltip formatter={(value: number) => [`${value.toFixed(1)}%`, 'Probability']} />
        <Line type="monotone" dataKey="probability" stroke="#2563eb" dot={false} strokeWidth={2} />

        {/* Highlight shock window */}
        {shockT1 && shockT2 && (
          <ReferenceArea
            x1={new Date(shockT1).toLocaleString()}
            x2={new Date(shockT2).toLocaleString()}
            fill="#ef4444"
            fillOpacity={0.15}
            label="Shock"
          />
        )}
      </LineChart>
    </ResponsiveContainer>
  );
}
```

- Build both components, test with dummy data at `localhost:3000`
- Have Claude Code polish the styling — use Tailwind for layout, spacing, colors

✅ Done when: shocks table renders with dummy data and is sortable; price chart renders a line with highlighted shock window.

---

## HOUR 6–10 — Detail Page + Histogram + Stats Cards

**Goal:** Build the per-shock detail page and start on the histogram component.

### Per-Shock Detail Page

```typescript
// app/shock/[id]/page.tsx
// This page shows:
// 1. Market question as title
// 2. Shock details (before/after price, delta, time window)
// 3. Full probability chart with shock window highlighted
// 4. Post-shock stats (1h/6h/24h reversion) if available

// Fetch market series from /api/markets?id={market_id}
// Fetch shock details from /api/shocks (filter by market_id)
// Render PriceChart component with the series data + shock window
```

Layout:
```
← Back to dashboard
Market Question Title
Source: polymarket · Category: politics · Shock: 42% → 57% (+15pp)
┌─────────────────────────────────────┐
│     Probability Over Time Chart     │
│     (shock window highlighted)      │
└─────────────────────────────────────┘
Post-Shock Outcomes:
  Horizon    Post Move    Reversion
  1 hour     -8.0pp       +8.0pp
  6 hours    -11.0pp      +11.0pp
  24 hours   -9.0pp       +9.0pp
```

### Histogram Component

```typescript
// components/Histogram.tsx
// Shows distribution of post-shock probability moves
// X-axis: reversion magnitude (negative = continuation, positive = reversion)
// Y-axis: count of shocks
// Use Recharts BarChart with bins

// Key design choices:
// - Color bars: green for reversion (positive), red for continuation (negative)
// - Add vertical reference line at x=0
// - Show mean reversion as a dashed vertical line
// - Label the axes clearly for demo
```

### Stats Cards Component

```typescript
// components/StatsCards.tsx
// 3-4 summary cards at top of dashboard:
// 1. "Total Shocks Detected" — large number
// 2. "6h Reversion Rate" — percentage with color coding (>50% = green)
// 3. "Mean Reversion Magnitude" — percentage points
// 4. "Markets Analyzed" — count
//
// Use a clean card grid with Tailwind
```

### FindingsBlock Component

1-2 sentence summary paragraph with real numbers plugged in, e.g.:
> "In a sample of 47 shocks across 83 prediction markets, 68% showed mean
> reversion within 6 hours, with an average magnitude of 3.4 percentage points.
> Political markets reverted at a higher rate (72%) than the overall average."

✅ Done when: detail page renders with dummy data, histogram shows dummy distribution, stats cards display.

---

## HOUR 10–16 — Layout + Category Breakdown + Start Wiring Real Data

**Goal:** Build the aggregate histogram and stats cards. Set up layout/navigation. Start connecting to real API routes as data becomes available.

### Hour 10–12 — Histogram + Stats Cards
- Build the histogram component showing distribution of post-shock moves
- Build stats cards showing headline numbers
- Wire both to dummy data initially

### Hour 12–14 — Layout and Navigation

Main page (`/`) should show:
```
Header: "ShockTest — Do Prediction Markets Overreact?"
Subtitle: "Analyzing mean reversion in Polymarket probability shocks"
├── Stats Cards row (4 cards)
├── Findings paragraph (1-2 sentences with real numbers, filled in later)
├── Shocks Table (sortable, filterable)
├── Aggregate Histogram
├── CategoryBreakdown (table)
└── Footer: "Powered by Polymarket · Data stored in MongoDB Atlas · Categories by Google Gemini"
```

Detail page (`/shock/[id]`) should show:
```
├── Back link to main page
├── Market question as title
├── Shock details (delta, time window, category)
├── Full price chart with shock highlight
└── Post-shock outcomes table (1h, 6h, 24h)
```

### CategoryBreakdown Component

Table showing reversion rate per market category:
```
Category    Shocks    6h Reversion Rate    Mean Reversion
politics    18        72%                  4.1pp
crypto      15        60%                  2.9pp
sports      8         63%                  3.2pp
other       6         67%                  3.5pp
```

### Hour 14–16 — Start Wiring Real Data

Check if Person 2's data is in MongoDB by hitting your API routes:
```bash
curl http://localhost:3000/api/shocks    # should return shock events
curl http://localhost:3000/api/stats     # should return aggregate stats
```

- If real data is available, start replacing dummy data imports with `fetch('/api/...')` calls
- If not yet available, keep using dummy data — you'll swap in Hours 16–20

✅ Done when: full page layout works with either dummy or real data, navigation between main page and detail pages works.

---

## HOUR 16–20 — Wire Real Data + Deploy

**Goal:** Wire all real data into the dashboard. Everything should show real numbers, not dummy data.

### Hour 16–18 — Replace Dummy Data with API Calls

Every component that uses `DUMMY_SHOCKS`, `DUMMY_STATS`, etc. should now fetch from your API routes:

```typescript
// Pattern for each component:
const [data, setData] = useState(null);
const [loading, setLoading] = useState(true);

useEffect(() => {
  fetch('/api/shocks')
    .then(res => res.json())
    .then(data => { setData(data); setLoading(false); })
    .catch(err => { console.error(err); setLoading(false); });
}, []);
```

### Hour 18–20 — Polish and Deploy

- Add the findings paragraph from Person 2 to the top of the dashboard
- Add "Powered by Polymarket" logo/text in footer
- Add data source badges (Polymarket, MongoDB, Gemini)
- Deploy to Vercel:
```bash
vercel --prod
```

- Point GoDaddy domain to Vercel:
  - In Vercel: Settings → Domains → add `shocktest.xyz`
  - In GoDaddy: DNS → add CNAME record pointing to `cname.vercel-dns.com`
  - Or use Vercel's nameservers (Vercel will show instructions)

✅ Done when: `shocktest.xyz` loads the dashboard with **real data** from MongoDB.

---

## HOUR 20–24 — Polish for Best UI/UX + Submit

### Hour 20–22 — UI/UX Polish (aim for Best UI/UX prize)

Use Claude Code to:
- Apply a consistent color palette via Tailwind config (not default blue — pick something distinctive)
- Ensure chart labels are readable (font size, contrast, axis labels)
- Add smooth transitions/animations on page load (fade-in for cards, etc.)
- Make layout responsive (test at mobile width)
- Add visual hierarchy — the headline finding should be the most prominent element
- Clean up any rough edges (loading states, error states, empty states)

### Hour 22–23 — Film Most Viral Post Reel

Screen-record a 30-second walkthrough:
1. Show a dramatic shock in the table
2. Click into it — show the price chart spiking and reverting
3. Show the aggregate stats
4. End with the URL: `shocktest.xyz`

Post to Instagram as a reel, tag **@yhack.yale**.

### Hour 23–24 — Final Deploy + Devpost Submission

```bash
# Final production deploy
vercel --prod

# Verify everything works
curl https://shocktest.xyz
curl https://shocktest.xyz/api/shocks
curl https://shocktest.xyz/api/stats
```

Submit on Devpost (`yhack-2026.devpost.com`):
- Project name: **ShockTest**
- Tagline: "Do Prediction Markets Overreact?"
- Select tracks: Prediction Markets, Most Creative Hack, Best UI/UX
- Add demo URL: `shocktest.xyz`
- Add GitHub repo link
- Add demo video (can reuse the reel or record a longer walkthrough)
- Paste the description Person 2 wrote

---

## Quick Reference — Commands

```bash
# Dev server
npm run dev                  # localhost:3000

# Check your code before pushing
npx eslint .                 # lint
npx tsc --noEmit             # typecheck
npm run build                # full build (catches everything)

# Deploy
vercel --prod

# Test API routes (while dev server is running)
curl http://localhost:3000/api/shocks
curl http://localhost:3000/api/stats
curl http://localhost:3000/api/markets
```

---

## Quick Reference — File Ownership

Everything in `dashboard/` is yours. Don't touch `scripts/` or `analysis/`.

| File                              | What it does                                |
|-----------------------------------|---------------------------------------------|
| `lib/types.ts`                    | TypeScript interfaces for all data shapes   |
| `lib/mongodb.ts`                  | Database connection (shared by API routes)   |
| `lib/dummyData.ts`                | Fake data for building UI before real data   |
| `app/api/shocks/route.ts`        | Returns shock events from MongoDB            |
| `app/api/markets/route.ts`       | Returns market list or single market         |
| `app/api/stats/route.ts`         | Returns aggregate statistics                 |
| `app/page.tsx`                    | Main dashboard page                          |
| `app/shock/[id]/page.tsx`        | Per-shock detail page                        |
| `components/Header.tsx`           | Title bar                                    |
| `components/StatsCards.tsx`       | 4 summary metric cards                       |
| `components/FindingsBlock.tsx`    | Summary paragraph with real numbers          |
| `components/ShocksTable.tsx`      | Sortable, filterable shocks table            |
| `components/PriceChart.tsx`       | Probability line chart with shock highlight  |
| `components/Histogram.tsx`        | Distribution of post-shock reversion values  |
| `components/CategoryBreakdown.tsx`| Reversion rate per category                  |
| `components/LoadingSpinner.tsx`   | Shared loading spinner                       |
| `components/Footer.tsx`           | Attribution line                             |
