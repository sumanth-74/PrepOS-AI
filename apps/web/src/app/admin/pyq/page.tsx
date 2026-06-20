"use client";

import Link from "next/link";

import { PyqOperationsDashboard } from "@/components/admin/pyq-operations-dashboard";
import { RoleGuard } from "@/components/auth/role-guard";
import { PageHeader } from "@/components/ui/page-header";

export default function AdminPyqPage() {
  return (
    <RoleGuard allowed={["institute_admin", "super_admin"]}>
      <div className="mx-auto max-w-6xl space-y-6 p-4 sm:p-6">
        <PageHeader
          title="PYQ intelligence"
          description="Upload previous year questions, review concept mappings, and monitor PYQ retrieval analytics."
          actions={
            <div className="flex gap-2">
              <Link href="/admin/knowledge" className="btn-secondary">
                Knowledge
              </Link>
              <Link href="/admin/current-affairs" className="btn-secondary">
                Current affairs
              </Link>
            </div>
          }
        />
        <PyqOperationsDashboard />
      </div>
    </RoleGuard>
  );
}
