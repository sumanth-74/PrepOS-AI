"use client";

import Link from "next/link";
import { PageHeader } from "@/components/ui/page-header";
import { QueryBoundary } from "@/components/ui/query-boundary";
import { StatusBadge } from "@/components/ui/status-badge";
import { useMentorQueue } from "@/hooks/use-mentor-queries";
import { formatLabel, formatScore } from "@/lib/utils/format";

export default function MentorQueuePage() {
  const queueQuery = useMentorQueue();

  return (
    <>
      <PageHeader
        title="Mentor Queue"
        description="Students requiring mentor attention, sorted by API priority."
      />
      <QueryBoundary
        query={queueQuery}
        loadingLabel="Loading queue..."
        emptyTitle="Queue is empty"
        emptyDescription="No students currently need mentor action."
        isEmpty={(data) => data.length === 0}
      >
        {(items) => (
          <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3">Student</th>
                  <th className="px-4 py-3">Action</th>
                  <th className="px-4 py-3">Priority</th>
                  <th className="px-4 py-3">Escalation</th>
                  <th className="px-4 py-3">Case</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.case_id} className="border-b border-slate-100">
                    <td className="px-4 py-3">
                      <Link
                        href={`/mentor/student/${item.student_id}`}
                        className="font-medium text-brand-700 hover:underline"
                      >
                        {item.student_id}
                      </Link>
                    </td>
                    <td className="px-4 py-3">{formatLabel(item.mentor_action)}</td>
                    <td className="px-4 py-3">{formatScore(item.priority_score)}</td>
                    <td className="px-4 py-3">
                      <StatusBadge label={formatLabel(item.escalation_level)} tone="warning" />
                    </td>
                    <td className="px-4 py-3">
                      <Link
                        href={`/mentor/cases/${item.case_id}`}
                        className="text-brand-700 hover:underline"
                      >
                        {formatLabel(item.case_status)}
                      </Link>
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
