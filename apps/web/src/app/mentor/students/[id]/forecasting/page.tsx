"use client";

import Link from "next/link";
import { use } from "react";

import { GoalForecastingView } from "@/components/forecasting/goal-forecasting-view";
import { PageHeader } from "@/components/ui/page-header";
import { QueryBoundary } from "@/components/ui/query-boundary";
import { useStudentDisplayName, useStudentProfile } from "@/hooks/use-student-lookup";
import {
  useMentorForecastMutations,
  useMentorStudentForecast,
} from "@/hooks/use-forecasting-queries";

export default function MentorStudentForecastingPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id: studentId } = use(params);
  const profileQuery = useStudentProfile(studentId);
  const studentName = useStudentDisplayName(studentId, profileQuery.data?.target_exam);
  const examId = profileQuery.data?.target_exam ?? undefined;
  const forecastQuery = useMentorStudentForecast(studentId, examId);
  const { simulateMutation } = useMentorForecastMutations(studentId, examId);

  return (
    <>
      <PageHeader
        title="Student forecasting"
        description={studentName}
        actions={
          <div className="flex gap-2">
            <Link href={`/mentor/student/${studentId}`} className="btn-secondary">
              Twin view
            </Link>
            <button
              type="button"
              className="btn-primary"
              disabled={simulateMutation.isPending}
              onClick={() => simulateMutation.mutate()}
            >
              {simulateMutation.isPending ? "Simulating…" : "Simulate intervention"}
            </button>
          </div>
        }
      />
      <QueryBoundary
        query={forecastQuery}
        loadingLabel="Loading student forecast..."
        emptyTitle="No forecast for student"
        emptyDescription="Simulate to generate an explainable goal forecast with scenarios."
        isEmpty={() => false}
      >
        {(forecast) => (
          <GoalForecastingView
            forecast={forecast}
            showRegenerate
            generating={simulateMutation.isPending}
            onGenerate={() => simulateMutation.mutate()}
          />
        )}
      </QueryBoundary>
    </>
  );
}
