"use client";

import { useQuery } from "@tanstack/react-query";

import Link from "next/link";

import { PageHeader } from "@/components/ui/page-header";
import { QueryBoundary } from "@/components/ui/query-boundary";
import { adminPlatformApi } from "@/lib/api";
import { useAuthStore } from "@/stores";

export default function AdminPlatformReadinessPage() {
  const token = useAuthStore((state) => state.accessToken);
  const query = useQuery({
    queryKey: ["admin", "platform-readiness"],
    queryFn: () => adminPlatformApi.platformReadiness(token!),
    enabled: Boolean(token),
  });

  return (
    <>
      <PageHeader
        title="Platform readiness"
        description="Composite score across security, reliability, observability, and AI quality."
        actions={
          <Link href="/admin/security" className="btn-secondary">
            Security dashboard
          </Link>
        }
      />
      <QueryBoundary
        query={query}
        loadingLabel="Loading platform readiness…"
        emptyTitle="No readiness data"
        isEmpty={(data) => Object.keys(data).length === 0}
      >
        {(data) => {
          const dimensions = (data.dimension_scores ?? {}) as Record<string, number>;
          return (
            <>
              <div className="rounded-lg border border-slate-200 bg-white p-6">
                <p className="text-sm text-slate-500">Overall score</p>
                <p className="text-4xl font-bold text-brand-800">{String(data.overall_score ?? "—")}</p>
              </div>
              <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {Object.entries(dimensions).map(([key, score]) => (
                  <div key={key} className="rounded-lg border border-slate-200 p-4">
                    <p className="text-xs uppercase text-slate-500">{key.replace(/_/g, " ")}</p>
                    <p className="text-xl font-semibold">{score}</p>
                  </div>
                ))}
              </div>
            </>
          );
        }}
      </QueryBoundary>
    </>
  );
}
