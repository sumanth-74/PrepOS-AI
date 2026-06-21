"use client";

import Link from "next/link";

import { CoachingMemoryDashboard } from "@/components/admin/coaching-memory-dashboard";
import { PageHeader } from "@/components/ui/page-header";

export default function AdminMemoryPage() {
  return (
    <>
        <PageHeader
          title="Coaching memory"
          description="Structured, auditable coaching memory for student and mentor copilot continuity."
          actions={
            <div className="flex gap-2">
              <Link href="/admin/recommendations" className="btn-secondary">
                Recommendations
              </Link>
              <Link href="/admin/recommendation-effectiveness" className="btn-secondary">
                Effectiveness
              </Link>
              <Link href="/admin/copilot" className="btn-secondary">
                Copilot analytics
              </Link>
            </div>
          }
        />
        <CoachingMemoryDashboard />
    </>
  );
}
