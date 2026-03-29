import { AggregateStats } from "@/lib/types";

interface StatsCardsProps {
  stats: AggregateStats;
  horizon?: "1h" | "6h" | "24h";
}

export default function StatsCards({ stats, horizon = "6h" }: StatsCardsProps) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const s = stats as any;
  const revRate = (s[`reversion_rate_${horizon}`] as number | null) ?? stats.reversion_rate_6h;
  const meanRev = (s[`mean_reversion_${horizon}`] as number | null) ?? stats.mean_reversion_6h;
  const sampleSize = (s[`sample_size_${horizon}`] as number) ?? stats.sample_size_6h;
  const winRate = (s.backtest?.[`win_rate_${horizon}`] as number | null) ?? stats.backtest?.win_rate_6h ?? null;

  const items = [
    {
      label: "Total Shocks",
      value: stats.total_shocks.toString(),
      delta: `across ${stats.total_markets} markets`,
      color: "text-text-primary",
    },
    {
      label: `${horizon} Reversion Rate`,
      value:
        revRate !== null
          ? `${(revRate * 100).toFixed(1)}%`
          : "—",
      delta:
        revRate !== null && revRate > 0.5
          ? "majority revert"
          : "below 50%",
      color:
        revRate !== null && revRate > 0.5
          ? "text-yes-text"
          : "text-text-primary",
    },
    {
      label: "Mean Reversion",
      value:
        meanRev !== null
          ? `${(meanRev * 100).toFixed(1)}pp`
          : "—",
      delta: `avg magnitude at ${horizon}`,
      color: "text-text-primary",
    },
    {
      label: "Sample Size",
      value: sampleSize.toString(),
      delta: `${sampleSize} valid at ${horizon}`,
      color: "text-text-primary",
    },
    {
      label: "Win Rate",
      value:
        winRate != null
          ? `${(winRate * 100).toFixed(0)}%`
          : "—",
      delta: `fade strategy ${horizon}`,
      color:
        winRate != null && winRate > 0.5
          ? "text-yes-text"
          : "text-text-primary",
    },
  ];

  return (
    <div className="flex overflow-x-auto border-b border-border">
      {items.map((item, i) => (
        <div
          key={item.label}
          className={`flex-1 min-w-[120px] px-4 py-3 ${i < items.length - 1 ? "border-r border-border" : ""}`}
        >
          <p className="text-[10px] font-medium uppercase tracking-wider text-text-muted">
            {item.label}
          </p>
          <p className={`mt-1 font-mono text-base font-medium ${item.color}`}>
            {item.value}
          </p>
          <p className="mt-0.5 text-[10px] text-text-muted">{item.delta}</p>
        </div>
      ))}
    </div>
  );
}
