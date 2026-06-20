"use client";

import { AdaptivePlanningView } from "@/components/planning/adaptive-planning-view";
import { PageHeader } from "@/components/ui/page-header";
import { QueryBoundary } from "@/components/ui/query-boundary";
import {
  useAdaptivePlan,
  useAdaptivePlanMutations,
} from "@/hooks/use-planning-queries";
import { useStudentContext } from "@/hooks/use-student-context";
import { studentApi } from "@/lib/api";

export default function StudentPlanningPage() {
  const { examId, token } = useStudentContext();
  const planQuery = useAdaptivePlan();
  const { generateMutation, completeMutation } = useAdaptivePlanMutations();

  return (
    <>
      <PageHeader
        title="Adaptive Planning"
        description="Explainable weekly study plan from twin signals, recommendations, PYQ, current affairs, and coaching memory."
        actions={
          <button
            type="button"
            className="btn-primary"
            disabled={generateMutation.isPending}
            onClick={() => generateMutation.mutate(undefined)}
          >
            {generateMutation.isPending ? "Generating…" : "Generate plan"}
          </button>
        }
      />
      <QueryBoundary
        query={planQuery}
        loadingLabel="Loading adaptive plan..."
        emptyTitle="No adaptive plan yet"
        emptyDescription="Generate a plan to see today, this week, and next week draft schedules."
        isEmpty={() => false}
      >
        {(plan) => (
          <AdaptivePlanningView
            plan={plan}
            examId={examId}
            generating={generateMutation.isPending}
            completing={completeMutation.isPending}
            onGenerate={() => generateMutation.mutate(undefined)}
            onCompleteItem={(itemId) => completeMutation.mutate(itemId)}
            onExplainConcept={(conceptId) =>
              studentApi.explainPlanConcept(token!, conceptId, examId ?? undefined)
            }
          />
        )}
      </QueryBoundary>
    </>
  );
}
