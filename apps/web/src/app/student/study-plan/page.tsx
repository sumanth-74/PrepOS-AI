"use client";

import { PageHeader } from "@/components/ui/page-header";
import { QueryBoundary } from "@/components/ui/query-boundary";
import { StatusBadge } from "@/components/ui/status-badge";
import { useStudyPlan, useStudyPlanMutations } from "@/hooks/use-student-queries";
import { formatLabel, formatScore } from "@/lib/utils/format";
import type { DailyPlanItem, WeeklyPlanItem } from "@/lib/types/api";

export default function StudyPlanPage() {
  const planQuery = useStudyPlan();
  const { completeMutation, skipMutation, examId } = useStudyPlanMutations();

  const handleComplete = (item: DailyPlanItem) => {
    if (!examId) return;
    completeMutation.mutate({
      exam_id: examId,
      concept_id: item.concept_id,
      activity_type: item.activity_type,
      planned_minutes: item.estimated_minutes,
    });
  };

  const handleSkip = (item: DailyPlanItem) => {
    if (!examId) return;
    skipMutation.mutate({
      exam_id: examId,
      concept_id: item.concept_id,
      activity_type: item.activity_type,
      planned_minutes: item.estimated_minutes,
    });
  };

  return (
    <>
      <PageHeader
        title="Study Plan"
        description="Daily and weekly plan with estimated readiness gain."
      />
      <QueryBoundary
        query={planQuery}
        loadingLabel="Loading study plan..."
        emptyTitle="No study plan available"
        emptyDescription="Set a goal and complete onboarding to generate a plan."
      >
        {(plan) => (
          <div className="space-y-8">
            <div className="card">
              <p className="text-xs uppercase text-slate-500">Estimated total gain</p>
              <p className="text-2xl font-semibold text-brand-700">
                {formatScore(plan.total_estimated_gain)}
              </p>
            </div>

            <section>
              <h2 className="mb-3 text-sm font-semibold text-slate-900">Daily plan</h2>
              {plan.daily_plan.length === 0 ? (
                <p className="text-sm text-slate-600">No daily items scheduled.</p>
              ) : (
                <div className="space-y-3">
                  {plan.daily_plan.map((item) => (
                    <DailyItemCard
                      key={`${item.concept_id}-${item.activity_type}`}
                      item={item}
                      onComplete={() => handleComplete(item)}
                      onSkip={() => handleSkip(item)}
                      busy={
                        completeMutation.isPending || skipMutation.isPending
                      }
                    />
                  ))}
                </div>
              )}
            </section>

            <section>
              <h2 className="mb-3 text-sm font-semibold text-slate-900">Weekly plan</h2>
              {plan.weekly_plan.length === 0 ? (
                <p className="text-sm text-slate-600">No weekly items scheduled.</p>
              ) : (
                <div className="grid gap-3 md:grid-cols-2">
                  {plan.weekly_plan.map((item) => (
                    <WeeklyItemCard
                      key={item.concept_id}
                      item={item}
                    />
                  ))}
                </div>
              )}
            </section>
          </div>
        )}
      </QueryBoundary>
    </>
  );
}

function DailyItemCard({
  item,
  onComplete,
  onSkip,
  busy,
}: {
  item: DailyPlanItem;
  onComplete: () => void;
  onSkip: () => void;
  busy: boolean;
}) {
  return (
    <article className="card flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h3 className="text-sm font-semibold text-slate-900">{item.concept_id}</h3>
        <p className="text-sm text-slate-600">
          {formatLabel(item.activity_type)} · {item.estimated_minutes} min
        </p>
        <p className="mt-1 text-xs text-slate-500">
          Gain: {formatScore(item.readiness_gain)} · {item.adjustment_explanation}
        </p>
      </div>
      <div className="flex gap-2">
        <button
          type="button"
          className="btn-primary"
          disabled={busy}
          onClick={onComplete}
        >
          Complete
        </button>
        <button
          type="button"
          className="btn-secondary"
          disabled={busy}
          onClick={onSkip}
        >
          Skip
        </button>
      </div>
    </article>
  );
}

function WeeklyItemCard({ item }: { item: WeeklyPlanItem }) {
  return (
    <article className="card">
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-900">{item.concept_id}</h3>
        <StatusBadge label={`${item.target_sessions} sessions`} />
      </div>
      <p className="mt-2 text-sm text-slate-600">
        {item.estimated_minutes} min · Gain {formatScore(item.readiness_gain)}
      </p>
    </article>
  );
}
