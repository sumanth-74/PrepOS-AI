"use client";

import Link from "next/link";
import { use } from "react";

import { MentorInterventionView } from "@/components/interventions/mentor-intervention-view";
import { PageHeader } from "@/components/ui/page-header";
import { QueryBoundary } from "@/components/ui/query-boundary";
import { useStudentDisplayName, useStudentProfile } from "@/hooks/use-student-lookup";
import {
  useMentorInterventionMutations,
  useMentorStudentInterventions,
} from "@/hooks/use-intervention-queries";
import { mentorApi } from "@/lib/api";
import { useAuthStore } from "@/stores";

export default function MentorStudentInterventionsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id: studentId } = use(params);
  const token = useAuthStore((state) => state.accessToken);
  const profileQuery = useStudentProfile(studentId);
  const studentName = useStudentDisplayName(studentId, profileQuery.data?.target_exam);
  const examId = profileQuery.data?.target_exam ?? undefined;
  const bundleQuery = useMentorStudentInterventions(studentId, examId);
  const { generateMutation, executeMutation, completeMutation } =
    useMentorInterventionMutations(studentId, examId);

  return (
    <>
      <PageHeader
        title="Student interventions"
        description={studentName}
        actions={
          <div className="flex gap-2">
            <Link href={`/mentor/student/${studentId}`} className="btn-secondary">
              Twin view
            </Link>
            <button
              type="button"
              className="btn-primary"
              disabled={generateMutation.isPending}
              onClick={() => generateMutation.mutate()}
            >
              {generateMutation.isPending ? "Generating…" : "Generate interventions"}
            </button>
          </div>
        }
      />
      <QueryBoundary
        query={bundleQuery}
        loadingLabel="Loading interventions..."
        emptyTitle="No interventions yet"
        emptyDescription="Generate explainable intervention recommendations for this student."
        isEmpty={() => false}
      >
        {(bundle) => (
          <MentorInterventionView
            bundle={bundle}
            generating={generateMutation.isPending}
            executing={executeMutation.isPending}
            completing={completeMutation.isPending}
            onGenerate={() => generateMutation.mutate()}
            onExecute={(id) => executeMutation.mutate(id)}
            onComplete={(id) => completeMutation.mutate(id)}
            onExplain={(id) => mentorApi.explainIntervention(token!, id)}
          />
        )}
      </QueryBoundary>
    </>
  );
}
