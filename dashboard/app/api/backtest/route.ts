import { NextResponse } from "next/server";
import clientPromise from "@/lib/mongodb";
import { DUMMY_BACKTEST } from "@/lib/dummyData";

export const dynamic = "force-dynamic";

export async function GET() {
  const t0 = Date.now();
  try {
    const client = await clientPromise;
    console.log(`[/api/backtest] mongo connect: ${Date.now() - t0}ms`);

    const db = client.db("shocktest");
    const stats = await db
      .collection("shock_results")
      .findOne({ _id: "aggregate_stats" as unknown as import("mongodb").ObjectId });

    console.log(`[/api/backtest] query done: ${Date.now() - t0}ms`);
    if (!stats) {
      return NextResponse.json(DUMMY_BACKTEST);
    }

    return NextResponse.json({
      backtest: stats.backtest || null,
      distribution_1h: stats.distribution_1h || null,
      distribution_6h: stats.distribution_6h || null,
      distribution_24h: stats.distribution_24h || null,
    });
  } catch {
    // DB connection failed — serve dummy backtest
    return NextResponse.json(DUMMY_BACKTEST);
  }
}
