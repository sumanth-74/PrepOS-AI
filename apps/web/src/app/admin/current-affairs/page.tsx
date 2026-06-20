"use client";

import Link from "next/link";

import { RoleGuard } from "@/components/auth/role-guard";
import { CurrentAffairsOperationsDashboard } from "@/components/admin/current-affairs-operations-dashboard";
import { PageHeader } from "@/components/ui/page-header";

export default function AdminCurrentAffairsPage() {
  return (
    <RoleGuard allowed={["institute_admin", "super_admin"]}>
      <div className="mx-auto max-w-6xl space-y-6 p-4 sm:p-6">
        <PageHeader
          title="Current affairs operations"
          description="Upload, index, and explore UPSC current affairs sources with recency-aware retrieval."
          actions={
            <Link href="/admin/knowledge" className="btn-secondary">
              Knowledge operations
            </Link>
          }
        />
        <CurrentAffairsOperationsDashboard />
      </div>
    </RoleGuard>
  );
}
