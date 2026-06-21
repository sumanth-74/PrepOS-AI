"use client";

import Link from "next/link";

import { PlatformMaturityOverview, SecurityDashboard } from "@/components/admin/platform-maturity-dashboard";
import { PageHeader } from "@/components/ui/page-header";

export default function AdminSecurityPage() {
  return (
    <>
      <PageHeader
        title="Security hardening"
        description="Prompt injection defense, attack KPIs, and tenant distribution."
        actions={
          <div className="flex flex-wrap gap-2">
            <Link href="/admin/security/tenant-audit" className="btn-secondary">
              Tenant audit
            </Link>
            <Link href="/admin/security/knowledge" className="btn-secondary">
              Knowledge security
            </Link>
            <Link href="/admin/security/rate-limits" className="btn-secondary">
              Rate limits
            </Link>
          </div>
        }
      />
      <PlatformMaturityOverview />
      <SecurityDashboard />
    </>
  );
}
