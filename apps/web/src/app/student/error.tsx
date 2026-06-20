"use client";

import { useEffect } from "react";

export default function StudentError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Student route error:", error);
  }, [error]);

  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 px-4 text-center">
      <h2 className="text-xl font-semibold text-slate-900">Something went wrong</h2>
      <p className="max-w-md text-sm text-slate-600">
        This page failed to load. You can retry or return to your dashboard.
      </p>
      <div className="flex gap-3">
        <button type="button" className="btn-primary" onClick={() => reset()}>
          Try again
        </button>
        <a href="/student/dashboard" className="btn-secondary">
          Go to dashboard
        </a>
      </div>
    </div>
  );
}
