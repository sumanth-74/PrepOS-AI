"use client";

import Link from "next/link";

import { CoachingMemoryDashboard } from "@/components/admin/coaching-memory-dashboard";
import { RoleGuard } from "@/components/auth/role-guard";
import { PageHeader } from "@/components/ui/page-header";

export default function AdminMemoryPage() {
  return (
    <RoleGuard allowed={["institute_admin", "super_admin"]}>
      <div className="mx-auto max-w-6xl space-y-6 p-4 sm:p-6">
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
      </div>
    </RoleGuard>
  );
}
