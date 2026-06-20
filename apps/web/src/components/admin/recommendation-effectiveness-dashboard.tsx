"use client";

import { useQuery } from "@tanstack/react-query";

import { adminRecommendationEffectivenessApi } from "@/lib/api";
import type { RecommendationEffectivenessAdminResponse } from "@/lib/types/api";
import { useAuthStore } from "@/stores";

function KpiTile({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="card">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}

function pct(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

export function RecommendationEffectivenessDashboard() {
  const token = useAuthStore((state) => state.accessToken);
  const dashboardQuery = useQuery({
    queryKey: ["admin", "recommendation-effectiveness"],
    queryFn: () => adminRecommendationEffectivenessApi.dashboard(token!, 30),
    enabled: Boolean(token),
    refetchInterval: 30_000,
  });

  const handleExport = async () => {
    if (!token) return;
    const csv = await adminRecommendationEffectivenessApi.exportCsv(token, 30);
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "recommendation_effectiveness.csv";
    anchor.click();
    URL.revokeObjectURL(url);
  };

  if (dashboardQuery.isLoading) {
    return <p className="text-sm text-slate-600">Loading recommendation effectiveness…</p>;
  }

  const data: RecommendationEffectivenessAdminResponse | undefined = dashboardQuery.data;

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <button type="button" className="btn-secondary" onClick={() => void handleExport()}>
          Export CSV
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiTile label="Average effectiveness" value={pct(data?.average_effectiveness ?? 0)} />
        <KpiTile label="Average actual gain" value={(data?.average_actual_gain ?? 0).toFixed(2)} />
        <KpiTile label="Completion rate" value={pct(data?.completion_rate ?? 0)} />
        <KpiTile label="Success rate" value={pct(data?.success_rate ?? 0)} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card">
          <h2 className="text-lg font-semibold text-slate-900">Top-performing concepts</h2>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {(data?.top_performing_concepts ?? []).map((item) => (
              <li key={item.concept_id} className="flex justify-between gap-4">
                <span>{item.concept_name}</span>
                <span className="font-medium">{item.effectiveness_score.toFixed(2)}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="card">
          <h2 className="text-lg font-semibold text-slate-900">Lowest-performing concepts</h2>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {(data?.lowest_performing_concepts ?? []).map((item) => (
              <li key={item.concept_id} className="flex justify-between gap-4">
                <span>{item.concept_name}</span>
                <span className="font-medium">{item.effectiveness_score.toFixed(2)}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card">
          <h2 className="text-lg font-semibold text-slate-900">Readiness uplift trend</h2>
          <ul className="mt-3 space-y-1 text-sm text-slate-700">
            {(data?.readiness_uplift_trend ?? []).map((point) => (
              <li key={String(point.date)} className="flex justify-between">
                <span>{String(point.date)}</span>
                <span>+{Number(point.average_uplift).toFixed(2)}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="card">
          <h2 className="text-lg font-semibold text-slate-900">Forecast uplift trend</h2>
          <ul className="mt-3 space-y-1 text-sm text-slate-700">
            {(data?.forecast_uplift_trend ?? []).map((point) => (
              <li key={String(point.date)} className="flex justify-between">
                <span>{String(point.date)}</span>
                <span>+{Number(point.average_uplift).toFixed(2)}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
