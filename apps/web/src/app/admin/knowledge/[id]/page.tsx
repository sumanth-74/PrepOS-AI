"use client";

import Link from "next/link";
import { use } from "react";

import { RoleGuard } from "@/components/auth/role-guard";
import { KnowledgeSourceDetail } from "@/components/admin/knowledge-source-detail";
import { PageHeader } from "@/components/ui/page-header";

interface AdminKnowledgeDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function AdminKnowledgeDetailPage({ params }: AdminKnowledgeDetailPageProps) {
  const { id } = use(params);

  return (
    <RoleGuard allowed={["institute_admin", "super_admin"]}>
      <div className="mx-auto max-w-4xl space-y-6 p-4 sm:p-6">
        <PageHeader
          title="Knowledge source"
          description="Ingestion status, chunk metrics, and indexing progress."
          actions={
            <Link href="/admin/knowledge" className="btn-secondary">
              All sources
            </Link>
          }
        />
        <KnowledgeSourceDetail sourceId={id} />
      </div>
    </RoleGuard>
  );
}
