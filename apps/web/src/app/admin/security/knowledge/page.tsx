"use client";

import { useQuery } from "@tanstack/react-query";

import { PageHeader } from "@/components/ui/page-header";
import { QueryBoundary } from "@/components/ui/query-boundary";
import { adminSecurityApi } from "@/lib/api";
import { useAuthStore } from "@/stores";

export default function AdminKnowledgeSecurityPage() {
  const token = useAuthStore((state) => state.accessToken);
  const query = useQuery({
    queryKey: ["admin", "security", "knowledge"],
    queryFn: () => adminSecurityApi.knowledgeSecurity(token!),
    enabled: Boolean(token),
  });

  return (
    <>
      <PageHeader
        title="Knowledge security"
        description="Scan results, blocked uploads, and sensitive content detections."
      />
      <QueryBoundary
        query={query}
        loadingLabel="Loading knowledge security metrics…"
        emptyTitle="No knowledge security events"
        emptyDescription="Upload scans will appear here when sources are ingested."
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
