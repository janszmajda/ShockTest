import { NextResponse } from "next/server";
import clientPromise from "@/lib/mongodb";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const client = await clientPromise;
    const db = client.db("shocktest");

    const [stats, liveMarketCount] = await Promise.all([
      db
        .collection("shock_results")
        .findOne({ _id: "aggregate_stats" as unknown as import("mongodb").ObjectId }),
      db.collection("market_series").countDocuments(),
    ]);

    const fallback = {
      total_shocks: 0, total_markets: 0,
      reversion_rate_1h: null, reversion_rate_6h: null, reversion_rate_24h: null,
      mean_reversion_6h: null, sample_size_6h: 0,
    };
    const result = stats || fallback;
    // Use live count from market_series (actual tracked markets)
    result.total_markets = liveMarketCount;
    return NextResponse.json(result, {
      headers: { "Cache-Control": "public, s-maxage=30, stale-while-revalidate=60" },
    });
  } catch {
    return NextResponse.json(
      { error: "Failed to fetch stats" },
      { status: 500 },
    );
  }
}
