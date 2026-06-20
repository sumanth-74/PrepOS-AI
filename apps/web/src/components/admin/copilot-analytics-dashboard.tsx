"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { adminCopilotApi } from "@/lib/api";
import type { CopilotAnalyticsResponse } from "@/lib/types/api";
import { useAuthStore } from "@/stores";

function formatPercent(value: string): string {
  const numeric = Number(value);
  if (Number.isNaN(numeric)) {
    return value;
  }
  return `${numeric.toFixed(1)}%`;
}

function CriteriaBadge({ met }: { met: boolean }) {
  return (
    <span
      className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${
        met ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"
      }`}
    >
      {met ? "Met" : "Not met"}
    </span>
  );
}

function HorizontalBarChart({
  items,
  labelKey,
  valueKey,
}: {
  items: Array<Record<string, string | number>>;
  labelKey: string;
  valueKey: string;
}) {
  const max = Math.max(...items.map((item) => Number(item[valueKey]) || 0), 1);
  return (
    <div className="space-y-2" role="img" aria-label="Bar chart">
      {items.map((item) => {
        const value = Number(item[valueKey]) || 0;
        const width = `${Math.max(4, (value / max) * 100)}%`;
        return (
          <div key={String(item[labelKey])}>
            <div className="mb-1 flex items-center justify-between gap-2 text-xs text-slate-600">
              <span className="truncate">{String(item[labelKey])}</span>
              <span>{value}</span>
            </div>
            <div className="h-2 rounded-full bg-slate-100">
              <div className="h-2 rounded-full bg-brand-600" style={{ width }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function KpiTile({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <div className="card">
      <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{value}</p>
      {hint ? <p className="mt-1 text-xs text-slate-500">{hint}</p> : null}
    </div>
  );
}

export function CopilotAnalyticsDashboard() {
  const token = useAuthStore((state) => state.accessToken);
  const [days, setDays] = useState(30);
  const [exporting, setExporting] = useState(false);

  const analyticsQuery = useQuery({
    queryKey: ["admin", "copilot", "analytics", days],
    queryFn: () => adminCopilotApi.analytics(token!, days),
    enabled: Boolean(token),
    refetchInterval: 60_000,
  });

  async function handleExport() {
    if (!token) {
      return;
    }
    setExporting(true);
    try {
      const csv = await adminCopilotApi.exportCsv(token, days);
      const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `copilot_queries_${days}d.csv`;
      anchor.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  }

  if (analyticsQuery.isLoading) {
    return <p className="text-sm text-slate-600">Loading copilot analytics…</p>;
  }

  if (analyticsQuery.isError || !analyticsQuery.data) {
    return (
      <div className="card border-red-200 bg-red-50">
        <p className="text-sm text-red-800">Unable to load copilot analytics.</p>
      </div>
    );
  }

  const data: CopilotAnalyticsResponse = analyticsQuery.data;

  return (
    <div className="space-y-6">
      <section className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <label htmlFor="analytics-days" className="label">
            Period (days)
          </label>
          <select
            id="analytics-days"
            className="input mt-1 w-32"
            value={days}
            onChange={(event) => setDays(Number(event.target.value))}
          >
            {[7, 14, 30, 60, 90].map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>
        <button type="button" className="btn-secondary" disabled={exporting} onClick={() => void handleExport()}>
          {exporting ? "Exporting…" : "Export CSV"}
        </button>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiTile label="DAU" value={data.dau} hint="Distinct users today" />
        <KpiTile label="WAU" value={data.wau} hint="Distinct users this week" />
        <KpiTile label="Total queries" value={data.total_queries} />
        <KpiTile
          label="Queries / active user"
          value={Number(data.queries_per_user_avg).toFixed(2)}
        />
      </section>

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiTile
          label="Content questions today"
          value={data.content_analytics.content_questions_today}
        />
        <KpiTile
          label="Content questions (period)"
          value={data.content_analytics.content_questions_period}
        />
        <KpiTile
          label="Queries with citations"
          value={data.content_analytics.citation_usage_count}
          hint={`${formatPercent(data.content_analytics.citation_usage_rate)} of content Q&A`}
        />
        <KpiTile
          label="Confidence levels tracked"
          value={data.content_analytics.confidence_distribution.length}
        />
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <div className="card">
          <h2 className="text-sm font-semibold text-slate-900">Student usage</h2>
          <p className="mt-2 text-2xl font-semibold">{data.student_usage.query_count}</p>
          <p className="text-xs text-slate-500">
            {data.student_usage.unique_users} users · {formatPercent(data.student_usage.share_of_queries)}
          </p>
        </div>
        <div className="card">
          <h2 className="text-sm font-semibold text-slate-900">Mentor usage</h2>
          <p className="mt-2 text-2xl font-semibold">{data.mentor_usage.query_count}</p>
          <p className="text-xs text-slate-500">
            {data.mentor_usage.unique_users} users · {formatPercent(data.mentor_usage.share_of_queries)}
          </p>
        </div>
        <div className="card">
          <h2 className="text-sm font-semibold text-slate-900">Admin usage</h2>
          <p className="mt-2 text-2xl font-semibold">{data.admin_usage.query_count}</p>
          <p className="text-xs text-slate-500">
            {data.admin_usage.unique_users} users · {formatPercent(data.admin_usage.share_of_queries)}
          </p>
        </div>
      </section>

      <section className="card">
        <h2 className="mb-3 text-sm font-semibold text-slate-900">Pilot success criteria</h2>
        <ul className="space-y-2 text-sm">
          <li className="flex items-center justify-between gap-3">
            <span>≥40% active users use Copilot ({formatPercent(data.success_criteria.active_user_adoption_actual)})</span>
            <CriteriaBadge met={data.success_criteria.active_user_adoption_met} />
          </li>
          <li className="flex items-center justify-between gap-3">
            <span>Unknown intent rate &lt;15% ({formatPercent(data.success_criteria.unknown_intent_rate_actual)})</span>
            <CriteriaBadge met={data.success_criteria.unknown_intent_rate_met} />
          </li>
          <li className="flex items-center justify-between gap-3">
            <span>
              Avg queries per active user &gt;3 ({Number(data.success_criteria.queries_per_active_user_actual).toFixed(2)})
            </span>
            <CriteriaBadge met={data.success_criteria.queries_per_active_user_met} />
          </li>
          <li className="flex items-center justify-between gap-3">
            <span>Content-explanation signal in top prompts</span>
            <CriteriaBadge met={data.success_criteria.content_explanation_in_top_five_met} />
          </li>
        </ul>
        <p className="mt-3 text-xs text-slate-500">{data.success_criteria.content_explanation_note}</p>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="card">
          <h2 className="mb-3 text-sm font-semibold text-slate-900">Content questions per day</h2>
          <HorizontalBarChart
            items={data.content_analytics.content_daily_usage.map((item) => ({
              date: item.date,
              query_count: item.query_count,
            }))}
            labelKey="date"
            valueKey="query_count"
          />
        </div>
        <div className="card">
          <h2 className="mb-3 text-sm font-semibold text-slate-900">Confidence distribution</h2>
          {data.content_analytics.confidence_distribution.length === 0 ? (
            <p className="text-sm text-slate-500">No content Q&A confidence data in this period.</p>
          ) : (
            <HorizontalBarChart
              items={data.content_analytics.confidence_distribution.map((item) => ({
                confidence: item.confidence,
                count: item.count,
              }))}
              labelKey="confidence"
              valueKey="count"
            />
          )}
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold text-slate-900">Mentor knowledge Q&A</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <KpiTile
            label="Mentor content questions today"
            value={data.mentor_content_analytics.mentor_content_questions_today}
          />
          <KpiTile
            label="Mentor content questions (period)"
            value={data.mentor_content_analytics.mentor_content_questions_period}
          />
          <KpiTile
            label="Mentor queries with citations"
            value={data.mentor_content_analytics.citation_usage_count}
            hint={`${formatPercent(data.mentor_content_analytics.citation_usage_rate)} of mentor content Q&A`}
          />
          <KpiTile
            label="Mentor confidence levels tracked"
            value={data.mentor_content_analytics.confidence_distribution.length}
          />
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="card">
          <h2 className="mb-3 text-sm font-semibold text-slate-900">Mentor content questions per day</h2>
          <HorizontalBarChart
            items={data.mentor_content_analytics.mentor_content_daily_usage.map((item) => ({
              date: item.date,
              query_count: item.query_count,
            }))}
            labelKey="date"
            valueKey="query_count"
          />
        </div>
        <div className="card">
          <h2 className="mb-3 text-sm font-semibold text-slate-900">Mentor confidence distribution</h2>
          {data.mentor_content_analytics.confidence_distribution.length === 0 ? (
            <p className="text-sm text-slate-500">No mentor content Q&A confidence data in this period.</p>
          ) : (
            <HorizontalBarChart
              items={data.mentor_content_analytics.confidence_distribution.map((item) => ({
                confidence: item.confidence,
                count: item.count,
              }))}
              labelKey="confidence"
              valueKey="count"
            />
          )}
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="card">
          <h2 className="mb-3 text-sm font-semibold text-slate-900">Daily usage trend</h2>
          <HorizontalBarChart
            items={data.daily_usage_trend.map((item) => ({
              date: item.date,
              query_count: item.query_count,
            }))}
            labelKey="date"
            valueKey="query_count"
          />
        </div>
        <div className="card">
          <h2 className="mb-3 text-sm font-semibold text-slate-900">Intent distribution</h2>
          <HorizontalBarChart
            items={data.intent_distribution.map((item) => ({
              intent: item.intent,
              count: item.count,
            }))}
            labelKey="intent"
            valueKey="count"
          />
          <p className="mt-3 text-xs text-slate-500">
            Unknown intent rate: {formatPercent(data.unknown_intent_rate)}
          </p>
        </div>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <div className="card">
          <h2 className="mb-3 text-sm font-semibold text-slate-900">Top prompts</h2>
          <HorizontalBarChart
            items={data.top_prompts.map((item) => ({
              query_text: item.query_text,
              count: item.count,
            }))}
            labelKey="query_text"
            valueKey="count"
          />
        </div>
        <div className="card">
          <h2 className="mb-3 text-sm font-semibold text-slate-900">Unknown intents</h2>
          {data.unknown_intents.length === 0 ? (
            <p className="text-sm text-slate-500">No unknown intents in this period.</p>
          ) : (
            <HorizontalBarChart
              items={data.unknown_intents.map((item) => ({
                query_text: item.query_text,
                count: item.count,
              }))}
              labelKey="query_text"
              valueKey="count"
            />
          )}
        </div>
      </section>

      <section className="card">
        <h2 className="mb-3 text-sm font-semibold text-slate-900">Adoption funnel</h2>
        <HorizontalBarChart
          items={data.adoption_funnel.map((item) => ({
            stage: item.stage.replaceAll("_", " "),
            count: item.count,
          }))}
          labelKey="stage"
          valueKey="count"
        />
      </section>

      <p className="text-xs text-slate-500">
        Generated at {new Date(data.generated_at).toLocaleString()} ·{" "}
        <Link href="/admin/health" className="text-brand-700 underline">
          Platform health
        </Link>
      </p>
    </div>
  );
}
