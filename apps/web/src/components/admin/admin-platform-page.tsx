"use client";

import { useQuery } from "@tanstack/react-query";
import type { UseQueryResult } from "@tanstack/react-query";

import { PageHeader } from "@/components/ui/page-header";
import { QueryBoundary } from "@/components/ui/query-boundary";

interface AdminPlatformPageProps {
  title: string;
  description: string;
  query: UseQueryResult<Record<string, unknown>>;
  loadingLabel: string;
  emptyTitle: string;
  emptyDescription?: string;
}

export function AdminPlatformPage({
  title,
  description,
  query,
  loadingLabel,
  emptyTitle,
  emptyDescription,
}: AdminPlatformPageProps) {
  return (
    <>
      <PageHeader title={title} description={description} />
      <QueryBoundary
        query={query}
        loadingLabel={loadingLabel}
        emptyTitle={emptyTitle}
        emptyDescription={emptyDescription}
        isEmpty={(data) => Object.keys(data).length === 0}
      >
        {(data) => (
          <pre className="overflow-x-auto rounded-lg border border-slate-200 bg-slate-50 p-4 text-xs text-slate-700">
            {JSON.stringify(data, null, 2)}
          </pre>
        )}
      </QueryBoundary>
    </>
  );
}

export function useAdminPlatformQuery<T extends Record<string, unknown>>(
  key: string[],
  fetchFn: () => Promise<T>,
  enabled: boolean,
): UseQueryResult<T> {
  return useQuery({
    queryKey: key,
    queryFn: fetchFn,
    enabled,
  });
}
