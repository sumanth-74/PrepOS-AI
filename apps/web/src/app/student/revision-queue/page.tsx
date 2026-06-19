"use client";

import { PageHeader } from "@/components/ui/page-header";
import { QueryBoundary } from "@/components/ui/query-boundary";
import { StatusBadge } from "@/components/ui/status-badge";
import { useRevisionQueue } from "@/hooks/use-student-queries";
import { formatLabel, formatScore } from "@/lib/utils/format";

export default function RevisionQueuePage() {
  const queueQuery = useRevisionQueue();

  return (
    <>
      <PageHeader
        title="Revision Queue"
        description="Concepts due for spaced revision."
      />
      <QueryBoundary
        query={queueQuery}
        loadingLabel="Loading revision queue..."
        emptyTitle="Revision queue is empty"
        emptyDescription="You're caught up on revisions."
        isEmpty={(data) => data.length === 0}
      >
        {(items) => (
          <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3">Concept</th>
                  <th className="px-4 py-3">Due</th>
                  <th className="px-4 py-3">Retention</th>
                  <th className="px-4 py-3">Priority</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.concept_id} className="border-b border-slate-100">
                    <td className="px-4 py-3 font-medium">{item.concept_id}</td>
                    <td className="px-4 py-3">{item.next_review_at}</td>
                    <td className="px-4 py-3">{formatScore(item.retention_score)}</td>
                    <td className="px-4 py-3">{formatScore(item.priority_score)}</td>
                    <td className="px-4 py-3">
                      <StatusBadge label={formatLabel(item.status)} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </QueryBoundary>
    </>
  );
}
