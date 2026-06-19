"use client";

import { PageHeader } from "@/components/ui/page-header";
import { QueryBoundary } from "@/components/ui/query-boundary";
import { StatusBadge } from "@/components/ui/status-badge";
import { useRecommendations } from "@/hooks/use-student-queries";
import { formatLabel, formatScore } from "@/lib/utils/format";

export default function RecommendationsPage() {
  const recommendationsQuery = useRecommendations();

  return (
    <>
      <PageHeader
        title="Recommendations"
        description="Canonical next actions from your preparation twin."
      />
      <QueryBoundary
        query={recommendationsQuery}
        loadingLabel="Loading recommendations..."
        emptyTitle="No recommendations yet"
        emptyDescription="Keep studying to receive personalized recommendations."
        isEmpty={(data) => data.length === 0}
      >
        {(items) => (
          <div className="space-y-4">
            {items.map((item) => (
              <article key={`${item.concept_id}-${item.recommendation_type}`} className="card">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="text-base font-semibold text-slate-900">
                      {formatLabel(item.concept_id)}
                    </h2>
                    <p className="mt-1 text-sm text-slate-600">
                      {formatLabel(item.recommendation_type)}
                    </p>
                  </div>
                  <StatusBadge
                    label={`Priority ${formatScore(item.recommendation_score)}`}
                    tone="info"
                  />
                </div>
                <p className="mt-3 text-sm text-slate-700">{item.explanation}</p>
                <p className="mt-2 text-xs text-slate-500">
                  Readiness gain: {formatScore(item.readiness_gain)}
                </p>
              </article>
            ))}
          </div>
        )}
      </QueryBoundary>
    </>
  );
}
