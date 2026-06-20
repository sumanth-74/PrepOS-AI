"use client";

import { KpiCard } from "@/components/ui/kpi-card";
import { KpiSkeletonGrid } from "@/components/ui/loading-skeleton";
import { PageHeader } from "@/components/ui/page-header";
import { QueryBoundary } from "@/components/ui/query-boundary";
import { useMentorDashboard } from "@/hooks/use-mentor-queries";
import { formatLabel, formatScore } from "@/lib/utils/format";

export default function MentorDashboardPage() {
  const dashboardQuery = useMentorDashboard();

  return (
    <>
      <PageHeader
        title="Mentor Dashboard"
        description="Case load, effectiveness, and recommended action."
      />
      <QueryBoundary
        query={dashboardQuery}
        loadingFallback={<KpiSkeletonGrid count={4} />}
        loadingLabel="Loading mentor dashboard..."
        emptyTitle="No mentor dashboard data"
        emptyDescription="Cases and effectiveness metrics appear once students enter the mentor queue."
      >
        {(data) => (
          <div className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <KpiCard label="Open cases" value={String(data.open_cases)} />
              <KpiCard
                label="Critical cases"
                value={String(data.critical_cases)}
                tone={data.critical_cases > 0 ? "danger" : "default"}
              />
              <KpiCard
                label="Mentor effectiveness"
                value={formatScore(data.mentor_effectiveness_score)}
              />
              <KpiCard
                label="Avg resolution (hrs)"
                value={formatScore(data.average_resolution_time_hours)}
              />
            </div>

            <section className="card space-y-3">
              <h2 className="text-sm font-semibold text-slate-900">Best action</h2>
              <p className="text-lg font-medium text-brand-700">
                {formatLabel(data.best_action)}
              </p>
              <div className="grid gap-3 text-sm text-slate-700 sm:grid-cols-2">
                <p>Best action effectiveness: {formatScore(data.best_action_effectiveness)}</p>
                <p>Average action effectiveness: {formatScore(data.average_action_effectiveness)}</p>
              </div>
            </section>
          </div>
        )}
      </QueryBoundary>
    </>
  );
}
