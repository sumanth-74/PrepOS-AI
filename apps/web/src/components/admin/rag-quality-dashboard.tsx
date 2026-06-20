"use client";

import { useQuery } from "@tanstack/react-query";

import { adminRagQualityApi } from "@/lib/api";
import type { RagQualityResponse, RagQualityTrendPoint, SourceQualityItem } from "@/lib/types/api";
import { useAuthStore } from "@/stores";

function KpiTile({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="card">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}

function TrendChart({
  title,
  points,
  field,
  colorClass,
}: {
  title: string;
  points: RagQualityTrendPoint[];
  field: keyof RagQualityTrendPoint;
  colorClass: string;
}) {
  const values = points.map((point) => Number(point[field] ?? 0));
  const max = Math.max(...values, 1);
  return (
    <div className="card">
      <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
      <div className="mt-4 flex h-32 items-end gap-1">
        {points.length === 0 ? (
          <p className="text-sm text-slate-500">No trend data yet.</p>
        ) : (
          points.map((point) => {
            const value = Number(point[field] ?? 0);
            const height = `${Math.max(8, (value / max) * 100)}%`;
            return (
              <div key={`${point.date}-${String(field)}`} className="flex flex-1 flex-col items-center gap-1">
                <div className={`w-full rounded-t ${colorClass}`} style={{ height }} title={`${value.toFixed(1)}`} />
                <span className="text-[10px] text-slate-500">{point.date.slice(5)}</span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

function pct(value: number) {
  return `${value.toFixed(1)}%`;
}

export function RagQualityDashboard() {
  const token = useAuthStore((state) => state.accessToken);
  const qualityQuery = useQuery({
    queryKey: ["admin", "rag-quality"],
    queryFn: () => adminRagQualityApi.metrics(token!, 30),
    enabled: Boolean(token),
    refetchInterval: 30_000,
  });

  if (qualityQuery.isLoading) {
    return <p className="text-sm text-slate-600">Loading RAG quality metrics…</p>;
  }

  const data: RagQualityResponse | undefined = qualityQuery.data;
  const faithfulness = data?.faithfulness.avg_support_score ?? 0;
  const citationCoverage = data?.citation_coverage.avg_citation_coverage ?? 0;
  const hallucinationRate = ((data?.hallucination.avg_hallucination_score ?? 0) / 100) * 100;
  const avgConfidence = data?.source_quality.sources.length
    ? data.source_quality.sources.reduce((sum, item) => sum + item.avg_confidence_score, 0) /
      data.source_quality.sources.length
    : 0;

  const handleExport = async () => {
    if (!token) return;
    const csv = await adminRagQualityApi.exportCsv(token, 30);
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "rag_quality_evaluations.csv";
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <button type="button" className="btn-secondary" onClick={() => void handleExport()}>
          Export CSV
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiTile label="Avg faithfulness" value={pct(faithfulness)} />
        <KpiTile label="Avg citation coverage" value={pct(citationCoverage)} />
        <KpiTile label="Hallucination rate" value={pct(hallucinationRate)} />
        <KpiTile label="Avg confidence" value={pct(avgConfidence)} />
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-slate-900">Retrieval metrics</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <KpiTile label="Recall@5" value={(data?.retrieval.recall_at_5 ?? 0).toFixed(3)} />
          <KpiTile label="Recall@8" value={(data?.retrieval.recall_at_8 ?? 0).toFixed(3)} />
          <KpiTile label="Precision@5" value={(data?.retrieval.precision_at_5 ?? 0).toFixed(3)} />
          <KpiTile label="Precision@8" value={(data?.retrieval.precision_at_8 ?? 0).toFixed(3)} />
          <KpiTile label="MRR" value={(data?.retrieval.mrr ?? 0).toFixed(3)} />
          <KpiTile label="NDCG" value={(data?.retrieval.ndcg ?? 0).toFixed(3)} />
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <TrendChart
          title="Faithfulness trend"
          points={data?.trends ?? []}
          field="avg_support_score"
          colorClass="bg-emerald-500"
        />
        <TrendChart
          title="Hallucination trend"
          points={data?.trends ?? []}
          field="avg_hallucination_score"
          colorClass="bg-rose-500"
        />
        <TrendChart
          title="Citation coverage trend"
          points={data?.trends ?? []}
          field="avg_citation_coverage"
          colorClass="bg-sky-500"
        />
      </div>

      <div className="card overflow-x-auto">
        <h2 className="text-lg font-semibold text-slate-900">Source quality</h2>
        <table className="mt-4 w-full text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-xs uppercase text-slate-500">
              <th className="py-2 pr-4">Source type</th>
              <th className="py-2 pr-4">Queries</th>
              <th className="py-2 pr-4">Avg confidence</th>
              <th className="py-2 pr-4">Avg support</th>
              <th className="py-2">Avg hallucination</th>
            </tr>
          </thead>
          <tbody>
            {(data?.source_quality.sources ?? []).map((row: SourceQualityItem) => (
              <tr key={row.source_type} className="border-b border-slate-100">
                <td className="py-2 pr-4 font-medium">{row.source_type}</td>
                <td className="py-2 pr-4">{row.query_count}</td>
                <td className="py-2 pr-4">{pct(row.avg_confidence_score)}</td>
                <td className="py-2 pr-4">{pct(row.avg_support_score)}</td>
                <td className="py-2">{pct(row.avg_hallucination_score)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
