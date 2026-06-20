"use client";

import { useQuery } from "@tanstack/react-query";
import { getApiOrigin } from "@/lib/api/origin";

interface OpsHealthResponse {
  status: string;
  checks: Record<string, string | number>;
  worker: {
    status: string;
    worker_count: number;
    workers: string[];
  };
  outbox: {
    pending: number;
    published: number;
    failed: number;
    total: number;
  };
}

async function fetchOpsHealth(): Promise<OpsHealthResponse> {
  const response = await fetch(`${getApiOrigin()}/health/ops`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Health check failed (${response.status})`);
  }
  return response.json() as Promise<OpsHealthResponse>;
}

function StatusPill({ status }: { status: string }) {
  const tone =
    status === "ok"
      ? "bg-emerald-100 text-emerald-800"
      : status === "degraded"
        ? "bg-amber-100 text-amber-800"
        : "bg-red-100 text-red-800";

  return (
    <span className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${tone}`}>
      {status}
    </span>
  );
}

export function OpsHealthDashboard() {
  const healthQuery = useQuery({
    queryKey: ["ops", "health"],
    queryFn: fetchOpsHealth,
    refetchInterval: 15_000,
  });

  if (healthQuery.isLoading) {
    return <p className="text-sm text-slate-600">Loading platform health…</p>;
  }

  if (healthQuery.isError || !healthQuery.data) {
    return (
      <div className="card border-red-200 bg-red-50">
        <p className="text-sm text-red-800">
          Unable to reach backend health endpoints. Ensure the API is running.
        </p>
      </div>
    );
  }

  const data = healthQuery.data;

  return (
    <div className="space-y-6">
      <section className="card">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-sm font-semibold text-slate-900">Overall status</h2>
          <StatusPill status={data.status} />
        </div>
        <p className="mt-2 text-xs text-slate-500">Auto-refreshes every 15 seconds.</p>
      </section>

      <section className="card">
        <h2 className="mb-3 text-sm font-semibold text-slate-900">Component checks</h2>
        <dl className="grid gap-3 sm:grid-cols-2">
          {Object.entries(data.checks).map(([key, value]) => (
            <div key={key} className="rounded-lg bg-slate-50 p-3">
              <dt className="text-xs uppercase text-slate-500">{key.replaceAll("_", " ")}</dt>
              <dd className="mt-1 text-sm font-medium text-slate-900">{String(value)}</dd>
            </div>
          ))}
        </dl>
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="card">
          <h2 className="text-sm font-semibold text-slate-900">Celery workers</h2>
          <div className="mt-3 space-y-2 text-sm text-slate-700">
            <p>
              Status: <StatusPill status={data.worker.status} />
            </p>
            <p>Workers online: {data.worker.worker_count}</p>
            {data.worker.workers.length > 0 ? (
              <ul className="list-inside list-disc text-xs text-slate-600">
                {data.worker.workers.map((worker) => (
                  <li key={worker}>{worker}</li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-slate-500">No workers responded to heartbeat ping.</p>
            )}
          </div>
        </section>

        <section className="card">
          <h2 className="text-sm font-semibold text-slate-900">Outbox queue</h2>
          <dl className="mt-3 grid grid-cols-2 gap-3 text-sm text-slate-700">
            <div>
              <dt className="text-xs text-slate-500">Pending</dt>
              <dd className="font-medium">{data.outbox.pending}</dd>
            </div>
            <div>
              <dt className="text-xs text-slate-500">Published</dt>
              <dd className="font-medium">{data.outbox.published}</dd>
            </div>
            <div>
              <dt className="text-xs text-slate-500">Failed</dt>
              <dd className="font-medium">{data.outbox.failed}</dd>
            </div>
            <div>
              <dt className="text-xs text-slate-500">Total</dt>
              <dd className="font-medium">{data.outbox.total}</dd>
            </div>
          </dl>
        </section>
      </div>
    </div>
  );
}
