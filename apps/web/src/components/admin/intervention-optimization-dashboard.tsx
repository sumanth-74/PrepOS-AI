"use client";

import { useQuery } from "@tanstack/react-query";

import { adminInterventionsApi } from "@/lib/api";
import type { InterventionAdminResponse } from "@/lib/types/api";
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

export function InterventionOptimizationDashboard() {
  const token = useAuthStore((state) => state.accessToken);
  const dashboardQuery = useQuery({
    queryKey: ["admin", "interventions"],
    queryFn: () => adminInterventionsApi.dashboard(token!),
    enabled: Boolean(token),
    refetchInterval: 30_000,
  });

  const handleExport = async () => {
    if (!token) return;
    const csv = await adminInterventionsApi.exportCsv(token);
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "mentor_interventions.csv";
    anchor.click();
    URL.revokeObjectURL(url);
  };

  if (dashboardQuery.isLoading) {
    return <p className="text-sm text-slate-600">Loading intervention analytics…</p>;
  }

  const data: InterventionAdminResponse | undefined = dashboardQuery.data;

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <button type="button" className="btn-secondary" onClick={() => void handleExport()}>
          Export CSV
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiTile label="Total interventions" value={data?.total_interventions ?? 0} />
        <KpiTile label="Last 30 days" value={data?.interventions_last_30_days ?? 0} />
        <KpiTile label="Average gain" value={`+${formatScore(data?.average_gain ?? 0)}`} />
        <KpiTile
          label="Mentor success rate"
          value={formatPercent((data?.mentor_success_rate ?? 0) * 100)}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card">
          <h2 className="text-lg font-semibold text-slate-900">Top interventions</h2>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {(data?.top_interventions ?? []).map((item) => (
              <li key={item.intervention_type} className="flex justify-between gap-4">
                <span>{item.intervention_type}</span>
                <span className="font-medium">{item.count}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="card">
          <h2 className="text-lg font-semibold text-slate-900">Least effective</h2>
          <p className="mt-1 text-sm text-slate-600">
            Average effectiveness: {formatScore(data?.average_effectiveness ?? 0)}%
          </p>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {(data?.least_effective_interventions ?? []).map((item) => (
              <li key={item.intervention_type} className="flex justify-between gap-4">
                <span>{item.intervention_type}</span>
                <span className="font-medium">{formatScore(item.average_effectiveness)}%</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
