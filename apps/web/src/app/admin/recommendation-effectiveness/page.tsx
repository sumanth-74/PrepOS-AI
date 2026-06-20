"use client";

import Link from "next/link";

import { RecommendationEffectivenessDashboard } from "@/components/admin/recommendation-effectiveness-dashboard";
import { RoleGuard } from "@/components/auth/role-guard";
import { PageHeader } from "@/components/ui/page-header";

export default function AdminRecommendationEffectivenessPage() {
  return (
    <RoleGuard allowed={["institute_admin", "super_admin"]}>
      <div className="mx-auto max-w-6xl space-y-6 p-4 sm:p-6">
        <PageHeader
          title="Recommendation effectiveness"
          description="Measure whether recommendations improve readiness, forecast, and concept mastery."
          actions={
            <div className="flex gap-2">
              <Link href="/admin/recommendations" className="btn-secondary">
                Recommendations
              </Link>
              <Link href="/admin/copilot" className="btn-secondary">
                Copilot analytics
              </Link>
            </div>
          }
        />
        <RecommendationEffectivenessDashboard />
      </div>
    </RoleGuard>
  );
}
