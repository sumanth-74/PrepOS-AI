"use client";

import Link from "next/link";

import { RagQualityDashboard } from "@/components/admin/rag-quality-dashboard";
import { RoleGuard } from "@/components/auth/role-guard";
import { PageHeader } from "@/components/ui/page-header";

export default function AdminRagQualityPage() {
  return (
    <RoleGuard allowed={["institute_admin", "super_admin"]}>
      <div className="mx-auto max-w-6xl space-y-6 p-4 sm:p-6">
        <PageHeader
          title="RAG quality monitoring"
          description="Track retrieval quality, citation coverage, faithfulness, and hallucination risk for Knowledge Agent answers."
          actions={
            <div className="flex gap-2">
              <Link href="/admin/knowledge" className="btn-secondary">
                Knowledge
              </Link>
              <Link href="/admin/copilot" className="btn-secondary">
                Copilot analytics
              </Link>
            </div>
          }
        />
        <RagQualityDashboard />
      </div>
    </RoleGuard>
  );
}
