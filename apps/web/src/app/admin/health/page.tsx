"use client";

import Link from "next/link";

import { RoleGuard } from "@/components/auth/role-guard";
import { OpsHealthDashboard } from "@/components/admin/ops-health-dashboard";
import { PageHeader } from "@/components/ui/page-header";

export default function AdminHealthPage() {
  return (
    <RoleGuard allowed={["institute_admin", "super_admin"]}>
      <div className="mx-auto max-w-5xl space-y-6 p-4 sm:p-6">
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
      </div>
    </RoleGuard>
  );
}
