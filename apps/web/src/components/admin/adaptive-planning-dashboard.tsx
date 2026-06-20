"use client";

import { useQuery } from "@tanstack/react-query";

import { adminPlanningApi } from "@/lib/api";
import type { PlanningAdminResponse } from "@/lib/types/api";
import { useAuthStore } from "@/stores";

function KpiTile({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="card">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}

export function AdaptivePlanningDashboard() {
  const token = useAuthStore((state) => state.accessToken);
  const dashboardQuery = useQuery({
    queryKey: ["admin", "planning"],
    queryFn: () => adminPlanningApi.dashboard(token!),
    enabled: Boolean(token),
    refetchInterval: 30_000,
  });

  const handleExport = async () => {
    if (!token) return;
    const csv = await adminPlanningApi.exportCsv(token);
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "adaptive_planning.csv";
    anchor.click();
    URL.revokeObjectURL(url);
  };

  if (dashboardQuery.isLoading) {
    return <p className="text-sm text-slate-600">Loading planning analytics…</p>;
  }

  const data: PlanningAdminResponse | undefined = dashboardQuery.data;

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <button type="button" className="btn-secondary" onClick={() => void handleExport()}>
          Export CSV
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiTile label="Total plans" value={data?.total_plans ?? 0} />
        <KpiTile label="Active plans" value={data?.active_plans ?? 0} />
        <KpiTile label="Generated (30d)" value={data?.plans_generated_last_30_days ?? 0} />
        <KpiTile
          label="Completion rate"
          value={`${((data?.average_completion_rate ?? 0) * 100).toFixed(1)}%`}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card">
          <h2 className="text-lg font-semibold text-slate-900">Top scheduled concepts</h2>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {(data?.top_scheduled_concepts ?? []).map((item) => (
              <li key={item.concept_id} className="flex justify-between gap-4">
                <span>{item.concept_id}</span>
                <span className="font-medium">{item.count}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="card">
          <h2 className="text-lg font-semibold text-slate-900">Planning events</h2>
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
