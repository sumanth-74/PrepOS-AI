"use client";

import Link from "next/link";

import { CurrentAffairsOperationsDashboard } from "@/components/admin/current-affairs-operations-dashboard";
import { PageHeader } from "@/components/ui/page-header";

export default function AdminCurrentAffairsPage() {
  return (
    <>
        <PageHeader
          title="Current affairs operations"
          description="Upload, index, and explore UPSC current affairs sources with recency-aware retrieval."
          actions={
            <Link href="/admin/knowledge" className="btn-secondary">
              Knowledge operations
            </Link>
          }
        />
        <CurrentAffairsOperationsDashboard />
    </>
  );
}
