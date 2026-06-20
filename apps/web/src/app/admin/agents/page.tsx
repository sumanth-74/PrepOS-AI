"use client";

import Link from "next/link";

import { AgentOrchestrationDashboard } from "@/components/admin/agent-orchestration-dashboard";
import { RoleGuard } from "@/components/auth/role-guard";
import { PageHeader } from "@/components/ui/page-header";

export default function AdminAgentsPage() {
  return (
    <RoleGuard allowed={["institute_admin", "super_admin"]}>
      <div className="mx-auto max-w-6xl space-y-6 p-4 sm:p-6">
        <PageHeader
          title="Agent orchestration"
          description="Monitor planner decisions, tool invocations, workflow triggers, and execution audit trails."
          actions={
            <div className="flex flex-wrap gap-2">
              <Link href="/admin/agent-traces" className="btn-secondary">
                Trace explorer
              </Link>
              <Link href="/admin/agents/health" className="btn-secondary">
                Agent health
              </Link>
              <Link href="/admin/agent-costs" className="btn-secondary">
                Cost intelligence
              </Link>
              <Link href="/admin/approvals" className="btn-secondary">
                Approvals
              </Link>
              <Link href="/admin/copilot" className="btn-secondary">
                Copilot analytics
              </Link>
            </div>
          }
        />
        <AgentOrchestrationDashboard />
      </div>
    </RoleGuard>
  );
}
