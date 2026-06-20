"use client";

import { useQuery } from "@tanstack/react-query";

import { adminInstitutionApi } from "@/lib/api";
import type { InstitutionOutcomesResponse, InstitutionRoiResponse } from "@/lib/types/api";
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

export function InstitutionOutcomeDashboard() {
  const token = useAuthStore((state) => state.accessToken);

  const outcomesQuery = useQuery({
    queryKey: ["admin", "institution-outcomes"],
    queryFn: () => adminInstitutionApi.outcomes(token!),
    enabled: Boolean(token),
    refetchInterval: 30_000,
  });
  const roiQuery = useQuery({
    queryKey: ["admin", "institution-roi"],
    queryFn: () => adminInstitutionApi.roi(token!),
    enabled: Boolean(token),
  });
  const initiativesQuery = useQuery({
    queryKey: ["admin", "institution-initiatives"],
    queryFn: () => adminInstitutionApi.initiatives(token!),
    enabled: Boolean(token),
  });

  const handleExport = async () => {
    if (!token) return;
    const csv = await adminInstitutionApi.exportRoiCsv(token);
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "institution_roi.csv";
    anchor.click();
    URL.revokeObjectURL(url);
  };

  if (outcomesQuery.isLoading || roiQuery.isLoading) {
    return <p className="text-sm text-slate-600">Loading institution outcomes…</p>;
  }

  const outcomes: InstitutionOutcomesResponse | undefined = outcomesQuery.data;
  const roi: InstitutionRoiResponse | undefined = roiQuery.data;

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <button type="button" className="btn-secondary" onClick={() => void handleExport()}>
          Export ROI CSV
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiTile label="Average ROI" value={formatScore(roi?.average_roi_score ?? 0)} />
        <KpiTile
          label="Readiness uplift"
          value={`+${formatScore(outcomes?.average_readiness_uplift ?? 0)}`}
        />
        <KpiTile
          label="Forecast uplift"
          value={`+${formatScore(outcomes?.average_forecast_uplift ?? 0)}`}
        />
        <KpiTile
          label="Risk reduction"
          value={`-${formatScore(outcomes?.average_risk_reduction ?? 0)}`}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card">
          <h2 className="text-lg font-semibold text-slate-900">ROI leaderboard</h2>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {(roi?.items ?? []).slice(0, 8).map((item) => (
              <li key={item.subject_key} className="flex justify-between gap-4">
                <span>{item.title ?? item.subject_key.slice(0, 8)}</span>
                <span className="font-medium">
                  {formatScore(item.roi_score)} · +{formatScore(item.readiness_gain)} readiness
                </span>
              </li>
            ))}
          </ul>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-slate-900">Best initiatives</h2>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {(roi?.best_initiatives ?? []).map((item) => (
              <li key={`best-${item.subject_key}`} className="flex justify-between gap-4">
                <span>{item.title ?? item.initiative_type}</span>
                <span className="font-medium text-emerald-700">{formatScore(item.roi_score)} ROI</span>
              </li>
            ))}
            {!roi?.best_initiatives?.length ? (
              <li className="text-slate-500">No high-ROI initiatives yet.</li>
            ) : null}
          </ul>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card">
          <h2 className="text-lg font-semibold text-slate-900">Failed initiatives</h2>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {(roi?.failed_initiatives ?? []).map((item) => (
              <li key={`failed-${item.subject_key}`} className="flex justify-between gap-4">
                <span>{item.title ?? item.initiative_type}</span>
                <span className="font-medium text-rose-700">{formatScore(item.roi_score)} ROI</span>
              </li>
            ))}
            {!roi?.failed_initiatives?.length ? (
              <li className="text-slate-500">No failed initiatives flagged.</li>
            ) : null}
          </ul>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-slate-900">Active initiatives</h2>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
            {(initiativesQuery.data?.initiatives ?? []).slice(0, 8).map((initiative) => (
              <li key={initiative.id} className="flex justify-between gap-4">
                <span>{initiative.title}</span>
                <span className="font-medium capitalize">{initiative.status.replaceAll("_", " ")}</span>
              </li>
            ))}
            {!initiativesQuery.data?.initiatives?.length ? (
              <li className="text-slate-500">No initiatives tracked yet.</li>
            ) : null}
          </ul>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-slate-900">Outcome details</h2>
        <ul className="mt-3 space-y-3 text-sm text-slate-700">
          {(outcomes?.outcomes ?? []).slice(0, 10).map((outcome) => (
            <li key={`${outcome.outcome_type}-${outcome.subject_key}`}>
              <p className="font-medium text-slate-900">{outcome.outcome_type.replaceAll("_", " ")}</p>
              <p>
                Readiness {formatScore(outcome.before.readiness)} → {formatScore(outcome.after.readiness)} (
                {outcome.readiness_gain >= 0 ? "+" : ""}
                {formatScore(outcome.readiness_gain)}), forecast{" "}
                {formatPercent(outcome.before.forecast)} → {formatPercent(outcome.after.forecast)}, variance{" "}
                {outcome.variance >= 0 ? "+" : ""}
                {formatScore(outcome.variance)}
              </p>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
