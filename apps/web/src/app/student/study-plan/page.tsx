"use client";

import { CalendarDays, Target } from "lucide-react";

import { PremiumCard } from "@/components/design-system/card";
import { ConceptLabel } from "@/components/ui/concept-label";
import { PageHeader } from "@/components/ui/page-header";
import { QueryBoundary } from "@/components/ui/query-boundary";
import { StatusBadge } from "@/components/ui/status-badge";
import { useStudentContext } from "@/hooks/use-student-context";
import { useStudyPlan, useStudyPlanMutations } from "@/hooks/use-student-queries";
import { formatLabel, formatScore } from "@/lib/utils/format";
import type { DailyPlanItem, WeeklyPlanItem } from "@/lib/types/api";

export default function StudyPlanPage() {
  const { examId } = useStudentContext();
  const planQuery = useStudyPlan();
  const { completeMutation, skipMutation } = useStudyPlanMutations();

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
        eyebrow="Daily Mission"
        title="Your study plan"
        description="Structured daily and weekly missions with estimated readiness impact."
      />
      <QueryBoundary
        query={planQuery}
        loadingLabel="Loading study plan..."
        emptyTitle="Let's create your first study plan"
        emptyDescription="Set a preparation goal and complete onboarding — PrepOS will generate adaptive daily missions."
        emptyIcon={CalendarDays}
        emptyAction={{ label: "Set your goal", href: "/student/goals" }}
        emptySecondaryAction={{ label: "Complete onboarding", href: "/student/onboarding" }}
      >
        {(plan) => (
          <div className="space-y-8">
            <PremiumCard glow className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <p className="metric-label">Estimated total gain</p>
                <p className="mt-1 text-metric text-growth-700 dark:text-growth-400">
                  {formatScore(plan.total_estimated_gain)}
                </p>
              </div>
              <div className="flex items-center gap-2 text-sm text-foreground-muted">
                <Target className="h-4 w-4 text-growth-600" />
                Complete items to build momentum
              </div>
            </PremiumCard>

            <section>
              <h2 className="mb-3 text-heading-sm">Today&apos;s missions</h2>
              {plan.daily_plan.length === 0 ? (
                <PremiumCard className="text-center text-sm text-foreground-muted">
                  No missions scheduled today.{" "}
                  <a href="/student/goals" className="font-semibold text-growth-600 hover:underline">
                    Update your goal
                  </a>{" "}
                  to regenerate.
                </PremiumCard>
              ) : (
                <div className="space-y-3">
                  {plan.daily_plan.map((item) => (
                    <DailyItemCard
                      key={`${item.concept_id}-${item.activity_type}`}
                      item={item}
                      examId={examId}
                      onComplete={() => handleComplete(item)}
                      onSkip={() => handleSkip(item)}
                      busy={completeMutation.isPending || skipMutation.isPending}
                    />
                  ))}
                </div>
              )}
            </section>

            <section>
              <h2 className="mb-3 text-heading-sm">Weekly missions</h2>
              {plan.weekly_plan.length === 0 ? (
                <PremiumCard className="text-sm text-foreground-muted">Weekly missions appear after your daily rhythm is established.</PremiumCard>
              ) : (
                <div className="grid gap-3 md:grid-cols-2">
                  {plan.weekly_plan.map((item) => (
                    <WeeklyItemCard key={item.concept_id} item={item} examId={examId} />
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
  examId,
  onComplete,
  onSkip,
  busy,
}: {
  item: DailyPlanItem;
  examId: string | null;
  onComplete: () => void;
  onSkip: () => void;
  busy: boolean;
}) {
  return (
    <article className="card flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0 flex-1">
        <ConceptLabel conceptId={item.concept_id} examId={examId} showPath />
        <p className="text-sm text-foreground-muted">
          {formatLabel(item.activity_type)} · {item.estimated_minutes} min
        </p>
        <p className="mt-1 text-xs text-foreground-subtle">
          Gain {formatScore(item.readiness_gain)} · {item.adjustment_explanation}
        </p>
      </div>
      <div className="flex shrink-0 gap-2">
        <button type="button" className="btn-primary min-h-[44px] min-w-[44px]" disabled={busy} onClick={onComplete}>
          Complete
        </button>
        <button type="button" className="btn-secondary min-h-[44px]" disabled={busy} onClick={onSkip}>
          Skip
        </button>
      </div>
    </article>
  );
}

function WeeklyItemCard({ item, examId }: { item: WeeklyPlanItem; examId: string | null }) {
  return (
    <PremiumCard padding="sm">
      <div className="flex items-start justify-between gap-2">
        <ConceptLabel conceptId={item.concept_id} examId={examId} showPath />
        <StatusBadge label={`${item.target_sessions} sessions`} />
      </div>
      <p className="mt-2 text-sm text-foreground-muted">
        {item.estimated_minutes} min · Gain {formatScore(item.readiness_gain)}
      </p>
    </PremiumCard>
  );
}
