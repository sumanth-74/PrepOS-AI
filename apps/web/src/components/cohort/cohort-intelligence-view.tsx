"use client";

import type {
  CohortRisksResponse,
  CohortSummaryResponse,
  CohortTrendsResponse,
} from "@/lib/types/api";
import { formatLabel, formatPercent, formatScore } from "@/lib/utils/format";

function SegmentBar({ label, count, total }: { label: string; count: number; total: number }) {
  const width = total > 0 ? `${(count / total) * 100}%` : "0%";
  return (
    <div>
      <div className="mb-1 flex justify-between text-sm">
        <span className="text-slate-700">{formatLabel(label)}</span>
        <span className="font-medium text-slate-900">{count}</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-100">
        <div className="h-full rounded-full bg-brand-600" style={{ width }} />
      </div>
    </div>
  );
}

export function CohortIntelligenceView({
  summary,
  risks,
  trends,
}: {
  summary: CohortSummaryResponse;
  risks?: CohortRisksResponse;
  trends?: CohortTrendsResponse;
}) {
  const total = summary.student_count;

  return (
    <div className="space-y-8">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card">
          <p className="text-xs uppercase text-slate-500">Cohort health</p>
          <p className="text-2xl font-semibold text-brand-700">
            {formatScore(summary.metrics.cohort_health_score)}
          </p>
        </div>
        <div className="card">
          <p className="text-xs uppercase text-slate-500">Students</p>
          <p className="text-2xl font-semibold text-brand-700">{summary.student_count}</p>
        </div>
        <div className="card">
          <p className="text-xs uppercase text-slate-500">Avg readiness</p>
          <p className="text-2xl font-semibold text-brand-700">
            {formatScore(summary.metrics.average_readiness)}
          </p>
        </div>
        <div className="card">
          <p className="text-xs uppercase text-slate-500">Avg forecast</p>
          <p className="text-2xl font-semibold text-brand-700">
            {formatPercent(summary.metrics.average_forecast)}
          </p>
        </div>
      </div>

      <section className="card">
        <h2 className="text-sm font-semibold text-slate-900">Segment distribution</h2>
        <div className="mt-4 space-y-3">
          {Object.entries(summary.segments)
            .sort((a, b) => b[1] - a[1])
            .map(([segment, count]) => (
              <SegmentBar key={segment} label={segment} count={count} total={total} />
            ))}
        </div>
      </section>

      <div className="grid gap-4 lg:grid-cols-2">
        <section className="card">
          <h2 className="text-sm font-semibold text-slate-900">Top concept risks</h2>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {(risks?.top_concept_risks ?? summary.top_risks).map((risk) => (
              <li key={risk}>{risk}</li>
            ))}
          </ul>
        </section>
        <section className="card">
          <h2 className="text-sm font-semibold text-slate-900">Trends</h2>
          {trends ? (
            <div className="mt-3 space-y-2 text-sm text-slate-700">
              <p>Readiness: {formatLabel(trends.readiness_trend)}</p>
              <p>Forecast: {formatLabel(trends.forecast_trend)}</p>
              <p>Cohort growth: {formatPercent(trends.cohort_growth * 100)}</p>
              <ul className="mt-3 space-y-2">
                {trends.trends.slice(0, 5).map((trend) => (
                  <li key={trend.concept_id}>
                    {trend.concept_name}: {formatLabel(trend.trend_direction)} (
                    {trend.readiness_delta >= 0 ? "+" : ""}
                    {formatScore(trend.readiness_delta)})
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="mt-3 text-sm text-slate-600">Trend data loading…</p>
          )}
        </section>
      </div>

      {risks && risks.risks.length > 0 ? (
        <section className="card">
          <h2 className="text-sm font-semibold text-slate-900">At-risk students</h2>
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-left text-xs uppercase text-slate-500">
                  <th className="py-2 pr-4">Student</th>
                  <th className="py-2 pr-4">Segment</th>
                  <th className="py-2 pr-4">Risk</th>
                  <th className="py-2">Factors</th>
                </tr>
              </thead>
              <tbody>
                {risks.risks.slice(0, 10).map((risk) => (
                  <tr key={risk.student_id} className="border-b border-slate-50">
                    <td className="py-3 pr-4 font-mono text-xs">{risk.student_id.slice(0, 8)}…</td>
                    <td className="py-3 pr-4">{formatLabel(risk.segment_type)}</td>
                    <td className="py-3 pr-4">{formatScore(risk.risk_score)}</td>
                    <td className="py-3 text-slate-700">{risk.top_risk_factors.join(", ")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}
    </div>
  );
}
