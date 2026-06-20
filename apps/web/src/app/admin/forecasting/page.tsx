"use client";

import Link from "next/link";

import { GoalForecastingDashboard } from "@/components/admin/goal-forecasting-dashboard";
import { RoleGuard } from "@/components/auth/role-guard";
import { PageHeader } from "@/components/ui/page-header";

export default function AdminForecastingPage() {
  return (
    <RoleGuard allowed={["institute_admin", "super_admin"]}>
      <div className="mx-auto max-w-6xl space-y-6 p-4 sm:p-6">
        <PageHeader
          title="Goal forecasting"
          description="Forecast quality, scenario usage, goal attainment, and cohort projections."
          actions={
            <div className="flex gap-2">
              <Link href="/admin/cohort" className="btn-secondary">
                Cohort intelligence
              </Link>
              <Link href="/admin/planning" className="btn-secondary">
                Adaptive planning
              </Link>
              <Link href="/admin/memory" className="btn-secondary">
                Coaching memory
              </Link>
            </div>
          }
        />
        <GoalForecastingDashboard />
      </div>
    </RoleGuard>
  );
}
