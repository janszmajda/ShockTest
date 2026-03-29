import { NextResponse } from "next/server";
import clientPromise from "@/lib/mongodb";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const t0 = Date.now();
  try {
    const { searchParams } = new URL(request.url);
    const marketId = searchParams.get("id");

    const client = await clientPromise;
    console.log(`[/api/markets${marketId ? `?id=${marketId}` : ""}] mongo connect: ${Date.now() - t0}ms`);

    const db = client.db("shocktest");

    const cacheHeaders = {
      "Cache-Control": "public, s-maxage=30, stale-while-revalidate=60",
    };

    if (marketId) {
      const market = await db
        .collection("market_series")
        .findOne({ market_id: marketId });
      console.log(`[/api/markets?id=${marketId}] query done: ${Date.now() - t0}ms`);
      return NextResponse.json(market, { headers: cacheHeaders });
    }

    const markets = await db
      .collection("market_series")
      .find({})
      .project({ market_id: 1, source: 1, question: 1, category: 1, volume: 1, close_time: 1, token_id: 1 })
      .toArray();

    console.log(`[/api/markets] query done: ${Date.now() - t0}ms (${markets.length} docs)`);
    return NextResponse.json(markets, { headers: cacheHeaders });
  } catch {
    return NextResponse.json(
      { error: "Failed to fetch markets" },
      { status: 500 },
    );
  }
}
