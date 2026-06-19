"use client";

import { KpiCard } from "@/components/ui/kpi-card";
import { PageHeader } from "@/components/ui/page-header";
import { QueryBoundary } from "@/components/ui/query-boundary";
import { StatusBadge } from "@/components/ui/status-badge";
import { useTwinDashboard } from "@/hooks/use-student-queries";
import { formatLabel, formatPercent, formatScore } from "@/lib/utils/format";

export default function StudentDashboardPage() {
  const dashboardQuery = useTwinDashboard();

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Your preparation twin at a glance."
      />
      <QueryBoundary
        query={dashboardQuery}
        loadingLabel="Loading dashboard..."
        emptyTitle="No dashboard data yet"
        emptyDescription="Complete onboarding and study activities to populate your twin."
      >
        {(data) => (
          <div className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <KpiCard
                label="Readiness score"
                value={formatScore(data.readiness_score)}
              />
              <KpiCard
                label="Expected score"
                value={formatScore(data.expected_score)}
              />
              <KpiCard
                label="Goal probability"
                value={formatPercent(data.goal_probability)}
              />
              <KpiCard
                label="Study plan items"
                value={`${data.today_plan_count} today / ${data.weekly_plan_count} weekly`}
              />
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
              <section className="card space-y-3">
                <h2 className="text-sm font-semibold text-slate-900">Mentor status</h2>
                <div className="flex flex-wrap gap-2">
                  <StatusBadge label={formatLabel(data.mentor_status)} tone="info" />
                  {data.mentor_case?.case_status ? (
                    <StatusBadge
                      label={`Case: ${formatLabel(data.mentor_case.case_status)}`}
                      tone="warning"
                    />
                  ) : null}
                </div>
                <p className="text-sm text-slate-700">
                  {data.top_mentor_message ?? "No mentor message available."}
                </p>
                {data.mentor_action ? (
                  <p className="text-xs text-slate-500">
                    Suggested action: {formatLabel(data.mentor_action)}
                  </p>
                ) : null}
              </section>

              <section className="card space-y-3">
                <h2 className="text-sm font-semibold text-slate-900">
                  Decision & intervention
                </h2>
                <p className="text-sm text-slate-700">
                  Current decision: {formatLabel(data.current_decision)}
                </p>
                <p className="text-sm text-slate-700">
                  Current intervention: {formatLabel(data.current_intervention)}
                </p>
                {data.intervention_urgency ? (
                  <StatusBadge
                    label={`Urgency: ${formatLabel(data.intervention_urgency)}`}
                    tone="warning"
                  />
                ) : null}
              </section>
            </div>

            <section className="card">
              <h2 className="text-sm font-semibold text-slate-900">Milestone status</h2>
              <div className="mt-3 grid gap-3 sm:grid-cols-3">
                <div>
                  <p className="text-xs text-slate-500">Status</p>
                  <p className="text-sm font-medium">
                    {formatLabel(data.milestone_status)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Next milestone</p>
                  <p className="text-sm font-medium">
                    {data.next_milestone_date ?? "—"}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Target readiness</p>
                  <p className="text-sm font-medium">
                    {formatScore(data.next_milestone_target)}
                  </p>
                </div>
              </div>
              {data.on_track !== null ? (
                <div className="mt-3">
                  <StatusBadge
                    label={data.on_track ? "On track" : "Off track"}
                    tone={data.on_track ? "success" : "danger"}
                  />
                </div>
              ) : null}
            </section>
          </div>
        )}
      </QueryBoundary>
    </>
  );
}
