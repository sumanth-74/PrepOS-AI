"use client";

import { useQuery } from "@tanstack/react-query";

import type { RecommendationAnalyticsResponse } from "@/features/copilot/types";
import { adminRecommendationsApi } from "@/lib/api";
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

export function RecommendationAnalyticsDashboard() {
  const token = useAuthStore((state) => state.accessToken);
  const analyticsQuery = useQuery({
    queryKey: ["admin", "recommendations", "analytics"],
    queryFn: () => adminRecommendationsApi.analytics(token!, 30),
    enabled: Boolean(token),
    refetchInterval: 30_000,
  });

  if (analyticsQuery.isLoading) {
    return <p className="text-sm text-slate-600">Loading recommendation analytics…</p>;
  }

  const data: RecommendationAnalyticsResponse | undefined = analyticsQuery.data;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiTile label="Acceptance rate" value={pct(data?.recommendation_acceptance_rate ?? 0)} />
        <KpiTile label="Completion rate" value={pct(data?.completion_rate ?? 0)} />
        <KpiTile label="Avg readiness gain" value={(data?.average_readiness_gain ?? 0).toFixed(2)} />
        <KpiTile
          label="Effectiveness score"
          value={pct(data?.recommendation_effectiveness ?? 0)}
        />
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-slate-900">Top recommended concepts</h2>
        {(data?.top_recommended_concepts.length ?? 0) === 0 ? (
          <p className="mt-3 text-sm text-slate-500">No recommendation events recorded yet.</p>
        ) : (
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {data?.top_recommended_concepts.map((item) => (
              <li key={item.concept_id} className="flex justify-between gap-4">
                <span>{item.concept_id}</span>
                <span className="font-medium">{item.count} shown</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
