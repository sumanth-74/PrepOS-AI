"use client";

import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { adminCurrentAffairsApi, catalogApi } from "@/lib/api";
import type { CurrentAffairsArticleResponse } from "@/lib/types/api";
import { toastError, toastSuccess } from "@/lib/toast";
import { useAuthStore } from "@/stores";
import { StatusBadge } from "@/components/ui/status-badge";

const SOURCE_TYPES = [
  { value: "current_affairs", label: "Current affairs" },
  { value: "pib", label: "PIB" },
  { value: "prs", label: "PRS" },
  { value: "government_scheme", label: "Government scheme" },
  { value: "budget", label: "Budget" },
  { value: "economic_survey", label: "Economic survey" },
] as const;

function KpiTile({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="card">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}

export function CurrentAffairsOperationsDashboard() {
  const token = useAuthStore((state) => state.accessToken);
  const queryClient = useQueryClient();
  const [uploadOpen, setUploadOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [examId, setExamId] = useState("");
  const [sourceType, setSourceType] = useState("pib");
  const [publishedAt, setPublishedAt] = useState("");
  const [sourceAuthority, setSourceAuthority] = useState("pib");
  const [importance, setImportance] = useState("high");
  const [file, setFile] = useState<File | null>(null);

  const examsQuery = useQuery({
    queryKey: ["catalog", "exams"],
    queryFn: () => catalogApi.listExams(token!),
    enabled: Boolean(token),
  });
  const activeExams = useMemo(
    () => (examsQuery.data ?? []).filter((exam) => exam.status === "active"),
    [examsQuery.data],
  );

  const articlesQuery = useQuery({
    queryKey: ["admin", "current-affairs", "articles"],
    queryFn: () => adminCurrentAffairsApi.listArticles(token!),
    enabled: Boolean(token),
    refetchInterval: 15_000,
  });
  const indexingQuery = useQuery({
    queryKey: ["admin", "current-affairs", "indexing"],
    queryFn: () => adminCurrentAffairsApi.indexingMetrics(token!),
    enabled: Boolean(token),
    refetchInterval: 30_000,
  });
  const analyticsQuery = useQuery({
    queryKey: ["admin", "current-affairs", "analytics"],
    queryFn: () => adminCurrentAffairsApi.analytics(token!, 30),
    enabled: Boolean(token),
  });

  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!token || !file || !title.trim() || !examId) {
        throw new Error("Complete required fields and choose a file.");
      }
      const formData = new FormData();
      formData.append("title", title.trim());
      formData.append("exam_id", examId);
      formData.append("source_type", sourceType);
      formData.append("source_authority", sourceAuthority);
      formData.append("importance", importance);
      if (publishedAt) {
        formData.append("published_at", new Date(publishedAt).toISOString());
      }
      formData.append("file", file);
      return adminCurrentAffairsApi.uploadArticle(token, formData);
    },
    onSuccess: () => {
      toastSuccess("Current affairs article uploaded. Indexing started.");
      setUploadOpen(false);
      setTitle("");
      setFile(null);
      void queryClient.invalidateQueries({ queryKey: ["admin", "current-affairs"] });
    },
    onError: (error: Error) => toastError(error.message || "Upload failed."),
  });

  if (articlesQuery.isLoading) {
    return <p className="text-sm text-slate-600">Loading current affairs operations…</p>;
  }

  const articles = articlesQuery.data?.articles ?? [];
  const indexing = indexingQuery.data;
  const analytics = analyticsQuery.data;

  return (
    <div className="space-y-6">
      <section className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-slate-600">
          Upload PIB, PRS, schemes, and other UPSC current affairs sources with recency metadata.
        </p>
        <button type="button" className="btn-primary" onClick={() => setUploadOpen(true)}>
          Upload article
        </button>
      </section>

      {indexing ? (
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <KpiTile label="Total articles" value={indexing.total_articles} />
          <KpiTile label="Active" value={indexing.active_articles} />
          <KpiTile label="Processing" value={indexing.processing_articles} />
          <KpiTile label="Indexed chunks" value={indexing.indexed_chunks} />
        </section>
      ) : null}

      {analytics ? (
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <KpiTile label="Current affairs Q&A" value={analytics.current_affairs_qna_count} />
          <KpiTile label="Article citations" value={analytics.article_citation_usage_count} />
          <KpiTile
            label="Recency retrieval success"
            value={`${(analytics.recency_retrieval_success_rate * 100).toFixed(1)}%`}
          />
          <KpiTile
            label="Recency boost usage"
            value={`${(analytics.recency_boost_usage_rate * 100).toFixed(1)}%`}
          />
        </section>
      ) : null}

      <section className="card overflow-x-auto">
        <h2 className="mb-3 text-sm font-semibold text-slate-900">Article explorer</h2>
        <table className="min-w-full text-left text-sm">
          <thead className="text-xs uppercase text-slate-500">
            <tr>
              <th className="px-2 py-2">Title</th>
              <th className="px-2 py-2">Type</th>
              <th className="px-2 py-2">Published</th>
              <th className="px-2 py-2">Authority</th>
              <th className="px-2 py-2">Status</th>
              <th className="px-2 py-2">Indexed</th>
            </tr>
          </thead>
          <tbody>
            {articles.map((article: CurrentAffairsArticleResponse) => (
              <tr key={article.id} className="border-t border-slate-100">
                <td className="px-2 py-2">
                  <Link href={`/admin/current-affairs/${article.id}`} className="text-brand-700 underline">
                    {article.title}
                  </Link>
                </td>
                <td className="px-2 py-2">{article.source_type}</td>
                <td className="px-2 py-2">
                  {article.published_at ? new Date(article.published_at).toLocaleDateString() : "—"}
                </td>
                <td className="px-2 py-2">{article.source_authority ?? "—"}</td>
                <td className="px-2 py-2">
                  <StatusBadge tone={article.status === "active" ? "success" : "info"} label={article.status} />
                </td>
                <td className="px-2 py-2">
                  {article.indexed_chunk_count}/{article.chunk_count}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {uploadOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
          <div className="card w-full max-w-lg space-y-4">
            <h2 className="text-lg font-semibold text-slate-900">Upload current affairs article</h2>
            <label className="block text-sm">
              Title
              <input className="input mt-1 w-full" value={title} onChange={(e) => setTitle(e.target.value)} />
            </label>
            <label className="block text-sm">
              Exam
              <select className="input mt-1 w-full" value={examId} onChange={(e) => setExamId(e.target.value)}>
                <option value="">Select exam</option>
                {activeExams.map((exam) => (
                  <option key={exam.exam_id} value={exam.exam_id}>
                    {exam.exam_name}
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-sm">
              Source type
              <select
                className="input mt-1 w-full"
                value={sourceType}
                onChange={(e) => setSourceType(e.target.value)}
              >
                {SOURCE_TYPES.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-sm">
              Published at
              <input
                type="date"
                className="input mt-1 w-full"
                value={publishedAt}
                onChange={(e) => setPublishedAt(e.target.value)}
              />
            </label>
            <label className="block text-sm">
              Source authority
              <input
                className="input mt-1 w-full"
                value={sourceAuthority}
                onChange={(e) => setSourceAuthority(e.target.value)}
              />
            </label>
            <label className="block text-sm">
              Importance
              <select
                className="input mt-1 w-full"
                value={importance}
                onChange={(e) => setImportance(e.target.value)}
              >
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </label>
            <label className="block text-sm">
              File
              <input
                type="file"
                className="mt-1 block w-full text-sm"
                accept=".txt,.md,text/plain,text/markdown"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
            </label>
            <div className="flex justify-end gap-2">
              <button type="button" className="btn-secondary" onClick={() => setUploadOpen(false)}>
                Cancel
              </button>
              <button
                type="button"
                className="btn-primary"
                disabled={uploadMutation.isPending}
                onClick={() => void uploadMutation.mutate()}
              >
                {uploadMutation.isPending ? "Uploading…" : "Upload"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
