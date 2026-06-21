"use client";

import { useQuery } from "@tanstack/react-query";

import { getApiOrigin } from "@/lib/api/origin";

interface WorkerHealthResponse {
  status: string;
  worker_count?: number;
}

interface OutboxHealthResponse {
  pending: number;
  failed: number;
}

async function fetchWorkerHealth(): Promise<WorkerHealthResponse> {
  const response = await fetch(`${getApiOrigin()}/health/worker`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Worker health unavailable");
  }
  return response.json() as Promise<WorkerHealthResponse>;
}

async function fetchOutboxHealth(): Promise<OutboxHealthResponse> {
  const response = await fetch(`${getApiOrigin()}/health/outbox`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error("Outbox health unavailable");
  }
  return response.json() as Promise<OutboxHealthResponse>;
}

export function WorkerStatusBanner() {
  const workerQuery = useQuery({
    queryKey: ["health", "worker"],
    queryFn: fetchWorkerHealth,
    refetchInterval: 20_000,
    retry: 1,
  });

  const outboxQuery = useQuery({
    queryKey: ["health", "outbox"],
    queryFn: fetchOutboxHealth,
    refetchInterval: 20_000,
    retry: 1,
    enabled: workerQuery.isSuccess,
  });

  const workerDown =
    workerQuery.isError ||
    (workerQuery.data &&
      (workerQuery.data.status !== "ok" || (workerQuery.data.worker_count ?? 0) === 0));

  const backlog = outboxQuery.data?.pending ?? 0;
  const failed = outboxQuery.data?.failed ?? 0;
  const processing = workerQuery.isLoading || (workerDown && backlog > 0);

  if (!workerDown && !processing && failed === 0) {
    return null;
  }

  return (
    <div
      role="status"
      aria-live="polite"
      className={`border-b px-4 py-3 text-sm ${
        workerDown
          ? "border-amber-200 bg-amber-50 text-amber-900"
          : "border-blue-200 bg-blue-50 text-blue-900"
      }`}
    >
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3">
        <div>
          {workerDown ? (
            <p>
              <strong>Background workers unavailable.</strong> Async jobs (indexing, plans,
              forecasts) may stay pending until Celery workers are running.
            </p>
          ) : processing ? (
            <p>
              <strong>Processing background jobs…</strong> {backlog} task
              {backlog === 1 ? "" : "s"} in queue.
            </p>
          ) : (
            <p>
              <strong>{failed} failed background job{failed === 1 ? "" : "s"}.</strong> Review
              platform health for details.
            </p>
          )}
        </div>
        <button
          type="button"
          className="btn-secondary shrink-0"
          onClick={() => {
            void workerQuery.refetch();
            void outboxQuery.refetch();
          }}
        >
          Retry status check
        </button>
      </div>
    </div>
  );
}
