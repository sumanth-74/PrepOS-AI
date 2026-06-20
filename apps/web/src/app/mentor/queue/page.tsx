"use client";

import { MentorQueueTable } from "@/components/mentor/queue-table";
import { PageHeader } from "@/components/ui/page-header";
import { QueryBoundary } from "@/components/ui/query-boundary";
import { useMentorQueue } from "@/hooks/use-mentor-queries";

export default function MentorQueuePage() {
  const queueQuery = useMentorQueue();

  return (
    <>
      <PageHeader
        title="Mentor Queue"
        description="Students requiring mentor attention, sorted by priority."
      />
      <QueryBoundary
        query={queueQuery}
        loadingLabel="Loading queue..."
        emptyTitle="Queue is empty"
        emptyDescription="No students currently need mentor action."
        isEmpty={(data) => data.length === 0}
      >
        {(items) => <MentorQueueTable items={items} />}
      </QueryBoundary>
    </>
  );
}
