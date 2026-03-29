"use client";

import { useState } from "react";
import Link from "next/link";
import { Shock } from "@/lib/types";

interface LiveAlertBannerProps {
  alerts: Shock[];
}

const PAGE_SIZE = 3;

export default function LiveAlertBanner({ alerts }: LiveAlertBannerProps) {
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);

  if (alerts.length === 0) return null;

  const visible = alerts.slice(0, visibleCount);
  const hasMore = visibleCount < alerts.length;

  return (
    <div className="space-y-2">
      {visible.map((alert) => (
        <div
          key={alert._id}
          className="rounded-lg border border-border bg-no-dim px-4 py-3"
        >
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="inline-flex animate-pulse items-center rounded-full bg-no-dim px-2 py-0.5 text-xs font-bold text-no-text">
                  LIVE
                </span>
                <span className="text-sm font-semibold text-text-primary">
                  SHOCK DETECTED
                  {alert.hours_ago != null
                    ? alert.hours_ago < 1
                      ? ` ${Math.max(1, Math.round(alert.hours_ago * 60))}m ago`
                      : ` ${Math.round(alert.hours_ago)}h ago`
                    : ""}
                </span>
              </div>
              <p className="mt-1 truncate text-sm text-text-secondary">
                &ldquo;{alert.question}&rdquo;{" "}
                <span className="font-medium text-text-primary">
                  {(alert.p_before * 100).toFixed(0)}% &rarr;{" "}
                  {(alert.p_after * 100).toFixed(0)}%
                </span>{" "}
                <span
                  className={`font-semibold ${alert.delta > 0 ? "text-yes-text" : "text-no-text"}`}
                >
                  ({alert.delta > 0 ? "+" : ""}
                  {(alert.delta * 100).toFixed(0)}pp)
                </span>
              </p>
              {alert.ai_analysis && (
                <p className="mt-1 text-xs text-accent">
                  AI: {alert.ai_analysis.likely_cause}
                </p>
              )}
              {alert.historical_win_rate != null &&
                alert.historical_avg_pnl != null && (
                  <p className="mt-0.5 text-xs text-text-muted">
                    Historical edge:{" "}
                    {(alert.historical_win_rate * 100).toFixed(0)}% win rate |
                    Avg return: ${alert.historical_avg_pnl.toFixed(4)}/$1
                  </p>
                )}
            </div>
            <Link
              href={`/shock/${alert._id}`}
              className="shrink-0 rounded-md bg-accent-dim px-3 py-1.5 text-xs font-medium text-accent hover:bg-surface-3"
            >
              Analyze &rarr;
            </Link>
          </div>
        </div>
      ))}
      {hasMore && (
        <button
          onClick={() => setVisibleCount((prev) => prev + PAGE_SIZE)}
          className="w-full rounded-lg border border-border bg-surface-1 py-2 text-xs font-medium text-text-secondary transition-all hover:bg-surface-2 hover:text-text-primary"
        >
          Show {PAGE_SIZE} more &middot; {alerts.length - visibleCount} remaining
        </button>
      )}
    </div>
  );
}
