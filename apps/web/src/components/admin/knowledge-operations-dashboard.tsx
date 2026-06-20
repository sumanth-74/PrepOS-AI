"use client";

import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { adminKnowledgeApi, catalogApi } from "@/lib/api";
import type { KnowledgeSourceResponse } from "@/lib/types/api";
import { toastError, toastSuccess } from "@/lib/toast";
import { useAuthStore } from "@/stores";
import { StatusBadge } from "@/components/ui/status-badge";

const SOURCE_TYPES = [
  { value: "ncert", label: "NCERT" },
  { value: "pyq", label: "PYQ" },
  { value: "current_affairs", label: "Current affairs" },
  { value: "book", label: "Book" },
  { value: "syllabus", label: "Syllabus" },
  { value: "mentor_note", label: "Mentor note" },
  { value: "upload", label: "Upload" },
] as const;

function KpiTile({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <div className="card">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
      {hint ? <p className="mt-1 text-xs text-slate-500">{hint}</p> : null}
    </div>
  );
}

function statusTone(status: string): "neutral" | "info" | "success" | "warning" | "danger" {
  switch (status) {
    case "active":
      return "success";
    case "processing":
      return "info";
    case "failed":
    case "quarantined":
      return "danger";
    case "draft":
    case "archived":
      return "neutral";
    default:
      return "warning";
  }
}

function formatDate(value: string | null): string {
  if (!value) {
    return "—";
  }
  return new Date(value).toLocaleString();
}

interface UploadDialogProps {
  open: boolean;
  onClose: () => void;
  onUploaded: () => void;
}

