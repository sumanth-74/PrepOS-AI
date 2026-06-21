"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { adminAgentCostsApi } from "@/lib/api";
import { PageHeader } from "@/components/ui/page-header";
import { QueryBoundary } from "@/components/ui/query-boundary";
import { useAuthStore } from "@/stores";

export default function AdminAgentCostsPage() {
  const token = useAuthStore((state) => state.accessToken);
  const query = useQuery({
    queryKey: ["admin", "agent-costs"],
    queryFn: () => adminAgentCostsApi.dashboard(token!),
    enabled: Boolean(token),
  });

  return (
    <>
      <PageHeader
        title="Agent cost intelligence"
        description="Daily spend, cost per query, slow workflows, and highest-cost agents."
        actions={
          <Link href="/admin/agent-traces" className="btn-secondary">
            Trace explorer
          </Link>
        }
      />
      <QueryBoundary
        query={query}
        loadingLabel="Loading cost dashboard…"
        emptyTitle="No cost data"
        isEmpty={(data) => Object.keys(data).length === 0}
      >
        {(data) => (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <div className="card">
              <p className="text-xs uppercase text-slate-500">Daily cost</p>
              <p className="mt-1 text-2xl font-semibold">${data.daily_cost.toFixed(4)}</p>
            </div>
            <div className="card">
              <p className="text-xs uppercase text-slate-500">Cost per query</p>
              <p className="mt-1 text-2xl font-semibold">${data.cost_per_query.toFixed(4)}</p>
            </div>
            <div className="card">
              <p className="text-xs uppercase text-slate-500">Queries (24h)</p>
              <p className="mt-1 text-2xl font-semibold">{data.total_queries}</p>
            </div>
          </div>
        )}
      </QueryBoundary>
    </>
  );
}
