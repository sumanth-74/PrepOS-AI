"use client";

import Link from "next/link";

import { CohortIntelligenceDashboard } from "@/components/admin/cohort-intelligence-dashboard";
import { RoleGuard } from "@/components/auth/role-guard";
import { PageHeader } from "@/components/ui/page-header";

export default function AdminCohortPage() {
  return (
    <RoleGuard allowed={["institute_admin", "super_admin"]}>
      <div className="mx-auto max-w-6xl space-y-6 p-4 sm:p-6">
        <PageHeader
          title="Cohort intelligence"
          description="Institution health, segment distribution, risk areas, trends, and mentor comparison."
          actions={
            <div className="flex gap-2">
              <Link href="/admin/institution" className="btn-secondary">
                Institution intelligence
              </Link>
              <Link href="/admin/interventions" className="btn-secondary">
                Interventions
              </Link>
              <Link href="/admin/forecasting" className="btn-secondary">
                Forecasting
              </Link>
            </div>
          }
        />
        <CohortIntelligenceDashboard />
      </div>
    </RoleGuard>
  );
}
