"use client";

import { useQuery } from "@tanstack/react-query";

import { QueryBoundary } from "@/components/ui/query-boundary";
import { adminPlatformApi, adminSecurityApi } from "@/lib/api";
import { useAuthStore } from "@/stores";

function MetricCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}

export function SecurityDashboard() {
  const token = useAuthStore((state) => state.accessToken);
  const query = useQuery({
    queryKey: ["admin", "security", "dashboard"],
    queryFn: () => adminSecurityApi.dashboard(token!),
    enabled: Boolean(token),
  });

  return (
    <QueryBoundary
      query={query}
      loadingLabel="Loading security metrics…"
      emptyTitle="No security metrics"
      isEmpty={(data) => Object.keys(data).length === 0}
    >
      {(data) => {
        const dashboard = (data.dashboard ?? {}) as Record<string, unknown>;
        const totalAttacks = Number(dashboard.total_attacks ?? 0);
        const blockedAttacks = Number(dashboard.blocked_attacks ?? 0);
        const attackCategories = dashboard.attack_categories;
        const tenantDistribution = dashboard.tenant_distribution;
        return (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard label="Prompt attacks" value={totalAttacks} />
            <MetricCard label="Blocked attacks" value={blockedAttacks} />
            <MetricCard
              label="Attack categories"
              value={
                attackCategories && typeof attackCategories === "object"
                  ? Object.keys(attackCategories as Record<string, unknown>).length
                  : 0
              }
            />
            <MetricCard
              label="Tenants affected"
              value={
                tenantDistribution && typeof tenantDistribution === "object"
                  ? Object.keys(tenantDistribution as Record<string, unknown>).length
                  : 0
              }
            />
          </div>
        );
      }}
    </QueryBoundary>
  );
}

export function PlatformMaturityOverview() {
  const token = useAuthStore((state) => state.accessToken);
  const query = useQuery({
    queryKey: ["admin", "platform-readiness", "overview"],
    queryFn: () => adminPlatformApi.platformReadiness(token!),
    enabled: Boolean(token),
  });

  if (query.isLoading) {
    return <p className="text-sm text-slate-500">Loading readiness score…</p>;
  }

  if (query.isError || !query.data) {
    return null;
  }

  return (
    <div className="rounded-lg border border-brand-200 bg-brand-50 p-4">
      <p className="text-sm font-medium text-brand-900">Platform Readiness Score</p>
      <p className="text-3xl font-bold text-brand-800">{String(query.data.overall_score ?? "—")}</p>
    </div>
  );
}
