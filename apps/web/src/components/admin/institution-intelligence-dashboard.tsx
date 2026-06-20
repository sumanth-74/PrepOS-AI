"use client";

import { useQuery } from "@tanstack/react-query";

import { adminInstitutionApi } from "@/lib/api";
import type {
  InstitutionDashboardResponse,
  InstitutionInsightsResponse,
  InstitutionMentorEffectivenessResponse,
  InstitutionRecommendationsResponse,
  InstitutionTrendsResponse,
} from "@/lib/types/api";
import { formatPercent, formatScore } from "@/lib/utils/format";
import { useAuthStore } from "@/stores";

function KpiTile({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="card">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  );
}

function TrendBadge({ direction }: { direction: string }) {
  const tone =
    direction === "up" ? "text-emerald-700" : direction === "down" ? "text-rose-700" : "text-slate-600";
  return <span className={`font-medium capitalize ${tone}`}>{direction}</span>;
}

export function InstitutionIntelligenceDashboard() {
  const token = useAuthStore((state) => state.accessToken);

  const dashboardQuery = useQuery({
    queryKey: ["admin", "institution"],
    queryFn: () => adminInstitutionApi.dashboard(token!),
    enabled: Boolean(token),
    refetchInterval: 30_000,
  });
  const insightsQuery = useQuery({
    queryKey: ["admin", "institution-insights"],
    queryFn: () => adminInstitutionApi.insights(token!),
    enabled: Boolean(token),
  });
  const recommendationsQuery = useQuery({
    queryKey: ["admin", "institution-recommendations"],
    queryFn: () => adminInstitutionApi.recommendations(token!),
    enabled: Boolean(token),
  });
  const trendsQuery = useQuery({
    queryKey: ["admin", "institution-trends"],
    queryFn: () => adminInstitutionApi.trends(token!),
    enabled: Boolean(token),
  });
  const mentorsQuery = useQuery({
    queryKey: ["admin", "institution-mentors"],
    queryFn: () => adminInstitutionApi.mentorEffectiveness(token!),
    enabled: Boolean(token),
  });

  const handleExport = async () => {
    if (!token) return;
    const csv = await adminInstitutionApi.exportCsv(token);
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "institution_intelligence.csv";
    anchor.click();
    URL.revokeObjectURL(url);
  };

  if (dashboardQuery.isLoading) {
    return <p className="text-sm text-slate-600">Loading institution intelligence…</p>;
  }

  const dashboard: InstitutionDashboardResponse | undefined = dashboardQuery.data;
  const insights: InstitutionInsightsResponse | undefined = insightsQuery.data;
  const recommendations: InstitutionRecommendationsResponse | undefined = recommendationsQuery.data;
  const trends: InstitutionTrendsResponse | undefined = trendsQuery.data;
  const mentors: InstitutionMentorEffectivenessResponse | undefined = mentorsQuery.data;

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <button type="button" className="btn-secondary" onClick={() => void handleExport()}>
          Export CSV
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiTile label="Institution health" value={formatScore(dashboard?.kpis.institution_health_score ?? 0)} />
        <KpiTile label="Total students" value={dashboard?.kpis.total_students ?? 0} />
        <KpiTile label="At-risk students" value={dashboard?.kpis.at_risk_students ?? 0} />
        <KpiTile label="Intervention ROI" value={formatPercent(dashboard?.kpis.intervention_roi ?? 0)} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card">
          <h2 className="text-lg font-semibold text-slate-900">Readiness & forecast trends</h2>
          <div className="mt-3 space-y-2 text-sm text-slate-700">
            <p>
              Readiness trend: <TrendBadge direction={trends?.readiness_trend ?? "stable"} />
            </p>
            <p>
              Forecast trend: <TrendBadge direction={trends?.forecast_trend ?? "stable"} />
            </p>
            <p>Intervention ROI: {formatPercent(trends?.intervention_roi ?? dashboard?.kpis.intervention_roi ?? 0)}</p>
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-slate-900">Weak concept heatmap</h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {(dashboard?.weak_concepts ?? []).map((concept) => (
              <span
                key={concept}
                className="rounded-full bg-rose-50 px-3 py-1 text-xs font-medium text-rose-800"
              >
                {concept.replaceAll("_", " ")}
              </span>
            ))}
            {!dashboard?.weak_concepts?.length ? (
              <p className="text-sm text-slate-600">No weak concepts flagged yet.</p>
            ) : null}
          </div>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card">
          <h2 className="text-lg font-semibold text-slate-900">Cohort comparison</h2>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {(dashboard?.cohort_comparisons ?? []).map((cohort) => (
              <li key={cohort.cohort_id} className="flex justify-between gap-4">
                <span>{cohort.cohort_id}</span>
                <span className="font-medium">
                  {formatScore(cohort.average_readiness)} · {formatPercent(cohort.average_forecast)} ·{" "}
                  {cohort.at_risk_count} at risk
                </span>
              </li>
            ))}
          </ul>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-slate-900">Mentor effectiveness leaderboard</h2>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {(mentors?.mentors ?? []).slice(0, 5).map((mentor) => (
              <li key={mentor.mentor_id} className="flex justify-between gap-4">
                <span>{mentor.mentor_id.slice(0, 8)}…</span>
                <span className="font-medium">
                  {formatPercent(mentor.intervention_success_rate * 100)} · +
                  {formatScore(mentor.average_gain)} ({mentor.outperformance_pct >= 0 ? "+" : ""}
                  {formatScore(mentor.outperformance_pct)}%)
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card">
          <h2 className="text-lg font-semibold text-slate-900">Top insights</h2>
          <ul className="mt-3 space-y-3 text-sm text-slate-700">
            {(insights?.insights ?? dashboard?.top_insights ?? []).slice(0, 5).map((insight) => (
              <li key={`${insight.insight_type}-${insight.insight_key}`}>
                <p className="font-medium text-slate-900">{insight.title}</p>
                <p className="mt-1 text-xs text-slate-500">{insight.calculation}</p>
              </li>
            ))}
          </ul>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-slate-900">Recommendation panel</h2>
          <ul className="mt-3 space-y-3 text-sm text-slate-700">
            {(recommendations?.recommendations ?? dashboard?.top_recommendations ?? [])
              .slice(0, 5)
              .map((recommendation) => (
                <li key={recommendation.recommendation_type}>
                  <p className="font-medium text-slate-900">{recommendation.title}</p>
                  <p className="mt-1">
                    Impact +{formatScore(recommendation.expected_impact)} · {recommendation.affected_students}{" "}
                    students · priority {formatScore(recommendation.priority_score)}
                  </p>
                  <p className="mt-1 text-xs text-slate-500">{recommendation.explanation}</p>
                </li>
              ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
