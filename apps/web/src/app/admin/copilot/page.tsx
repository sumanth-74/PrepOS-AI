"use client";

import Link from "next/link";

import { CopilotAnalyticsDashboard } from "@/components/admin/copilot-analytics-dashboard";
import { PageHeader } from "@/components/ui/page-header";

export default function AdminCopilotPage() {
  return (
    <>
        <PageHeader
          title="Copilot analytics"
          description="Measure copilot adoption, intent coverage, and RAG investment signals."
          actions={
            <div className="flex flex-wrap gap-2">
              <Link href="/admin/knowledge" className="btn-secondary">
                Knowledge operations
              </Link>
              <Link href="/admin/health" className="btn-secondary">
                Platform health
              </Link>
              <Link href="/admin/agents" className="btn-secondary">
                Agent orchestration
              </Link>
            </div>
          }
        />
        <CopilotAnalyticsDashboard />
    </>
  );
}
