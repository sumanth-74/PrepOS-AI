"use client";

import Link from "next/link";

import { AgentTraceExplorerDashboard } from "@/components/admin/agent-trace-explorer-dashboard";
import { PageHeader } from "@/components/ui/page-header";

export default function AdminAgentTracesPage() {
  return (
    <>
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
    </>
  );
}
