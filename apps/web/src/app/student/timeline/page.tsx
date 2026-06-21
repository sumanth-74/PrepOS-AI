"use client";

import { useQuery } from "@tanstack/react-query";

import { PageHeader } from "@/components/ui/page-header";
import { QueryBoundary } from "@/components/ui/query-boundary";
import { studentTimelineApi } from "@/lib/api";
import { useAuthStore } from "@/stores";

export default function StudentTimelinePage() {
  const token = useAuthStore((state) => state.accessToken);
  const timelineQuery = useQuery({
    queryKey: ["memory", "student", "timeline"],
    queryFn: () => studentTimelineApi.get(token!),
    enabled: Boolean(token),
  });

  return (
    <>
      <PageHeader
        title="Learning timeline"
        description="Chronological journey of readiness, recommendations, plans, forecasts, and milestones."
      />
      <QueryBoundary
        query={timelineQuery}
        loadingLabel="Loading learning timeline…"
        emptyTitle="No timeline events yet"
        emptyDescription="Keep learning with Copilot to build your journey."
        isEmpty={(data) => data.events.length === 0}
      >
        {(data) => (
          <ol className="space-y-3">
            {data.events.map((event, index) => (
              <li
                key={`${String(event.occurred_at)}-${index}`}
                className="rounded-lg border border-slate-200 bg-white p-4"
              >
                <p className="text-xs font-semibold uppercase text-brand-700">
                  {String(event.event_type ?? "event")}
                </p>
                <p className="mt-1 text-sm text-slate-800">{String(event.summary ?? "")}</p>
                <p className="mt-1 text-xs text-slate-500">{String(event.occurred_at ?? "")}</p>
              </li>
            ))}
          </ol>
        )}
      </QueryBoundary>
    </>
  );
}
