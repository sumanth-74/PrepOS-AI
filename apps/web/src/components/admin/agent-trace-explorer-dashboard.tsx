"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { adminAgentTracesApi } from "@/lib/api";
import type { AgentTraceRecord } from "@/lib/types/api";
import { useAuthStore } from "@/stores";

export function AgentTraceExplorerDashboard() {
  const token = useAuthStore((state) => state.accessToken);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);

  const listQuery = useQuery({
    queryKey: ["admin", "agent-traces"],
    queryFn: () => adminAgentTracesApi.list(token!),
    enabled: Boolean(token),
  });

  const detailQuery = useQuery({
    queryKey: ["admin", "agent-traces", selectedId],
    queryFn: () => adminAgentTracesApi.get(token!, selectedId!),
    enabled: Boolean(token && selectedId),
  });

  async function handleExport(traceId: string) {
    if (!token) return;
    setExporting(true);
    try {
      const payload = await adminAgentTracesApi.exportJson(token, traceId);
      const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `agent_trace_${traceId}.json`;
      anchor.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  }

  if (listQuery.isLoading) {
    return <p className="text-sm text-slate-600">Loading agent traces…</p>;
  }

  const traces = listQuery.data?.items ?? [];
  const detail: AgentTraceRecord | undefined = detailQuery.data;

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <section className="card overflow-x-auto">
        <h3 className="mb-3 text-sm font-semibold text-slate-900">Execution explorer</h3>
        <table className="min-w-full text-left text-sm">
          <thead className="border-b border-slate-200 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-2 py-2">Persona</th>
              <th className="px-2 py-2">Question</th>
              <th className="px-2 py-2">Latency</th>
              <th className="px-2 py-2">Confidence</th>
            </tr>
          </thead>
          <tbody>
            {traces.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-2 py-4 text-slate-500">
                  No traces recorded yet. Run copilot with agent_mode enabled.
                </td>
              </tr>
            ) : (
              traces.map((trace) => (
                <tr
                  key={trace.trace_id}
                  className={`cursor-pointer border-b border-slate-100 ${selectedId === trace.trace_id ? "bg-brand-50" : ""}`}
                  onClick={() => setSelectedId(trace.trace_id)}
                >
                  <td className="px-2 py-2">{trace.persona}</td>
                  <td className="max-w-xs truncate px-2 py-2">{trace.question}</td>
                  <td className="px-2 py-2">{trace.latency_ms} ms</td>
                  <td className="px-2 py-2">{trace.confidence}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>

      <section className="card space-y-4">
        <div className="flex items-center justify-between gap-2">
          <h3 className="text-sm font-semibold text-slate-900">Trace detail & DAG</h3>
          {selectedId ? (
            <button type="button" className="btn-secondary" disabled={exporting} onClick={() => handleExport(selectedId)}>
              Export JSON
            </button>
          ) : null}
        </div>
        {!detail ? (
          <p className="text-sm text-slate-500">Select a trace to inspect planner steps, tools, critiques, and reflections.</p>
        ) : (
          <>
            <p className="text-sm text-slate-700">{detail.answer}</p>
            <div className="space-y-2">
              {detail.steps.map((step) => (
                <div key={step.step_number} className="rounded-lg border border-slate-200 p-3">
                  <p className="text-xs font-semibold uppercase text-slate-500">
                    Step {step.step_number}: {step.agent_name}
                    {step.tool_name ? ` → ${step.tool_name}` : ""}
                  </p>
                  <p className="mt-1 text-xs text-slate-600">Status: {step.status}</p>
                </div>
              ))}
            </div>
            <div className="space-y-2">
              {detail.artifacts.map((artifact) => (
                <div key={artifact.artifact_type} className="rounded-lg bg-slate-50 p-3 text-xs text-slate-700">
                  <p className="font-semibold">{artifact.artifact_type}</p>
                </div>
              ))}
            </div>
          </>
        )}
      </section>
    </div>
  );
}
