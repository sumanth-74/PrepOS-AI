"use client";

import Link from "next/link";

import { RecommendationAnalyticsDashboard } from "@/components/admin/recommendation-analytics-dashboard";
import { RoleGuard } from "@/components/auth/role-guard";
import { PageHeader } from "@/components/ui/page-header";

export default function AdminRecommendationsPage() {
  return (
    <RoleGuard allowed={["institute_admin", "super_admin"]}>
      <div className="mx-auto max-w-6xl space-y-6 p-4 sm:p-6">
        <PageHeader
          title="Recommendation analytics"
          description="Track recommendation acceptance, completion, readiness gains, and concept effectiveness."
          actions={
            <div className="flex gap-2">
              <Link href="/admin/recommendation-effectiveness" className="btn-secondary">
                Effectiveness
              </Link>
              <Link href="/admin/memory" className="btn-secondary">
                Coaching memory
              </Link>
              <Link href="/admin/planning" className="btn-secondary">
                Adaptive planning
              </Link>
              <Link href="/admin/copilot" className="btn-secondary">
                Copilot analytics
              </Link>
              <Link href="/admin/rag-quality" className="btn-secondary">
                RAG quality
              </Link>
            </div>
          }
        />
        <RecommendationAnalyticsDashboard />
      </div>
    </RoleGuard>
  );
}
