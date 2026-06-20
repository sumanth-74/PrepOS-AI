"use client";

import { useQuery } from "@tanstack/react-query";

import { adminMemoryApi } from "@/lib/api";
import type { MemoryAdminResponse } from "@/lib/types/api";
import { useAuthStore } from "@/stores";

function KpiTile({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="card">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}

export function CoachingMemoryDashboard() {
  const token = useAuthStore((state) => state.accessToken);
  const dashboardQuery = useQuery({
    queryKey: ["admin", "coaching-memory"],
    queryFn: () => adminMemoryApi.dashboard(token!),
    enabled: Boolean(token),
    refetchInterval: 30_000,
  });

  const handleExport = async () => {
    if (!token) return;
    const csv = await adminMemoryApi.exportCsv(token);
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "coaching_memory.csv";
    anchor.click();
    URL.revokeObjectURL(url);
  };

  if (dashboardQuery.isLoading) {
    return <p className="text-sm text-slate-600">Loading coaching memory analytics…</p>;
  }

  const data: MemoryAdminResponse | undefined = dashboardQuery.data;

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <button type="button" className="btn-secondary" onClick={() => void handleExport()}>
          Export CSV
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiTile label="Total memories" value={data?.total_memories ?? 0} />
        <KpiTile label="Growth (30 days)" value={data?.memory_growth_last_30_days ?? 0} />
        <KpiTile label="Milestones" value={data?.milestone_count ?? 0} />
        <KpiTile
          label="Last rebuild"
          value={data?.last_rebuild_at ? new Date(data.last_rebuild_at).toLocaleString() : "Never"}
        />
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-slate-900">Top memory types</h2>
        <ul className="mt-3 space-y-2 text-sm text-slate-700">
          {(data?.top_memory_types ?? []).map((item) => (
            <li key={String(item.memory_type)} className="flex justify-between gap-4">
              <span>{String(item.memory_type)}</span>
              <span className="font-medium">{String(item.count ?? 0)}</span>
            </li>
          ))}
          {(data?.top_memory_types ?? []).length === 0 ? (
            <li className="text-slate-500">No memories recorded yet. Run a rebuild to populate coaching memory.</li>
          ) : null}
        </ul>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-slate-900">Memory quality checks</h2>
        <ul className="mt-3 space-y-1 text-sm text-slate-700">
          <li>
            Structured memory types:{" "}
            {(data?.top_memory_types ?? []).length > 0 ? "pass" : "needs rebuild"}
          </li>
          <li>Milestone coverage: {data?.milestone_count ? "pass" : "no milestones yet"}</li>
          <li>
            Rebuild freshness:{" "}
            {data?.last_rebuild_at ? "recent rebuild recorded" : "no rebuild recorded in this session"}
          </li>
        </ul>
      </div>
    </div>
  );
}
