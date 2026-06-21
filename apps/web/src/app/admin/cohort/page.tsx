"use client";

import Link from "next/link";

import { CohortIntelligenceDashboard } from "@/components/admin/cohort-intelligence-dashboard";
import { PageHeader } from "@/components/ui/page-header";

export default function AdminCohortPage() {
  return (
    <>
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
    </>
  );
}
