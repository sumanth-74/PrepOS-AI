"use client";

import Link from "next/link";
import { use } from "react";
import { ConceptLabel } from "@/components/ui/concept-label";
import { KpiCard } from "@/components/ui/kpi-card";
import { PageHeader } from "@/components/ui/page-header";
import { QueryBoundary } from "@/components/ui/query-boundary";
import { StatusBadge } from "@/components/ui/status-badge";
import { useStudentProfile, useStudentDisplayName } from "@/hooks/use-student-lookup";
import {
  useRecommendations,
  useTwin,
  useTwinDashboard,
} from "@/hooks/use-student-queries";
import { formatLabel, formatPercent, formatScore } from "@/lib/utils/format";
import type { ConceptRecommendation } from "@/lib/types/api";

export default function MentorStudentPage({
  params,
}: {
  params: Promise<{ studentId: string }>;
}) {
  const { studentId } = use(params);
  const profileQuery = useStudentProfile(studentId);
  const studentName = useStudentDisplayName(studentId, profileQuery.data?.target_exam);
  const examId = profileQuery.data?.target_exam ?? null;
  const dashboardQuery = useTwinDashboard(studentId);
  const twinQuery = useTwin(studentId);
  const recommendationsQuery = useRecommendations(studentId, examId);

  return (
    <>
      <PageHeader
        title="Student Twin"
        description={studentName}
        actions={
          <div className="flex gap-2">
            <Link href={`/mentor/students/${studentId}/planning`} className="btn-secondary">
              Planning
            </Link>
            <Link href={`/mentor/students/${studentId}/forecasting`} className="btn-secondary">
              Forecasting
            </Link>
            <Link href={`/mentor/students/${studentId}/interventions`} className="btn-secondary">
              Interventions
            </Link>
            <Link href="/mentor/queue" className="btn-secondary">
              Back to queue
            </Link>
          </div>
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
          {(items) => <MentorRecommendations examId={examId} items={items} />}
        </QueryBoundary>
      </div>
    </>
  );
}

function MentorRecommendations({
  examId,
  items,
}: {
  examId: string | null;
  items: ConceptRecommendation[];
}) {
  return (
    <section className="card">
      <h2 className="text-sm font-semibold text-slate-900">Recommendations</h2>
      <ul className="mt-3 space-y-3">
        {items.slice(0, 8).map((item) => (
          <li key={item.concept_id} className="rounded-lg border border-slate-100 p-3">
            <div className="flex items-start justify-between gap-2">
              <ConceptLabel conceptId={item.concept_id} examId={examId} showPath />
              <StatusBadge label={formatScore(String(item.impact_score))} tone="info" />
            </div>
            <p className="mt-1 text-sm text-slate-600">
              {item.reasons[0] ?? item.concept_name}
            </p>
          </li>
        ))}
      </ul>
    </section>
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
