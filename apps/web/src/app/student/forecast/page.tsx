"use client";

import { ConceptLabel } from "@/components/ui/concept-label";
import { KpiCard } from "@/components/ui/kpi-card";
import { PageHeader } from "@/components/ui/page-header";
import { QueryBoundary } from "@/components/ui/query-boundary";
import { StatusBadge } from "@/components/ui/status-badge";
import { useStudentContext } from "@/hooks/use-student-context";
import { useRecommendations, useTwin, useTwinDashboard } from "@/hooks/use-student-queries";
import { formatLabel, formatPercent, formatScore } from "@/lib/utils/format";

export default function ForecastPage() {
  const { examId } = useStudentContext();
  const dashboardQuery = useTwinDashboard();
  const twinQuery = useTwin();
  const recommendationsQuery = useRecommendations();

  return (
    <>
      <PageHeader
        title="Forecast"
        description="Projected readiness, score range, probability, and scenarios."
      />

      <QueryBoundary
        query={dashboardQuery}
        loadingLabel="Loading forecast..."
        emptyTitle="No forecast data"
      >
        {(dashboard) => (
          <div className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <KpiCard
                label="Projected readiness"
                value={formatScore(dashboard.projected_readiness)}
              />
              <KpiCard
                label="Score range"
                value={`${formatScore(dashboard.low_score)} – ${formatScore(dashboard.high_score)}`}
              />
              <KpiCard
                label="Goal probability"
                value={formatPercent(dashboard.goal_probability)}
              />
              <KpiCard
                label="Gap to goal"
                value={formatScore(dashboard.gap_to_goal)}
                tone={dashboard.on_track ? "success" : "warning"}
              />
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
              <section className="card space-y-3">
                <h2 className="text-sm font-semibold text-slate-900">Scenarios</h2>
                <div className="grid gap-3 sm:grid-cols-2">
                  <Metric
                    label="Best case readiness"
                    value={formatScore(dashboard.best_case_readiness)}
                  />
                  <Metric
                    label="Worst case readiness"
                    value={formatScore(dashboard.worst_case_readiness)}
                  />
                  <Metric
                    label="Expected score"
                    value={formatScore(dashboard.expected_score)}
                  />
                  <Metric label="Risk level" value={formatLabel(dashboard.risk_level)} />
                </div>
              </section>

              <section className="card space-y-3">
                <h2 className="text-sm font-semibold text-slate-900">Milestones</h2>
                <div className="space-y-2 text-sm text-slate-700">
                  <p>Status: {formatLabel(dashboard.milestone_status)}</p>
                  <p>Next date: {dashboard.next_milestone_date ?? "—"}</p>
                  <p>Target: {formatScore(dashboard.next_milestone_target)}</p>
                  <p>
                    Weekly progress: {formatScore(dashboard.expected_weekly_progress)}
                  </p>
                </div>
                {dashboard.on_track !== null ? (
                  <StatusBadge
                    label={dashboard.on_track ? "On track" : "Off track"}
                    tone={dashboard.on_track ? "success" : "warning"}
                  />
                ) : null}
              </section>
            </div>
          </div>
        )}
      </QueryBoundary>

      <div className="mt-8 grid gap-4 lg:grid-cols-2">
        <QueryBoundary
          query={twinQuery}
          loadingLabel="Loading twin scenarios..."
          emptyTitle="No twin scenario data"
        >
          {(twin) => (
            <section className="card">
              <h2 className="text-sm font-semibold text-slate-900">Twin simulations</h2>
              <pre className="mt-3 overflow-x-auto rounded-lg bg-slate-50 p-3 text-xs text-slate-700">
                {JSON.stringify(twin.simulations ?? twin.predicted_outcome, null, 2)}
              </pre>
            </section>
          )}
        </QueryBoundary>

        <QueryBoundary
          query={recommendationsQuery}
          loadingLabel="Loading forecast actions..."
          emptyTitle="No forecast actions"
          isEmpty={(data) => data.length === 0}
        >
          {(items) => (
            <section className="card">
              <h2 className="text-sm font-semibold text-slate-900">Top forecast actions</h2>
              <ul className="mt-3 space-y-3 text-sm text-slate-700">
                {items.slice(0, 5).map((item) => (
                  <li key={item.concept_id}>
                    <ConceptLabel conceptId={item.concept_id} examId={examId} />
                    <p className="mt-1">{item.reasons[0] ?? item.concept_name}</p>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </QueryBoundary>
      </div>
    </>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-sm font-medium text-slate-900">{value}</p>
    </div>
  );
}