function UploadDialog({ open, onClose, onUploaded }: UploadDialogProps) {
  const token = useAuthStore((state) => state.accessToken);
  const [title, setTitle] = useState("");
  const [examId, setExamId] = useState("");
  const [sourceType, setSourceType] = useState("upload");
  const [file, setFile] = useState<File | null>(null);

  const examsQuery = useQuery({
    queryKey: ["catalog", "exams"],
    queryFn: () => catalogApi.listExams(token),
    enabled: Boolean(token) && open,
  });

  const activeExams = useMemo(
    () => (examsQuery.data ?? []).filter((exam) => exam.status === "active"),
    [examsQuery.data],
  );

  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!token || !file || !title.trim() || !examId) {
        throw new Error("Complete all required fields and choose a file.");
      }
      const formData = new FormData();
      formData.append("title", title.trim());
      formData.append("exam_id", examId);
      formData.append("source_type", sourceType);
      formData.append("file", file);
      return adminKnowledgeApi.uploadSource(token, formData);
    },
    onSuccess: () => {
      toastSuccess("Knowledge source uploaded. Indexing started.");
      setTitle("");
      setFile(null);
      onUploaded();
      onClose();
    },
    onError: (error: Error) => {
      toastError(error.message || "Upload failed.");
    },
  });

  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
      <div
        className="card w-full max-w-lg space-y-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="upload-knowledge-title"
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 id="upload-knowledge-title" className="text-lg font-semibold text-slate-900">
              Upload knowledge source
            </h2>
            <p className="text-sm text-slate-600">UTF-8 text or markdown files only (Phase 1).</p>
          </div>
          <button type="button" className="btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>

        <div className="space-y-3">
          <div>
            <label htmlFor="knowledge-title" className="label">
              Title
            </label>
            <input
              id="knowledge-title"
              className="input mt-1"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Polity fundamentals"
            />
          </div>

          <div>
            <label htmlFor="knowledge-exam" className="label">
              Exam
            </label>
            <select
              id="knowledge-exam"
              className="input mt-1"
              value={examId}
              onChange={(event) => setExamId(event.target.value)}
            >
              <option value="">Select exam</option>
              {activeExams.map((exam) => (
                <option key={exam.exam_id} value={exam.exam_id}>
                  {exam.exam_name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="knowledge-source-type" className="label">
              Source type
            </label>
            <select
              id="knowledge-source-type"
              className="input mt-1"
              value={sourceType}
              onChange={(event) => setSourceType(event.target.value)}
            >
              {SOURCE_TYPES.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="knowledge-file" className="label">
              File
            </label>
            <input
              id="knowledge-file"
              type="file"
              accept=".txt,.md,.markdown,text/plain,text/markdown"
              className="input mt-1"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
          </div>
        </div>

        <div className="flex justify-end gap-2">
          <button type="button" className="btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button
            type="button"
            className="btn-primary"
            disabled={uploadMutation.isPending}
            onClick={() => uploadMutation.mutate()}
          >
            {uploadMutation.isPending ? "Uploading…" : "Upload and index"}
          </button>
        </div>
      </div>
    </div>
  );
}

export function KnowledgeOperationsDashboard() {
  const token = useAuthStore((state) => state.accessToken);
  const queryClient = useQueryClient();
  const [uploadOpen, setUploadOpen] = useState(false);

  const metricsQuery = useQuery({
    queryKey: ["admin", "knowledge", "metrics"],
    queryFn: () => adminKnowledgeApi.metrics(token!),
    enabled: Boolean(token),
    refetchInterval: 30_000,
  });

  const sourcesQuery = useQuery({
    queryKey: ["admin", "knowledge", "sources"],
    queryFn: () => adminKnowledgeApi.listSources(token!, { limit: 100 }),
    enabled: Boolean(token),
    refetchInterval: 15_000,
  });

  function refreshAll() {
    void queryClient.invalidateQueries({ queryKey: ["admin", "knowledge"] });
  }

  if (metricsQuery.isLoading || sourcesQuery.isLoading) {
    return <p className="text-sm text-slate-600">Loading knowledge operations…</p>;
  }

  if (metricsQuery.isError || sourcesQuery.isError || !metricsQuery.data || !sourcesQuery.data) {
    return (
      <div className="card border-red-200 bg-red-50">
        <p className="text-sm text-red-800">Unable to load knowledge operations data.</p>
      </div>
    );
  }

  const metrics = metricsQuery.data;
  const failedChunks = Math.max(0, metrics.total_chunks - metrics.indexed_chunks);

  return (
    <div className="space-y-6">
      <section className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-slate-600">
          Upload sources, monitor indexing progress, and review ingestion failures.
        </p>
        <button type="button" className="btn-primary" onClick={() => setUploadOpen(true)}>
          Upload source
        </button>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <KpiTile label="Total sources" value={metrics.total_sources} />
        <KpiTile label="Active sources" value={metrics.active_sources} />
        <KpiTile label="Total chunks" value={metrics.total_chunks} />
        <KpiTile label="Indexed chunks" value={metrics.indexed_chunks} />
        <KpiTile
          label="Failed chunks"
          value={failedChunks}
          hint={`${metrics.embedding_failures} embedding · ${metrics.ingestion_failures} ingestion`}
        />
      </section>

      <section className="card overflow-x-auto">
        <h2 className="mb-3 text-sm font-semibold text-slate-900">Knowledge sources</h2>
        {sourcesQuery.data.sources.length === 0 ? (
          <p className="text-sm text-slate-500">No sources uploaded yet.</p>
        ) : (
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-slate-200 text-xs uppercase text-slate-500">
              <tr>
                <th className="px-2 py-2">Title</th>
                <th className="px-2 py-2">Type</th>
                <th className="px-2 py-2">Status</th>
                <th className="px-2 py-2">Chunks</th>
                <th className="px-2 py-2">Indexed</th>
                <th className="px-2 py-2">Embed fail</th>
                <th className="px-2 py-2">Ingest fail</th>
                <th className="px-2 py-2">Created</th>
                <th className="px-2 py-2" />
              </tr>
            </thead>
            <tbody>
              {sourcesQuery.data.sources.map((source: KnowledgeSourceResponse) => (
                <tr key={source.id} className="border-b border-slate-100">
                  <td className="px-2 py-3 font-medium text-slate-900">{source.title}</td>
                  <td className="px-2 py-3">{source.source_type}</td>
                  <td className="px-2 py-3">
                    <StatusBadge label={source.status} tone={statusTone(source.status)} />
                  </td>
                  <td className="px-2 py-3">{source.chunk_count}</td>
                  <td className="px-2 py-3">{source.indexed_chunk_count}</td>
                  <td className="px-2 py-3">{source.embedding_failure_count}</td>
                  <td className="px-2 py-3">{source.ingestion_failure_count}</td>
                  <td className="px-2 py-3 whitespace-nowrap">{formatDate(source.created_at)}</td>
                  <td className="px-2 py-3">
                    <Link href={`/admin/knowledge/${source.id}`} className="text-brand-700 underline">
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <p className="text-xs text-slate-500">
        Auto-refreshes every 15s ·{" "}
        <Link href="/admin/copilot" className="text-brand-700 underline">
          Copilot analytics
        </Link>
        {" · "}
        <Link href="/admin/health" className="text-brand-700 underline">
          Platform health
        </Link>
      </p>

      <UploadDialog open={uploadOpen} onClose={() => setUploadOpen(false)} onUploaded={refreshAll} />
    </div>
  );
}
