"use client";

import { useMutation, useQuery } from "@tanstack/react-query";

import { PageHeader } from "@/components/ui/page-header";
import { QueryBoundary } from "@/components/ui/query-boundary";
import { adminSecurityApi } from "@/lib/api";
import { useAuthStore } from "@/stores";

export default function AdminTenantAuditPage() {
  const token = useAuthStore((state) => state.accessToken);
  const auditQuery = useQuery({
    queryKey: ["admin", "security", "tenant-audit"],
    queryFn: () => adminSecurityApi.tenantAudits(token!),
    enabled: Boolean(token),
  });

  const runAuditMutation = useMutation({
    mutationFn: () => adminSecurityApi.runTenantAudit(token!, "full"),
    onSuccess: () => void auditQuery.refetch(),
  });

  return (
    <>
      <PageHeader
        title="Tenant audit"
        description="Cross-tenant security posture, isolation checks, and compliance snapshots."
        actions={
          <button
            type="button"
            className="btn-primary"
            disabled={runAuditMutation.isPending}
            onClick={() => runAuditMutation.mutate()}
          >
            {runAuditMutation.isPending ? "Running audit…" : "Run full audit"}
          </button>
        }
      />
      <QueryBoundary
        query={auditQuery}
        loadingLabel="Loading tenant audits…"
        emptyTitle="No tenant audits yet"
        emptyDescription="Run a full audit to generate the first report."
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
