"use client";

import Link from "next/link";

import { InstitutionOutcomeDashboard } from "@/components/admin/institution-outcome-dashboard";
import { RoleGuard } from "@/components/auth/role-guard";
import { PageHeader } from "@/components/ui/page-header";

export default function AdminInstitutionOutcomesPage() {
  return (
    <RoleGuard allowed={["institute_admin", "super_admin"]}>
      <div className="mx-auto max-w-6xl space-y-6 p-4 sm:p-6">
        <PageHeader
          title="Institution outcomes & ROI"
          description="Measure initiative effectiveness, readiness uplift, forecast gains, and institutional ROI."
          actions={
            <div className="flex flex-wrap gap-2">
              <Link href="/admin/institution" className="btn-secondary">
                Institution intelligence
              </Link>
              <Link href="/admin/cohort" className="btn-secondary">
                Cohort intelligence
              </Link>
            </div>
          }
        />
        <InstitutionOutcomeDashboard />
      </div>
    </RoleGuard>
  );
}
