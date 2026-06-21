"use client";

import Link from "next/link";

import { InterventionOptimizationDashboard } from "@/components/admin/intervention-optimization-dashboard";
import { PageHeader } from "@/components/ui/page-header";

export default function AdminInterventionsPage() {
  return (
    <>
        <PageHeader
          title="Intervention optimization"
          description="Mentor intervention effectiveness, ROI, success rates, and cohort analytics."
          actions={
            <div className="flex gap-2">
              <Link href="/admin/cohort" className="btn-secondary">
                Cohort intelligence
              </Link>
              <Link href="/admin/forecasting" className="btn-secondary">
                Goal forecasting
              </Link>
              <Link href="/admin/planning" className="btn-secondary">
                Adaptive planning
              </Link>
            </div>
          }
        />
        <InterventionOptimizationDashboard />
    </>
  );
}
