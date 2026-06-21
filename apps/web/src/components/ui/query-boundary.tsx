"use client";

import type { LucideIcon } from "lucide-react";
import type { UseQueryResult } from "@tanstack/react-query";

import { EmptyState, type EmptyStateAction } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { LoadingState } from "@/components/ui/loading-state";

interface QueryBoundaryProps<T> {
  query: UseQueryResult<T>;
  loadingLabel?: string;
  loadingFallback?: React.ReactNode;
  emptyTitle: string;
  emptyDescription?: string;
  emptyIcon?: LucideIcon;
  emptyAction?: EmptyStateAction;
  emptySecondaryAction?: EmptyStateAction;
  isEmpty?: (data: T) => boolean;
  children: (data: T) => React.ReactNode;
}

export function QueryBoundary<T>({
  query,
  loadingLabel,
  loadingFallback,
  emptyTitle,
  emptyDescription,
  emptyIcon,
  emptyAction,
  emptySecondaryAction,
  isEmpty,
  children,
}: QueryBoundaryProps<T>) {
  if (query.isLoading) {
    return loadingFallback ?? <LoadingState label={loadingLabel} />;
  }

  if (query.isError) {
    return <ErrorState error={query.error} onRetry={() => void query.refetch()} />;
  }

  const showEmpty =
    query.data === undefined ||
    query.data === null ||
    (query.data !== undefined && query.data !== null && isEmpty?.(query.data));

  if (showEmpty) {
    return (
      <EmptyState
        title={emptyTitle}
        description={emptyDescription}
        icon={emptyIcon}
        primaryAction={emptyAction}
        secondaryAction={emptySecondaryAction}
      />
    );
  }

  return children(query.data as T);
}
