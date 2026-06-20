"use client";

import Link from "next/link";
import { use } from "react";

import { AdaptivePlanningView } from "@/components/planning/adaptive-planning-view";
import { PageHeader } from "@/components/ui/page-header";
import { QueryBoundary } from "@/components/ui/query-boundary";
import { useStudentDisplayName, useStudentProfile } from "@/hooks/use-student-lookup";
import {
  useMentorPlanMutations,
  useMentorStudentPlan,
} from "@/hooks/use-planning-queries";

export default function MentorStudentPlanningPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id: studentId } = use(params);
  const profileQuery = useStudentProfile(studentId);
  const studentName = useStudentDisplayName(studentId, profileQuery.data?.target_exam);
  const examId = profileQuery.data?.target_exam ?? undefined;
  const planQuery = useMentorStudentPlan(studentId, examId);
  const { regenerateMutation } = useMentorPlanMutations(studentId, examId);

  return (
    <>
      <PageHeader
        title="Student planning"
        description={studentName}
        actions={
          <div className="flex gap-2">
            <Link href={`/mentor/student/${studentId}`} className="btn-secondary">
              Twin view
            </Link>
            <button
              type="button"
              className="btn-primary"
              disabled={regenerateMutation.isPending}
              onClick={() => regenerateMutation.mutate()}
            >
              Regenerate plan
            </button>
          </div>
        }
      />
      <QueryBoundary
        query={planQuery}
        loadingLabel="Loading student plan..."
        emptyTitle="No adaptive plan for student"
        emptyDescription="Regenerate to create an explainable weekly plan."
        isEmpty={() => false}
      >
        {(plan) => (
          <AdaptivePlanningView
            plan={plan}
            examId={examId ?? null}
            showRegenerate
            generating={regenerateMutation.isPending}
            onGenerate={() => regenerateMutation.mutate()}
          />
        )}
      </QueryBoundary>
    </>
  );
}
