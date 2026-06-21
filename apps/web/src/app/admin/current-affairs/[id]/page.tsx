"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";

import { PageHeader } from "@/components/ui/page-header";
import { StatusBadge } from "@/components/ui/status-badge";
import { adminCurrentAffairsApi } from "@/lib/api";
import { useAuthStore } from "@/stores";

export default function AdminCurrentAffairsDetailPage() {
  const params = useParams<{ id: string }>();
  const token = useAuthStore((state) => state.accessToken);

  const articleQuery = useQuery({
    queryKey: ["admin", "current-affairs", params.id],
    queryFn: () => adminCurrentAffairsApi.getArticle(token!, params.id),
    enabled: Boolean(token && params.id),
  });

  return (
    <>
        <PageHeader
          title="Current affairs article"
          description="Article metadata, indexing progress, and concept mapping."
          actions={
            <Link href="/admin/current-affairs" className="btn-secondary">
              Back to explorer
            </Link>
          }
        />
        {articleQuery.isLoading ? (
          <p className="text-sm text-slate-600">Loading article…</p>
        ) : articleQuery.data ? (
          <div className="card space-y-3 text-sm">
            <p className="text-lg font-semibold text-slate-900">{articleQuery.data.title}</p>
            <p>
              <StatusBadge
                tone={articleQuery.data.status === "active" ? "success" : "info"}
                label={articleQuery.data.status}
              />
            </p>
            <p>Type: {articleQuery.data.source_type}</p>
            <p>Authority: {articleQuery.data.source_authority ?? "—"}</p>
            <p>
              Published:{" "}
              {articleQuery.data.published_at
                ? new Date(articleQuery.data.published_at).toLocaleString()
                : "—"}
            </p>
            <p>Importance: {articleQuery.data.importance ?? "—"}</p>
            <p>Exam stage: {articleQuery.data.exam_stage ?? "—"}</p>
            <p>
              Indexed chunks: {articleQuery.data.indexed_chunk_count}/{articleQuery.data.chunk_count}
            </p>
            <p>Concept IDs: {articleQuery.data.concept_ids.join(", ") || "—"}</p>
          </div>
        ) : (
          <p className="text-sm text-red-700">Unable to load article.</p>
        )}
    </>
  );
}
