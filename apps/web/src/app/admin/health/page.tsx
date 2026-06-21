"use client";

import Link from "next/link";

import { OpsHealthDashboard } from "@/components/admin/ops-health-dashboard";
import { PageHeader } from "@/components/ui/page-header";

export default function AdminHealthPage() {
  return (
    <>
        <PageHeader
          title="Platform health"
          description="Operational status for API, database, Redis, Celery workers, and outbox backlog."
          actions={
            <div className="flex flex-wrap gap-2">
              <Link href="/admin/knowledge" className="btn-secondary">
                Knowledge operations
              </Link>
              <Link href="/admin/copilot" className="btn-secondary">
                Copilot analytics
              </Link>
            </div>
          }
        />
        <OpsHealthDashboard />
    </>
  );
}
