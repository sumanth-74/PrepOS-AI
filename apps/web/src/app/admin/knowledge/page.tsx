"use client";

import Link from "next/link";

import { KnowledgeOperationsDashboard } from "@/components/admin/knowledge-operations-dashboard";
import { PageHeader } from "@/components/ui/page-header";

export default function AdminKnowledgePage() {
  return (
    <>
        <PageHeader
          title="Knowledge operations"
          description="Upload, monitor, and manage institute knowledge sources for retrieval."
          actions={
            <div className="flex gap-2">
              <Link href="/admin/rag-quality" className="btn-secondary">
                RAG quality
              </Link>
              <Link href="/admin/pyq" className="btn-secondary">
                PYQ intelligence
              </Link>
              <Link href="/admin/current-affairs" className="btn-secondary">
                Current affairs
              </Link>
            </div>
          }
        />
        <KnowledgeOperationsDashboard />
    </>
  );
}
