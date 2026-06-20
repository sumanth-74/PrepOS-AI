"use client";

import Link from "next/link";
import type { UseQueryResult } from "@tanstack/react-query";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";

interface EmptyAction {
  label: string;
  href: string;
}

interface QueryBoundaryProps<T> {
  query: UseQueryResult<T>;
  loadingLabel?: string;
  loadingFallback?: React.ReactNode;
  emptyTitle: string;
  emptyDescription?: string;
  emptyAction?: EmptyAction;
  isEmpty?: (data: T) => boolean;
  children: (data: T) => React.ReactNode;
}

export function QueryBoundary<T>({
  query,
  loadingLabel,
  loadingFallback,
  emptyTitle,
  emptyDescription,
  emptyAction,
  isEmpty,
  children,
}: QueryBoundaryProps<T>) {
  if (query.isLoading) {
    return loadingFallback ?? <LoadingState label={loadingLabel} />;
  }

  if (query.isError) {
    return <ErrorState error={query.error} onRetry={() => void query.refetch()} />;
  }

  if (query.data === undefined || query.data === null) {
    return (
      <EmptyState
        title={emptyTitle}
        description={emptyDescription}
        action={
          emptyAction ? (
            <Link href={emptyAction.href} className="btn-primary">
              {emptyAction.label}
            </Link>
          ) : undefined
        }
      />
    );
  }

  if (isEmpty?.(query.data)) {
    return (
      <EmptyState
        title={emptyTitle}
        description={emptyDescription}
        action={
          emptyAction ? (
            <Link href={emptyAction.href} className="btn-primary">
              {emptyAction.label}
            </Link>
          ) : undefined
        }
      />
    );
  }

  return children(query.data);
}
