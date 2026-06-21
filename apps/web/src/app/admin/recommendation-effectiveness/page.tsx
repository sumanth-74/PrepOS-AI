"use client";

import Link from "next/link";

import { RecommendationEffectivenessDashboard } from "@/components/admin/recommendation-effectiveness-dashboard";
import { PageHeader } from "@/components/ui/page-header";

export default function AdminRecommendationEffectivenessPage() {
  return (
    <>
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
    </>
  );
}
