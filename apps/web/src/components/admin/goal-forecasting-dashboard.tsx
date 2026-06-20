"use client";

import { useQuery } from "@tanstack/react-query";

import { adminForecastingApi } from "@/lib/api";
import type { ForecastAdminResponse } from "@/lib/types/api";
import { formatPercent, formatScore } from "@/lib/utils/format";
import { useAuthStore } from "@/stores";

function KpiTile({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="card">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}

export function GoalForecastingDashboard() {
  const token = useAuthStore((state) => state.accessToken);
  const dashboardQuery = useQuery({
    queryKey: ["admin", "forecasting"],
    queryFn: () => adminForecastingApi.dashboard(token!),
    enabled: Boolean(token),
    refetchInterval: 30_000,
  });

  const handleExport = async () => {
    if (!token) return;
    const csv = await adminForecastingApi.exportCsv(token);
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "goal_forecasting.csv";
    anchor.click();
    URL.revokeObjectURL(url);
  };

  if (dashboardQuery.isLoading) {
    return <p className="text-sm text-slate-600">Loading forecasting analytics…</p>;
  }

  const data: ForecastAdminResponse | undefined = dashboardQuery.data;

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <button type="button" className="btn-secondary" onClick={() => void handleExport()}>
          Export CSV
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiTile label="Total forecasts" value={data?.total_forecasts ?? 0} />
        <KpiTile label="Generated (30d)" value={data?.forecasts_last_30_days ?? 0} />
        <KpiTile
          label="Average probability"
          value={formatPercent(data?.average_probability ?? 0)}
        />
        <KpiTile
          label="On-track rate"
          value={formatPercent((data?.on_track_rate ?? 0) * 100)}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card">
          <h2 className="text-lg font-semibold text-slate-900">Scenario usage</h2>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {(data?.scenario_usage ?? []).map((item) => (
              <li key={item.scenario_type} className="flex justify-between gap-4">
                <span>{item.scenario_type}</span>
                <span className="font-medium">{item.count}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="card">
          <h2 className="text-lg font-semibold text-slate-900">Forecast events</h2>
          <p className="mt-1 text-sm text-slate-600">
            Average projected gain: {formatScore(data?.average_projected_gain ?? 0)}
          </p>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {(data?.event_counts ?? []).map((item) => (
              <li key={item.event_type} className="flex justify-between gap-4">
                <span>{item.event_type}</span>
                <span className="font-medium">{item.count}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
