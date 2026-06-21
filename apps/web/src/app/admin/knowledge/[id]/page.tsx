"use client";

import Link from "next/link";
import { use } from "react";

import { KnowledgeSourceDetail } from "@/components/admin/knowledge-source-detail";
import { PageHeader } from "@/components/ui/page-header";

interface AdminKnowledgeDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function AdminKnowledgeDetailPage({ params }: AdminKnowledgeDetailPageProps) {
  const { id } = use(params);

  return (
    <>
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
    </>
  );
}
