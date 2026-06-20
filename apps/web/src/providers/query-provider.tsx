"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState, type ReactNode } from "react";
import { attachQueryErrorMonitoring } from "@/lib/observability/query-monitor";

export function QueryProvider({ children }: { children: ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            retry: (failureCount, error) => {
              if (
                typeof error === "object" &&
                error !== null &&
                "status" in error &&
                (error as { status: number }).status === 401
              ) {
                return false;
              }
              return failureCount < 1;
            },
            refetchOnWindowFocus: true,
          },
        },
      }),
  );

  useEffect(() => {
    attachQueryErrorMonitoring(client);
  }, [client]);

  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
