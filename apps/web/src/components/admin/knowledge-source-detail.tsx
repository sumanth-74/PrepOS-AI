"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";

import { adminKnowledgeApi } from "@/lib/api";
import { useAuthStore } from "@/stores";
import { StatusBadge } from "@/components/ui/status-badge";

function statusTone(status: string): "neutral" | "info" | "success" | "warning" | "danger" {
  switch (status) {
    case "active":
      return "success";
    case "processing":
      return "info";
    case "failed":
    case "quarantined":
      return "danger";
    default:
      return "neutral";
  }
}

function formatDate(value: string | null): string {
  if (!value) {
    return "—";
  }
  return new Date(value).toLocaleString();
}

function MetricRow({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-slate-100 py-2 text-sm last:border-b-0">
      <span className="text-slate-600">{label}</span>
      <span className="font-medium text-slate-900">{value}</span>
    </div>
  );
}

interface KnowledgeSourceDetailProps {
  sourceId: string;
}

export function KnowledgeSourceDetail({ sourceId }: KnowledgeSourceDetailProps) {
  const token = useAuthStore((state) => state.accessToken);

  const sourceQuery = useQuery({
    queryKey: ["admin", "knowledge", "source", sourceId],
    queryFn: () => adminKnowledgeApi.getSource(token!, sourceId),
    enabled: Boolean(token),
    refetchInterval: 10_000,
  });

  if (sourceQuery.isLoading) {
    return <p className="text-sm text-slate-600">Loading source details…</p>;
  }

  if (sourceQuery.isError || !sourceQuery.data) {
    return (
      <div className="card border-red-200 bg-red-50">
        <p className="text-sm text-red-800">Unable to load knowledge source.</p>
        <Link href="/admin/knowledge" className="mt-2 inline-block text-sm text-brand-700 underline">
          Back to sources
        </Link>
      </div>
    );
  }

  const source = sourceQuery.data;
  const progress =
    source.chunk_count > 0
      ? Math.round((source.indexed_chunk_count / source.chunk_count) * 100)
      : 0;

  return (
    <div className="space-y-6">
      <section className="card space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">{source.title}</h2>
            <p className="text-sm text-slate-600">
              {source.source_type} · {source.exam_id}
            </p>
          </div>
          <StatusBadge label={source.status} tone={statusTone(source.status)} />
        </div>
        {source.last_error ? (
          <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-800">{source.last_error}</p>
        ) : null}
      </section>

      <section className="card">
        <h3 className="mb-3 text-sm font-semibold text-slate-900">Indexing progress</h3>
        <div className="mb-2 flex items-center justify-between text-sm text-slate-600">
          <span>
            {source.indexed_chunk_count} / {source.chunk_count} chunks indexed
          </span>
          <span>{progress}%</span>
        </div>
        <div className="h-2 rounded-full bg-slate-100">
          <div className="h-2 rounded-full bg-brand-600 transition-all" style={{ width: `${progress}%` }} />
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="card">
          <h3 className="mb-2 text-sm font-semibold text-slate-900">Ingestion timestamps</h3>
          <MetricRow label="Started" value={formatDate(source.ingestion_started_at)} />
          <MetricRow label="Completed" value={formatDate(source.ingestion_completed_at)} />
          <MetricRow label="Created" value={formatDate(source.created_at)} />
          <MetricRow label="Updated" value={formatDate(source.updated_at)} />
        </div>

        <div className="card">
          <h3 className="mb-2 text-sm font-semibold text-slate-900">Chunk & failure metrics</h3>
          <MetricRow label="Total chunks" value={source.chunk_count} />
          <MetricRow label="Indexed chunks" value={source.indexed_chunk_count} />
          <MetricRow label="Embedding failures" value={source.embedding_failure_count} />
          <MetricRow label="Ingestion failures" value={source.ingestion_failure_count} />
          <MetricRow label="Pending/failed chunks" value={Math.max(0, source.chunk_count - source.indexed_chunk_count)} />
        </div>
      </section>

      <section className="card">
        <h3 className="mb-2 text-sm font-semibold text-slate-900">File & metadata</h3>
        <MetricRow label="File name" value={source.file_name ?? "—"} />
        <MetricRow label="MIME type" value={source.mime_type ?? "—"} />
        <MetricRow label="Content hash" value={source.content_hash} />
        <MetricRow label="Catalog version" value={source.catalog_version ?? "—"} />
        <div className="mt-3">
          <p className="text-xs uppercase tracking-wide text-slate-500">Metadata JSON</p>
          <pre className="mt-1 overflow-x-auto rounded-md bg-slate-50 p-3 text-xs text-slate-800">
            {JSON.stringify(source.metadata, null, 2)}
          </pre>
        </div>
      </section>

      <Link href="/admin/knowledge" className="text-sm text-brand-700 underline">
        Back to knowledge sources
      </Link>
    </div>
  );
}
