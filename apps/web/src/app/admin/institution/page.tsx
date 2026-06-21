"use client";

import Link from "next/link";

import { InstitutionIntelligenceDashboard } from "@/components/admin/institution-intelligence-dashboard";
import { PageHeader } from "@/components/ui/page-header";

export default function AdminInstitutionPage() {
  return (
    <>
        <PageHeader
          title="Institution intelligence"
          description="Executive insights, cohort comparisons, mentor effectiveness, trends, and actionable recommendations."
          actions={
            <div className="flex flex-wrap gap-2">
              <Link href="/admin/institution/outcomes" className="btn-secondary">
                Outcomes & ROI
              </Link>
              <Link href="/admin/cohort" className="btn-secondary">
                Cohort intelligence
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
        <InstitutionIntelligenceDashboard />
    </>
  );
}
