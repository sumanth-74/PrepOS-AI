"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { adminAgentHealthApi } from "@/lib/api";
import { RoleGuard } from "@/components/auth/role-guard";
import { PageHeader } from "@/components/ui/page-header";
import { useAuthStore } from "@/stores";

export default function AdminAgentHealthPage() {
  const token = useAuthStore((state) => state.accessToken);
  const query = useQuery({
    queryKey: ["admin", "agent-health"],
    queryFn: () => adminAgentHealthApi.leaderboard(token!),
    enabled: Boolean(token),
  });

  return (
    <RoleGuard allowed={["institute_admin", "super_admin"]}>
      <div className="mx-auto max-w-6xl space-y-6 p-4 sm:p-6">
        <PageHeader
          title="Agent health monitoring"
          description="Reliability leaderboard with failures, latency, confidence, satisfaction, and cost."
          actions={
            <Link href="/admin/agents" className="btn-secondary">
              Orchestration dashboard
            </Link>
          }
        />
        <section className="card overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-2 py-2">Agent</th>
                <th className="px-2 py-2">Executions</th>
                <th className="px-2 py-2">Failures</th>
                <th className="px-2 py-2">Latency</th>
                <th className="px-2 py-2">Confidence</th>
                <th className="px-2 py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {(query.data?.agents ?? []).map((agent) => (
                <tr key={agent.agent_type} className="border-b border-slate-100">
                  <td className="px-2 py-2">{agent.agent_type}</td>
                  <td className="px-2 py-2">{agent.executions}</td>
                  <td className="px-2 py-2">{agent.failures}</td>
                  <td className="px-2 py-2">{agent.average_latency_ms} ms</td>
                  <td className="px-2 py-2">{(agent.average_confidence_score * 100).toFixed(0)}%</td>
                  <td className="px-2 py-2">{agent.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>
    </RoleGuard>
  );
}
