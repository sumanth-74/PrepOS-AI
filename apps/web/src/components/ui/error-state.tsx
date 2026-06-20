"use client";

import { ApiError } from "@/lib/api/errors";

interface ErrorStateProps {
  error: unknown;
  title?: string;
  onRetry?: () => void;
}

export function ErrorState({ error, title, onRetry }: ErrorStateProps) {
  const message =
    error instanceof ApiError
      ? error.message
      : error instanceof Error
        ? error.message
        : "An unexpected error occurred";

  return (
    <div className="card border-red-200 bg-red-50">
      <h3 className="text-base font-semibold text-red-900">{title ?? "Something went wrong"}</h3>
      <p className="mt-2 text-sm text-red-800">{message}</p>
      {onRetry ? (
        <button type="button" className="btn-secondary mt-4" onClick={onRetry}>
          Try again
        </button>
      ) : null}
    </div>
  );
}
