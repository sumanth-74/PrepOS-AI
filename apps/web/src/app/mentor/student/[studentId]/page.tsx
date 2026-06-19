"use client";

import Link from "next/link";
import { use } from "react";
import { KpiCard } from "@/components/ui/kpi-card";
import { PageHeader } from "@/components/ui/page-header";
import { QueryBoundary } from "@/components/ui/query-boundary";
import { StatusBadge } from "@/components/ui/status-badge";
import {
  useRecommendations,
  useTwin,
  useTwinDashboard,
} from "@/hooks/use-student-queries";
import { formatLabel, formatPercent, formatScore } from "@/lib/utils/format";

export default function MentorStudentPage({
  params,
}: {
  params: Promise<{ studentId: string }>;
}) {
  const { studentId } = use(params);
  const dashboardQuery = useTwinDashboard(studentId);
  const twinQuery = useTwin(studentId);
  const recommendationsQuery = useRecommendations(studentId);

  return (
    <>
      <PageHeader
        title="Student Twin"
        description={`Twin view for student ${studentId}`}
        actions={
          <Link href="/mentor/queue" className="btn-secondary">
            Back to queue
          </Link>
        }
      />

      <QueryBoundary
        query={dashboardQuery}
        loadingLabel="Loading student dashboard..."
        emptyTitle="No twin dashboard for student"
      >
        {(dashboard) => (
          <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <KpiCard label="Readiness" value={formatScore(dashboard.readiness_score)} />
            <KpiCard label="Expected score" value={formatScore(dashboard.expected_score)} />
            <KpiCard
              label="Goal probability"
              value={formatPercent(dashboard.goal_probability)}
            />
            <KpiCard label="Mentor status" value={formatLabel(dashboard.mentor_status)} />
          </div>
        )}
      </QueryBoundary>

      <div className="grid gap-6 lg:grid-cols-2">
        <QueryBoundary
          query={twinQuery}
          loadingLabel="Loading twin..."
          emptyTitle="No twin data"
        >
          {(twin) => (
            <section className="card space-y-4">
              <h2 className="text-sm font-semibold text-slate-900">Forecast & intervention</h2>
              <TwinBlock title="Predicted outcome" data={twin.predicted_outcome} />
              <TwinBlock title="Intervention" data={twin.intervention} />
              <TwinBlock title="Mentor summary" data={twin.mentor} />
              <TwinBlock title="Behavior profile" data={twin.behavior_profile} />
            </section>
          )}
        </QueryBoundary>

        <QueryBoundary
          query={recommendationsQuery}
          loadingLabel="Loading recommendations..."
          emptyTitle="No recommendations"
          isEmpty={(data) => data.length === 0}
        >
          {(items) => (
            <section className="card">
              <h2 className="text-sm font-semibold text-slate-900">Recommendations</h2>
              <ul className="mt-3 space-y-3">
                {items.slice(0, 8).map((item) => (
                  <li
                    key={`${item.concept_id}-${item.recommendation_type}`}
                    className="rounded-lg border border-slate-100 p-3"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-sm font-medium text-slate-900">
                        {formatLabel(item.concept_id)}
                      </p>
                      <StatusBadge
                        label={formatScore(item.recommendation_score)}
                        tone="info"
                      />
                    </div>
                    <p className="mt-1 text-sm text-slate-600">{item.explanation}</p>
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

function TwinBlock({
  title,
  data,
}: {
  title: string;
  data: Record<string, unknown> | null;
}) {
  return (
    <div>
      <h3 className="text-xs font-semibold uppercase text-slate-500">{title}</h3>
      <pre className="mt-2 overflow-x-auto rounded-lg bg-slate-50 p-3 text-xs text-slate-700">
        {JSON.stringify(data ?? {}, null, 2)}
      </pre>
    </div>
  );
}
