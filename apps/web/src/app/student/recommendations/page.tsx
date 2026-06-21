"use client";

import Link from "next/link";
import { Lightbulb, Sparkles } from "lucide-react";

import { PremiumCard } from "@/components/design-system/card";
import { StaggerContainer, StaggerItem } from "@/components/motion/primitives";
import { ConceptLabel } from "@/components/ui/concept-label";
import { PageHeader } from "@/components/ui/page-header";
import { QueryBoundary } from "@/components/ui/query-boundary";
import { StatusBadge } from "@/components/ui/status-badge";
import { useStudentContext } from "@/hooks/use-student-context";
import { useRecommendations } from "@/hooks/use-student-queries";
import { formatLabel, formatScore } from "@/lib/utils/format";

export default function RecommendationsPage() {
  const { examId } = useStudentContext();
  const recommendationsQuery = useRecommendations();

  return (
    <>
      <PageHeader
        eyebrow="Intelligence"
        title="What should I study next?"
        description="AI-ranked actions based on your twin, weaknesses, goals, and PYQ patterns."
      />
      <QueryBoundary
        query={recommendationsQuery}
        loadingLabel="Loading recommendations..."
        emptyTitle="Unlock personalized recommendations"
        emptyDescription="Complete a readiness assessment and log study sessions — your twin will rank the highest-impact concepts."
        emptyIcon={Sparkles}
        emptyAction={{ label: "Log study activity", href: "/student/activities" }}
        emptySecondaryAction={{ label: "View learning graph", href: "/student/learning-graph" }}
        isEmpty={(data) => data.length === 0}
      >
        {(items) => (
          <StaggerContainer className="space-y-4">
            {items.map((item, index) => (
              <StaggerItem key={item.concept_id}>
                <PremiumCard className="group">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="flex gap-3">
                      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-growth-100 text-sm font-bold text-growth-700 dark:bg-growth-900/50">
                        {index + 1}
                      </span>
                      <div>
                        <ConceptLabel conceptId={item.concept_id} examId={examId} showPath />
                        <p className="mt-1 text-sm text-foreground-muted">
                          {item.reasons[0] ?? formatLabel(item.reason_codes[0] ?? "recommendation")}
                        </p>
                      </div>
                    </div>
                    <StatusBadge label={`Impact ${formatScore(String(item.impact_score))}`} tone="info" />
                  </div>
                  <div className="mt-4 h-2 overflow-hidden rounded-full bg-surface-raised">
                    <div
                      className="h-full rounded-full bg-gradient-growth transition-all duration-700"
                      style={{ width: `${Math.min(100, item.impact_score * 10)}%` }}
                    />
                  </div>
                  <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs text-foreground-muted">
                    <span>Gain +{formatScore(String(item.estimated_readiness_gain))}</span>
                    <span>{formatLabel(item.confidence)} confidence</span>
                  </div>
                  <Link
                    href="/student/activities"
                    className="mt-3 inline-flex items-center gap-1 text-sm font-semibold text-growth-600 opacity-0 transition-opacity group-hover:opacity-100"
                  >
                    <Lightbulb className="h-4 w-4" /> Log study on this concept
                  </Link>
                </PremiumCard>
              </StaggerItem>
            ))}
          </StaggerContainer>
        )}
      </QueryBoundary>
    </>
  );
}
