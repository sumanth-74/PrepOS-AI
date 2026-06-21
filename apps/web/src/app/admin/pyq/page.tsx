"use client";

import Link from "next/link";

import { PyqOperationsDashboard } from "@/components/admin/pyq-operations-dashboard";
import { PageHeader } from "@/components/ui/page-header";

export default function AdminPyqPage() {
  return (
    <>
        <PageHeader
          title="PYQ intelligence"
          description="Upload previous year questions, review concept mappings, and monitor PYQ retrieval analytics."
          actions={
            <div className="flex gap-2">
              <Link href="/admin/knowledge" className="btn-secondary">
                Knowledge
              </Link>
              <Link href="/admin/current-affairs" className="btn-secondary">
                Current affairs
              </Link>
            </div>
          }
        />
        <PyqOperationsDashboard />
    </>
  );
}
