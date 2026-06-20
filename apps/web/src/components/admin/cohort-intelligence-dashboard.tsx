"use client";

import { useQuery } from "@tanstack/react-query";

import { adminCohortApi } from "@/lib/api";
import type { CohortAdminResponse } from "@/lib/types/api";
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

export function CohortIntelligenceDashboard() {
  const token = useAuthStore((state) => state.accessToken);
  const dashboardQuery = useQuery({
    queryKey: ["admin", "cohort"],
    queryFn: () => adminCohortApi.dashboard(token!),
    enabled: Boolean(token),
    refetchInterval: 30_000,
  });
  const summaryQuery = useQuery({
    queryKey: ["admin", "cohort-summary"],
    queryFn: () => adminCohortApi.summary(token!),
    enabled: Boolean(token),
  });

  const handleExport = async () => {
    if (!token) return;
    const csv = await adminCohortApi.exportCsv(token);
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "cohort_intelligence.csv";
    anchor.click();
    URL.revokeObjectURL(url);
  };

  if (dashboardQuery.isLoading) {
    return <p className="text-sm text-slate-600">Loading cohort analytics…</p>;
  }

  const data: CohortAdminResponse | undefined = dashboardQuery.data;
  const summary = summaryQuery.data;

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <button type="button" className="btn-secondary" onClick={() => void handleExport()}>
          Export CSV
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiTile label="Snapshots" value={data?.total_snapshots ?? 0} />
        <KpiTile label="Students segmented" value={data?.total_students_segmented ?? 0} />
        <KpiTile label="Cohort health" value={formatScore(data?.average_cohort_health ?? 0)} />
        <KpiTile label="Snapshots (30d)" value={data?.snapshots_last_30_days ?? 0} />
      </div>

      {summary ? (
        <div className="card">
          <h2 className="text-lg font-semibold text-slate-900">Latest cohort summary</h2>
          <p className="mt-2 text-sm text-slate-700">
            {summary.cohort_id}: {summary.student_count} students, health{" "}
            {formatScore(summary.metrics.cohort_health_score)}
          </p>
        </div>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card">
          <h2 className="text-lg font-semibold text-slate-900">Segment distribution</h2>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {Object.entries(data?.segment_distribution ?? {}).map(([segment, count]) => (
              <li key={segment} className="flex justify-between gap-4">
                <span>{segment.replaceAll("_", " ")}</span>
                <span className="font-medium">{count}</span>
              </li>
            ))}
          </ul>
        </div>
        <div className="card">
          <h2 className="text-lg font-semibold text-slate-900">Mentor comparison</h2>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {(data?.mentor_comparisons ?? []).map((mentor) => (
              <li key={mentor.mentor_id} className="flex justify-between gap-4">
                <span>{mentor.mentor_id.slice(0, 8)}…</span>
                <span className="font-medium">
                  {formatPercent(mentor.intervention_success_rate * 100)} · +
                  {formatScore(mentor.average_gain)}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
