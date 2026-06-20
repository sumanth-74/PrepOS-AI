"use client";

import Link from "next/link";

import { MentorInterventionQueueView } from "@/components/interventions/mentor-intervention-view";
import { PageHeader } from "@/components/ui/page-header";
import { QueryBoundary } from "@/components/ui/query-boundary";
import { useMentorInterventionQueue } from "@/hooks/use-intervention-queries";

export default function MentorInterventionsPage() {
  const queueQuery = useMentorInterventionQueue();

  return (
    <>
      <PageHeader
        title="Intervention queue"
        description="Students needing mentor intervention, ranked by priority, forecast risk, and predicted readiness impact."
      />
      <QueryBoundary
        query={queueQuery}
        loadingLabel="Loading intervention queue..."
        emptyTitle="Queue is empty"
        emptyDescription="Generate interventions for students to populate the priority queue."
        isEmpty={(data) => data.items.length === 0}
      >
        {(data) => (
          <div className="space-y-4">
            <MentorInterventionQueueView items={data.items} />
            <p className="text-sm text-slate-600">
              Open a student from{" "}
              <Link href="/mentor/queue" className="text-brand-700 underline">
                mentor queue
              </Link>{" "}
              to generate and track interventions.
            </p>
          </div>
        )}
      </QueryBoundary>
    </>
  );
}
