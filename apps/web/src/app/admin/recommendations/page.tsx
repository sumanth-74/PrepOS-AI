"use client";

import Link from "next/link";

import { RecommendationAnalyticsDashboard } from "@/components/admin/recommendation-analytics-dashboard";
import { PageHeader } from "@/components/ui/page-header";

export default function AdminRecommendationsPage() {
  return (
    <>
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
    </>
  );
}
