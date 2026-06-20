"use client";

import Link from "next/link";

import { AdaptivePlanningDashboard } from "@/components/admin/adaptive-planning-dashboard";
import { RoleGuard } from "@/components/auth/role-guard";
import { PageHeader } from "@/components/ui/page-header";

export default function AdminPlanningPage() {
  return (
    <RoleGuard allowed={["institute_admin", "super_admin"]}>
      <div className="mx-auto max-w-6xl space-y-6 p-4 sm:p-6">
        <PageHeader
          title="Adaptive planning"
          description="Weekly plan generation, adherence, completion, and forecast analytics."
          actions={
            <div className="flex gap-2">
              <Link href="/admin/recommendations" className="btn-secondary">
                Recommendations
              </Link>
              <Link href="/admin/memory" className="btn-secondary">
                Coaching memory
              </Link>
              <Link href="/admin/forecasting" className="btn-secondary">
                Goal forecasting
              </Link>
              <Link href="/admin/interventions" className="btn-secondary">
                Interventions
              </Link>
              <Link href="/admin/cohort" className="btn-secondary">
                Cohort intelligence
              </Link>
            </div>
          }
        />
        <AdaptivePlanningDashboard />
      </div>
    </RoleGuard>
  );
}
