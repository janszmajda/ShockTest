import { NextResponse } from "next/server";
import clientPromise from "@/lib/mongodb";

export const dynamic = "force-dynamic";

export async function GET() {
  const t0 = Date.now();
  try {
    const client = await clientPromise;
    console.log(`[/api/shocks] mongo connect: ${Date.now() - t0}ms`);

    const db = client.db("shocktest");
    const raw = await db
      .collection("shock_events")
      .find({}, {
        projection: {
          market_id: 1, source: 1, question: 1, category: 1,
          t1: 1, t2: 1, p_before: 1, p_after: 1, delta: 1, abs_delta: 1,
          reversion_1h: 1, reversion_6h: 1, reversion_24h: 1,
          is_recent: 1, is_live_alert: 1, hours_ago: 1, detected_at: 1,
          ai_analysis: 1, fade_pnl_1h: 1, fade_pnl_6h: 1, fade_pnl_24h: 1,
        },
      })
      .sort({ abs_delta: -1 })
      .toArray();

    console.log(`[/api/shocks] query done: ${Date.now() - t0}ms (${raw.length} docs)`);

    // Strip live/recent flags from resolved markets (price at 0% or 100%)
    const shocks = raw.map((s) => {
      if (s.p_after <= 0.01 || s.p_after >= 0.99) {
        return { ...s, is_live_alert: false, is_recent: false };
      }
      return s;
    });

    return NextResponse.json(shocks, {
      headers: { "Cache-Control": "public, s-maxage=30, stale-while-revalidate=60" },
    });
  } catch (err) {
    console.error(`[/api/shocks] error at ${Date.now() - t0}ms:`, err);
    return NextResponse.json(
      { error: "Failed to fetch shocks" },
      { status: 500 },
    );
  }
}
