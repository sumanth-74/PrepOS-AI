"use client";

import Link from "next/link";

import { InstitutionOutcomeDashboard } from "@/components/admin/institution-outcome-dashboard";
import { PageHeader } from "@/components/ui/page-header";

export default function AdminInstitutionOutcomesPage() {
  return (
    <>
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
    </>
  );
}
