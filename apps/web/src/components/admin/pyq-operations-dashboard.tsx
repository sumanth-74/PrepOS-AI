"use client";

import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { adminPyqApi, catalogApi } from "@/lib/api";
import type { PyqMappingReviewItem, PyqTrendItem } from "@/lib/types/api";
import { toastError, toastSuccess } from "@/lib/toast";
import { useAuthStore } from "@/stores";

function KpiTile({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="card">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}

function TrendRow({ trend }: { trend: PyqTrendItem }) {
  return (
    <tr className="border-b border-slate-100">
      <td className="py-2 pr-4 font-mono text-xs text-slate-700">{trend.concept_id}</td>
      <td className="py-2 pr-4 text-sm">{trend.pyq_count}</td>
      <td className="py-2 pr-4 text-sm">{trend.frequency_score.toFixed(1)}</td>
      <td className="py-2 text-sm">{trend.trend_score.toFixed(1)}</td>
    </tr>
  );
}

export function PyqOperationsDashboard() {
  const token = useAuthStore((state) => state.accessToken);
  const queryClient = useQueryClient();
  const [uploadOpen, setUploadOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [examId, setExamId] = useState("");
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

  const indexingQuery = useQuery({
    queryKey: ["admin", "pyq", "indexing"],
    queryFn: () => adminPyqApi.indexingMetrics(token!),
    enabled: Boolean(token),
    refetchInterval: 30_000,
  });
  const trendsQuery = useQuery({
    queryKey: ["admin", "pyq", "trends", examId || "upsc_cse"],
    queryFn: () => adminPyqApi.trends(token!, examId || "upsc_cse"),
    enabled: Boolean(token),
  });
  const coverageQuery = useQuery({
    queryKey: ["admin", "pyq", "coverage", examId || "upsc_cse"],
    queryFn: () => adminPyqApi.coverage(token!, examId || "upsc_cse"),
    enabled: Boolean(token),
  });
  const analyticsQuery = useQuery({
    queryKey: ["admin", "pyq", "analytics"],
    queryFn: () => adminPyqApi.analytics(token!, 30),
    enabled: Boolean(token),
  });
  const mappingQuery = useQuery({
    queryKey: ["admin", "pyq", "mappings"],
    queryFn: () => adminPyqApi.mappingReview(token!, examId || undefined),
    enabled: Boolean(token),
  });

  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!token || !file || !title.trim() || !examId) {
        throw new Error("Complete required fields and choose a JSON file.");
      }
      const formData = new FormData();
      formData.append("title", title.trim());
      formData.append("exam_id", examId);
      formData.append("file", file);
      return adminPyqApi.upload(token, formData);
    },
    onSuccess: (data) => {
      toastSuccess(`Uploaded ${data.questions_ingested} PYQ questions. Indexing started.`);
      setUploadOpen(false);
      setTitle("");
      setFile(null);
      void queryClient.invalidateQueries({ queryKey: ["admin", "pyq"] });
    },
    onError: (error: Error) => toastError(error.message || "Upload failed."),
  });

  if (indexingQuery.isLoading) {
    return <p className="text-sm text-slate-600">Loading PYQ operations…</p>;
  }

  const indexing = indexingQuery.data;
  const analytics = analyticsQuery.data;
  const trends = trendsQuery.data?.trends ?? [];
  const coverage = coverageQuery.data;
  const mappings = mappingQuery.data ?? [];

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiTile label="Total PYQs" value={indexing?.total_questions ?? 0} />
        <KpiTile label="Indexed PYQs" value={indexing?.indexed_questions ?? 0} />
        <KpiTile label="PYQ chunks" value={indexing?.total_knowledge_chunks ?? 0} />
        <KpiTile label="Embedded chunks" value={indexing?.indexed_knowledge_chunks ?? 0} />
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiTile label="PYQ queries (30d)" value={analytics?.pyq_queries ?? 0} />
        <KpiTile label="Citation rate" value={`${((analytics?.pyq_citation_rate ?? 0) * 100).toFixed(1)}%`} />
        <KpiTile label="Topic frequency avg" value={(analytics?.pyq_topic_frequency_avg ?? 0).toFixed(2)} />
        <KpiTile label="Revision recs" value={analytics?.pyq_revision_recommendations ?? 0} />
      </div>

      <div className="card space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Upload PYQ bundle</h2>
            <p className="text-sm text-slate-600">JSON array with year, paper, question_text, and optional concept_ids.</p>
          </div>
          <button type="button" className="btn-primary" onClick={() => setUploadOpen((open) => !open)}>
            {uploadOpen ? "Close" : "Upload PYQs"}
          </button>
        </div>
        {uploadOpen ? (
          <form
            className="grid gap-3 md:grid-cols-2"
            onSubmit={(event) => {
              event.preventDefault();
              uploadMutation.mutate();
            }}
          >
            <label className="space-y-1 text-sm">
              <span className="font-medium text-slate-700">Title</span>
              <input className="input w-full" value={title} onChange={(e) => setTitle(e.target.value)} required />
            </label>
            <label className="space-y-1 text-sm">
              <span className="font-medium text-slate-700">Exam</span>
              <select className="input w-full" value={examId} onChange={(e) => setExamId(e.target.value)} required>
                <option value="">Select exam</option>
                {activeExams.map((exam) => (
                  <option key={exam.id} value={exam.id}>
                    {exam.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-1 text-sm md:col-span-2">
              <span className="font-medium text-slate-700">PYQ JSON file</span>
              <input
                type="file"
                accept=".json,.txt,application/json,text/plain"
                className="input w-full"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                required
              />
            </label>
            <div className="md:col-span-2">
              <button type="submit" className="btn-primary" disabled={uploadMutation.isPending}>
                {uploadMutation.isPending ? "Uploading…" : "Start ingestion"}
              </button>
            </div>
          </form>
        ) : null}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card">
          <h2 className="text-lg font-semibold text-slate-900">Trends dashboard</h2>
          <p className="mt-1 text-sm text-slate-600">
            {coverage ? `${coverage.mapped_questions}/${coverage.total_questions} mapped` : "Loading coverage…"}
          </p>
          <table className="mt-4 w-full text-left">
            <thead>
              <tr className="border-b border-slate-200 text-xs uppercase text-slate-500">
                <th className="py-2 pr-4">Concept</th>
                <th className="py-2 pr-4">Count</th>
                <th className="py-2 pr-4">Frequency</th>
                <th className="py-2">Trend</th>
              </tr>
            </thead>
            <tbody>
              {trends.slice(0, 10).map((trend) => (
                <TrendRow key={trend.concept_id} trend={trend} />
              ))}
            </tbody>
          </table>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-slate-900">Mapping review</h2>
          <p className="mt-1 text-sm text-slate-600">Recent PYQ concept mappings for faculty review.</p>
          <ul className="mt-4 space-y-3">
            {mappings.slice(0, 8).map((item: PyqMappingReviewItem) => (
              <li key={item.question.id} className="rounded-lg border border-slate-100 p-3">
                <p className="text-sm font-medium text-slate-900">
                  {item.question.year} · {item.question.paper}
                </p>
                <p className="mt-1 line-clamp-2 text-sm text-slate-600">{item.question.question_text}</p>
                <p className="mt-2 text-xs text-slate-500">
                  Concepts: {item.mappings.map((m) => m.concept_id).join(", ") || "Unmapped"}
                </p>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
