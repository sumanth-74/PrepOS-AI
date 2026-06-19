"use client";

import type { UseQueryResult } from "@tanstack/react-query";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";

interface QueryBoundaryProps<T> {
  query: UseQueryResult<T>;
  loadingLabel?: string;
  emptyTitle: string;
  emptyDescription?: string;
  isEmpty?: (data: T) => boolean;
  children: (data: T) => React.ReactNode;
}

export function QueryBoundary<T>({
  query,
  loadingLabel,
  emptyTitle,
  emptyDescription,
  isEmpty,
  children,
}: QueryBoundaryProps<T>) {
  if (query.isLoading) {
    return <LoadingState label={loadingLabel} />;
  }

  if (query.isError) {
    return <ErrorState error={query.error} onRetry={() => void query.refetch()} />;
  }

  if (query.data === undefined || query.data === null) {
    return <EmptyState title={emptyTitle} description={emptyDescription} />;
  }

  if (isEmpty?.(query.data)) {
    return <EmptyState title={emptyTitle} description={emptyDescription} />;
  }

  return children(query.data);
}
