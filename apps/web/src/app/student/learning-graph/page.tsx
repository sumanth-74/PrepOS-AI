"use client";

import { GitBranch } from "lucide-react";

import { PremiumCard } from "@/components/design-system/card";
import { ReadinessRadar, SegmentHeatmap } from "@/components/charts/lazy-charts";
import { ConceptLabel } from "@/components/ui/concept-label";
import { PageHeader } from "@/components/ui/page-header";
import { QueryBoundary } from "@/components/ui/query-boundary";
import { StatusBadge } from "@/components/ui/status-badge";
import { useStudentContext } from "@/hooks/use-student-context";
import { useLearningGraph, useReadiness, useTwinDashboard } from "@/hooks/use-student-queries";
import { formatLabel, formatPercent, formatScore } from "@/lib/utils/format";

export default function LearningGraphPage() {
  const { examId } = useStudentContext();
  const graphQuery = useLearningGraph();
  const readinessQuery = useReadiness();
  const dashboardQuery = useTwinDashboard();

  return (
    <>
      <PageHeader
        eyebrow="Knowledge Map"
        title="Where am I strong — and where am I weak?"
        description="Concept mastery, readiness dimensions, and focus areas across your syllabus."
      />

      <div className="mb-6">
        <QueryBoundary
          query={readinessQuery}
          loadingLabel="Loading readiness..."
          emptyTitle="Build your readiness profile"
          emptyDescription="Log assessments and revisions to map your knowledge, retention, and confidence."
          emptyIcon={GitBranch}
          emptyAction={{ label: "Log activity", href: "/student/activities" }}
          emptySecondaryAction={{ label: "View recommendations", href: "/student/recommendations" }}
        >
          {(readiness) => {
            const radarData = [
              { dimension: "Knowledge", value: Number(readiness.knowledge_subscore ?? 0) },
              { dimension: "Retention", value: Number(readiness.retention_subscore ?? 0) },
              { dimension: "Confidence", value: Number(readiness.confidence_subscore ?? 0) },
              { dimension: "Coverage", value: Number(readiness.coverage_subscore ?? 0) },
            ];
            return (
              <div className="grid gap-6 lg:grid-cols-2">
                <PremiumCard glow>
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="metric-label">Overall readiness</p>
                      <p className="mt-1 text-metric text-growth-700 dark:text-growth-400">
                        {formatScore(readiness.overall_score)}
                      </p>
                    </div>
                    <StatusBadge label={`${readiness.rated_node_count}/${readiness.total_node_count} rated`} tone="info" />
                  </div>
                  <ReadinessRadar data={radarData} height={220} className="mt-4" />
                </PremiumCard>
                <PremiumCard>
                  <h2 className="text-heading-sm">Subscores</h2>
                  <div className="mt-4 grid gap-4 sm:grid-cols-2">
                    <Metric label="Knowledge" value={readiness.knowledge_subscore} />
                    <Metric label="Retention" value={readiness.retention_subscore} />
                    <Metric label="Confidence" value={readiness.confidence_subscore} />
                    <Metric label="Coverage" value={readiness.coverage_subscore} />
                  </div>
                </PremiumCard>
              </div>
            );
          }}
        </QueryBoundary>
      </div>

      <QueryBoundary
        query={graphQuery}
        loadingLabel="Loading concepts..."
        emptyTitle="Your learning graph is provisioning"
        emptyDescription="Complete onboarding — your syllabus concepts will appear here within moments."
        emptyAction={{ label: "Complete onboarding", href: "/student/onboarding" }}
        isEmpty={(data) => data.nodes.length === 0}
      >
        {(graph) => (
          <>
            <SegmentHeatmap
              cells={graph.nodes.slice(0, 8).map((node) => ({
                label: node.concept_id.split(".").pop() ?? node.concept_id,
                value: Math.round(Number(node.mastery_score ?? 0)),
              }))}
              className="mb-6"
            />
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {graph.nodes.map((node) => (
                <PremiumCard key={node.concept_id} padding="sm" className="space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <ConceptLabel conceptId={node.concept_id} examId={examId} showPath />
                    <StatusBadge label={formatLabel(node.node_state)} />
                  </div>
                  <div className="h-1.5 overflow-hidden rounded-full bg-surface-raised">
                    <div
                      className="h-full rounded-full bg-gradient-growth"
                      style={{ width: `${Math.min(100, Number(node.mastery_score ?? 0))}%` }}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs text-foreground-muted">
                    <span>Mastery: {formatScore(node.mastery_score)}</span>
                    <span>Retention: {formatScore(node.retention_score)}</span>
                  </div>
                </PremiumCard>
              ))}
            </div>
          </>
        )}
      </QueryBoundary>

      <div className="mt-8 grid gap-4 lg:grid-cols-2">
        <QueryBoundary
          query={dashboardQuery}
          loadingLabel="Loading strengths..."
          emptyTitle="Strengths emerging"
          emptyDescription="Keep studying — your top drivers will appear here."
          isEmpty={(data) => data.top_positive_drivers.length === 0}
        >
          {(dashboard) => (
            <PremiumCard>
              <h2 className="text-heading-sm text-growth-700">Strengths</h2>
              <ul className="mt-3 space-y-2 text-sm text-foreground">
                {dashboard.top_positive_drivers.map((driver) => (
                  <li key={driver} className="flex items-center gap-2">
                    <span className="text-growth-600">↑</span>
                    {formatLabel(driver)}
                  </li>
                ))}
              </ul>
            </PremiumCard>
          )}
        </QueryBoundary>

        <QueryBoundary
          query={dashboardQuery}
          loadingLabel="Loading weaknesses..."
          emptyTitle="No critical weaknesses yet"
          emptyDescription="Log more activities to identify focus areas."
          isEmpty={(data) => data.top_negative_drivers.length === 0}
        >
          {(dashboard) => (
            <PremiumCard>
              <h2 className="text-heading-sm text-amber-700">Focus areas</h2>
              <ul className="mt-3 space-y-2 text-sm text-foreground">
                {dashboard.top_negative_drivers.map((driver) => (
                  <li key={driver} className="flex items-center gap-2">
                    <span className="text-amber-600">!</span>
                    {formatLabel(driver)}
                  </li>
                ))}
              </ul>
            </PremiumCard>
          )}
        </QueryBoundary>
      </div>
    </>
  );
}

function Metric({ label, value }: { label: string; value: string | null }) {
  return (
    <div className="rounded-xl bg-surface-raised p-3">
      <p className="text-xs text-foreground-muted">{label}</p>
      <p className="text-lg font-semibold text-foreground">{formatPercent(value)}</p>
    </div>
  );
}
