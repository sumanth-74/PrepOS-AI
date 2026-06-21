"use client";

import { useQuery } from "@tanstack/react-query";

import { PageHeader } from "@/components/ui/page-header";
import { QueryBoundary } from "@/components/ui/query-boundary";
import { adminSecurityApi } from "@/lib/api";
import { useAuthStore } from "@/stores";

export default function AdminRateLimitsPage() {
  const token = useAuthStore((state) => state.accessToken);
  const query = useQuery({
    queryKey: ["admin", "security", "rate-limits"],
    queryFn: () => adminSecurityApi.rateLimits(token!),
    enabled: Boolean(token),
  });

  return (
    <>
      <PageHeader
        title="Rate limits"
        description="Tenant-level throttling, burst usage, and blocked request telemetry."
      />
      <QueryBoundary
        query={query}
        loadingLabel="Loading rate limit metrics…"
        emptyTitle="No rate limit data"
        emptyDescription="Rate limit telemetry appears after traffic is observed."
        isEmpty={(data) => Object.keys(data).length === 0}
      >
        {(data) => (
          <pre className="overflow-x-auto rounded-lg border border-slate-200 bg-slate-50 p-4 text-xs text-slate-700">
            {JSON.stringify(data, null, 2)}
          </pre>
        )}
      </QueryBoundary>
    </>
  );
}
