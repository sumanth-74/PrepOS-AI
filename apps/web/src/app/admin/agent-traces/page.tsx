"use client";

import Link from "next/link";

import { AgentTraceExplorerDashboard } from "@/components/admin/agent-trace-explorer-dashboard";
import { RoleGuard } from "@/components/auth/role-guard";
import { PageHeader } from "@/components/ui/page-header";

export default function AdminAgentTracesPage() {
  return (
    <RoleGuard allowed={["institute_admin", "super_admin"]}>
      <div className="mx-auto max-w-6xl space-y-6 p-4 sm:p-6">
        <PageHeader
          title="Agent trace explorer"
          description="Inspect planner decisions, multi-agent DAG execution, critiques, reflections, and export JSON traces."
          actions={
            <div className="flex flex-wrap gap-2">
              <Link href="/admin/agents" className="btn-secondary">
                Agent orchestration
              </Link>
              <Link href="/admin/agent-costs" className="btn-secondary">
                Cost intelligence
              </Link>
            </div>
          }
        />
        <AgentTraceExplorerDashboard />
      </div>
    </RoleGuard>
  );
}
