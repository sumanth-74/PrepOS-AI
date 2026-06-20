"use client";

import { useEffect } from "react";
import { ErrorState } from "@/components/ui/error-state";
import { captureException } from "@/lib/observability/sentry";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    captureException(error, { digest: error.digest, boundary: "global" });
  }, [error]);

  return (
    <html lang="en">
      <body className="flex min-h-screen items-center justify-center bg-slate-50 p-6">
        <div className="w-full max-w-lg">
          <ErrorState error={error} title="Application error" onRetry={reset} />
        </div>
      </body>
    </html>
  );
}
