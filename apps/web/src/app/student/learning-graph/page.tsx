"use client";

import { PageHeader } from "@/components/ui/page-header";
import { QueryBoundary } from "@/components/ui/query-boundary";
import { StatusBadge } from "@/components/ui/status-badge";
import {
  useLearningGraph,
  useReadiness,
  useTwinDashboard,
} from "@/hooks/use-student-queries";
import { formatLabel, formatPercent, formatScore } from "@/lib/utils/format";

export default function LearningGraphPage() {
  const graphQuery = useLearningGraph();
  const readinessQuery = useReadiness();
  const dashboardQuery = useTwinDashboard();

  return (
    <>
      <PageHeader
        title="Learning Graph"
        description="Concept mastery, readiness, strengths, and weaknesses."
      />

      <div className="mb-6">
        <QueryBoundary
          query={readinessQuery}
          loadingLabel="Loading readiness..."
          emptyTitle="No readiness data"
        >
          {(readiness) => (
            <div className="card">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-xs uppercase text-slate-500">Overall readiness</p>
                  <p className="text-3xl font-semibold text-brand-700">
                    {formatScore(readiness.overall_score)}
                  </p>
                </div>
                <StatusBadge
                  label={`${readiness.rated_node_count}/${readiness.total_node_count} rated`}
                />
              </div>
              <div className="mt-4 grid gap-3 sm:grid-cols-4">
                <Metric label="Knowledge" value={readiness.knowledge_subscore} />
                <Metric label="Retention" value={readiness.retention_subscore} />
                <Metric label="Confidence" value={readiness.confidence_subscore} />
                <Metric label="Coverage" value={readiness.coverage_subscore} />
              </div>
            </div>
          )}
        </QueryBoundary>
      </div>

      <QueryBoundary
        query={graphQuery}
        loadingLabel="Loading concepts..."
        emptyTitle="No concepts provisioned"
        isEmpty={(data) => data.nodes.length === 0}
      >
        {(graph) => (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {graph.nodes.map((node) => (
              <article key={node.concept_id} className="card space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="text-sm font-semibold text-slate-900">
                    {node.concept_id}
                  </h3>
                  <StatusBadge label={formatLabel(node.node_state)} />
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs text-slate-600">
                  <span>Mastery: {formatScore(node.mastery_score)}</span>
                  <span>Retention: {formatScore(node.retention_score)}</span>
                  <span>Confidence: {formatScore(node.confidence_score)}</span>
                  <span>Importance: {formatScore(node.importance_score)}</span>
                </div>
              </article>
            ))}
          </div>
        )}
      </QueryBoundary>

      <div className="mt-8 grid gap-4 lg:grid-cols-2">
        <QueryBoundary
          query={dashboardQuery}
          loadingLabel="Loading strengths..."
          emptyTitle="No strength drivers"
          isEmpty={(data) => data.top_positive_drivers.length === 0}
        >
          {(dashboard) => (
            <section className="card">
              <h2 className="text-sm font-semibold text-slate-900">Strengths</h2>
              <ul className="mt-3 space-y-2 text-sm text-slate-700">
                {dashboard.top_positive_drivers.map((driver) => (
                  <li key={driver}>{formatLabel(driver)}</li>
                ))}
              </ul>
            </section>
          )}
        </QueryBoundary>

        <QueryBoundary
          query={dashboardQuery}
          loadingLabel="Loading weaknesses..."
          emptyTitle="No weakness drivers"
          isEmpty={(data) => data.top_negative_drivers.length === 0}
        >
          {(dashboard) => (
            <section className="card">
              <h2 className="text-sm font-semibold text-slate-900">Weaknesses</h2>
              <ul className="mt-3 space-y-2 text-sm text-slate-700">
                {dashboard.top_negative_drivers.map((driver) => (
                  <li key={driver}>{formatLabel(driver)}</li>
                ))}
              </ul>
            </section>
          )}
        </QueryBoundary>
      </div>
    </>
  );
}

function Metric({ label, value }: { label: string; value: string | null }) {
  return (
    <div>
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-sm font-medium text-slate-900">{formatPercent(value)}</p>
    </div>
  );
}
