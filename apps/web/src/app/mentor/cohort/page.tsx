"use client";

import { CohortIntelligenceView } from "@/components/cohort/cohort-intelligence-view";
import { PageHeader } from "@/components/ui/page-header";
import { QueryBoundary } from "@/components/ui/query-boundary";
import { useCohortRisks, useCohortSummary, useCohortTrends } from "@/hooks/use-cohort-queries";

export default function MentorCohortPage() {
  const summaryQuery = useCohortSummary(undefined, true);
  const risksQuery = useCohortRisks();
  const trendsQuery = useCohortTrends();

  return (
    <>
      <PageHeader
        title="Cohort intelligence"
        description="Explainable student segmentation, cohort risk, trends, and intervention effectiveness."
      />
      <QueryBoundary
        query={summaryQuery}
        loadingLabel="Loading cohort intelligence..."
        emptyTitle="No cohort data"
        emptyDescription="Cohort snapshots will appear once students are onboarded and segmented."
        isEmpty={(data) => data.student_count === 0}
      >
        {(summary) => (
          <CohortIntelligenceView
            summary={summary}
            risks={risksQuery.data}
            trends={trendsQuery.data}
          />
        )}
      </QueryBoundary>
    </>
  );
}
