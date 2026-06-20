import type { QueryClient } from "@tanstack/react-query";
import { captureException } from "@/lib/observability/sentry";

export function attachQueryErrorMonitoring(queryClient: QueryClient): void {
  queryClient.getQueryCache().subscribe((event) => {
    if (event.type !== "updated") return;
    const query = event.query;
    if (query.state.status !== "error") return;
    if (!query.state.error) return;

    captureException(query.state.error, {
      source: "react_query",
      queryKey: JSON.stringify(query.queryKey),
    });
  });

  queryClient.getMutationCache().subscribe((event) => {
    if (event.type !== "updated") return;
    const mutation = event.mutation;
    if (mutation.state.status !== "error") return;
    if (!mutation.state.error) return;

    captureException(mutation.state.error, {
      source: "react_query_mutation",
      mutationKey: JSON.stringify(mutation.options.mutationKey ?? []),
    });
  });
}
