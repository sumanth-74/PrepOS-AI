"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { adminAgentsApi } from "@/lib/api";
import type { AgentAdminDashboardResponse } from "@/lib/types/api";
import { useAuthStore } from "@/stores";

function KpiTile({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <div className="card">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
      {hint ? <p className="mt-1 text-xs text-slate-500">{hint}</p> : null}
    </div>
  );
}

function UsageBars({ title, items }: { title: string; items: Record<string, number> }) {
  const entries = Object.entries(items).sort((left, right) => right[1] - left[1]);
  const max = Math.max(...entries.map(([, value]) => value), 1);

  return (
    <div className="card space-y-3">
      <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
      {entries.length === 0 ? (
        <p className="text-sm text-slate-500">No usage recorded yet.</p>
      ) : (
        entries.map(([label, value]) => (
          <div key={label}>
            <div className="mb-1 flex items-center justify-between gap-2 text-xs text-slate-600">
              <span className="truncate">{label}</span>
              <span>{value}</span>
            </div>
            <div className="h-2 rounded-full bg-slate-100">
              <div className="h-2 rounded-full bg-brand-600" style={{ width: `${Math.max(4, (value / max) * 100)}%` }} />
            </div>
          </div>
        ))
      )}
    </div>
  );
}

export function AgentOrchestrationDashboard() {
  const token = useAuthStore((state) => state.accessToken);
  const [exporting, setExporting] = useState(false);

  const dashboardQuery = useQuery({
    queryKey: ["admin", "agents", "dashboard"],
    queryFn: () => adminAgentsApi.dashboard(token!),
    enabled: Boolean(token),
    refetchInterval: 60_000,
  });

  async function handleExport() {
    if (!token) {
      return;
    }
    setExporting(true);
    try {
      const csv = await adminAgentsApi.exportCsv(token);
      const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "agent_executions.csv";
      anchor.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  }

  if (dashboardQuery.isLoading) {
    return <p className="text-sm text-slate-600">Loading agent orchestration analytics…</p>;
  }

  if (dashboardQuery.isError || !dashboardQuery.data) {
    return (
      <div className="card border-red-200 bg-red-50">
        <p className="text-sm text-red-800">Unable to load agent orchestration dashboard.</p>
      </div>
    );
  }

  const data: AgentAdminDashboardResponse = dashboardQuery.data;

  return (
    <div className="space-y-6">
      <section className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-sm text-slate-600">
            Audit agent executions, workflows, confidence, and tool usage across the orchestration layer.
          </p>
        </div>
        <button type="button" className="btn-secondary" disabled={exporting} onClick={handleExport}>
          {exporting ? "Exporting…" : "Export CSV"}
        </button>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiTile label="Total executions" value={data.total_executions} />
        <KpiTile label="Executions (30d)" value={data.executions_last_30_days} />
        <KpiTile
          label="Success rate"
          value={`${(data.success_rate * 100).toFixed(1)}%`}
          hint="Completed agent runs without tool failures"
        />
        <KpiTile
          label="Average confidence"
          value={`${(data.average_confidence_score * 100).toFixed(1)}%`}
          hint="Normalized high/medium/low confidence"
        />
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <UsageBars title="Agent usage" items={data.agent_usage} />
        <UsageBars title="Tool usage" items={data.tool_usage} />
        <UsageBars title="Workflow counts" items={data.workflow_counts} />
      </section>

      <section className="card overflow-x-auto">
        <h3 className="mb-3 text-sm font-semibold text-slate-900">Recent executions</h3>
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-slate-200 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-2 py-2">Agent</th>
              <th className="px-2 py-2">Persona</th>
              <th className="px-2 py-2">Confidence</th>
              <th className="px-2 py-2">Success</th>
              <th className="px-2 py-2">Duration (ms)</th>
              <th className="px-2 py-2">Created</th>
            </tr>
          </thead>
          <tbody>
            {data.recent_executions.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-2 py-4 text-slate-500">
                  No agent executions recorded yet.
                </td>
              </tr>
            ) : (
              data.recent_executions.map((execution) => (
                <tr key={execution.execution_id} className="border-b border-slate-100">
                  <td className="px-2 py-2">{execution.agent_type}</td>
                  <td className="px-2 py-2">{execution.persona}</td>
                  <td className="px-2 py-2">{execution.confidence}</td>
                  <td className="px-2 py-2">{execution.success ? "Yes" : "No"}</td>
                  <td className="px-2 py-2">{execution.execution_time_ms}</td>
                  <td className="px-2 py-2">{new Date(execution.created_at).toLocaleString()}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>
    </div>
  );
}
