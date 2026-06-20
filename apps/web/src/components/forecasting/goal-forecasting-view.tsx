"use client";

import { useState } from "react";

import { StatusBadge } from "@/components/ui/status-badge";
import type {
  ForecastExplainResponse,
  ForecastHistoryEntry,
  ForecastScenarioItem,
  GoalForecastResponse,
} from "@/lib/types/api";
import { formatLabel, formatPercent, formatScore } from "@/lib/utils/format";

function statusTone(status: string): "success" | "warning" | "info" {
  if (status === "on_track" || status === "achieved") return "success";
  if (status === "at_risk" || status === "off_track") return "warning";
  return "info";
}

function ReadinessProjectionChart({
  current,
  projected,
  target,
}: {
  current: number;
  projected: number;
  target: number;
}) {
  const max = Math.max(current, projected, target, 100);
  const bars = [
    { label: "Current", value: current, color: "bg-slate-400" },
    { label: "Projected", value: projected, color: "bg-brand-600" },
    { label: "Target", value: target, color: "bg-emerald-500" },
  ];

  return (
    <div className="card">
      <h2 className="text-sm font-semibold text-slate-900">Readiness projection</h2>
      <div className="mt-4 flex h-40 items-end gap-4">
        {bars.map((bar) => (
          <div key={bar.label} className="flex flex-1 flex-col items-center gap-2">
            <span className="text-xs font-medium text-slate-700">{formatScore(bar.value)}</span>
            <div
              className={`w-full rounded-t ${bar.color}`}
              style={{ height: `${Math.max(8, (bar.value / max) * 100)}%` }}
            />
            <span className="text-xs text-slate-500">{bar.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ProbabilityMeter({ probability }: { probability: number }) {
  const clamped = Math.min(100, Math.max(0, probability));
  const tone =
    clamped >= 75 ? "bg-emerald-500" : clamped >= 50 ? "bg-amber-500" : "bg-rose-500";

  return (
    <div className="card">
      <p className="text-xs uppercase text-slate-500">Goal probability</p>
      <p className="mt-1 text-3xl font-semibold text-brand-700">{formatPercent(clamped)}</p>
      <div className="mt-4 h-3 overflow-hidden rounded-full bg-slate-100">
        <div className={`h-full rounded-full ${tone}`} style={{ width: `${clamped}%` }} />
      </div>
    </div>
  );
}

function ScenarioTable({ scenarios }: { scenarios: ForecastScenarioItem[] }) {
  if (scenarios.length === 0) {
    return <p className="text-sm text-slate-600">No scenarios available.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="border-b border-slate-100 text-left text-xs uppercase text-slate-500">
            <th className="py-2 pr-4">Scenario</th>
            <th className="py-2 pr-4">Hours/week</th>
            <th className="py-2 pr-4">Readiness</th>
            <th className="py-2">Probability</th>
          </tr>
        </thead>
        <tbody>
          {scenarios.map((scenario) => (
            <tr key={scenario.id} className="border-b border-slate-50">
              <td className="py-3 pr-4 font-medium text-slate-900">{scenario.scenario_name}</td>
              <td className="py-3 pr-4 text-slate-700">
                {(scenario.weekly_minutes / 60).toFixed(1)}h
              </td>
              <td className="py-3 pr-4 text-slate-700">
                {formatScore(scenario.projected_readiness)}
              </td>
              <td className="py-3 text-slate-700">
                {formatPercent(scenario.probability_of_success)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ForecastHistoryTable({ entries }: { entries: ForecastHistoryEntry[] }) {
  if (entries.length === 0) {
    return <p className="text-sm text-slate-600">No forecast history yet.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="border-b border-slate-100 text-left text-xs uppercase text-slate-500">
            <th className="py-2 pr-4">Date</th>
            <th className="py-2 pr-4">Projected</th>
            <th className="py-2 pr-4">Probability</th>
            <th className="py-2">Status</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <tr key={entry.forecast_id} className="border-b border-slate-50">
              <td className="py-3 pr-4 text-slate-700">{entry.forecast_date}</td>
              <td className="py-3 pr-4 text-slate-700">
                {formatScore(entry.projected_readiness)}
              </td>
              <td className="py-3 pr-4 text-slate-700">
                {formatPercent(entry.probability_of_success)}
              </td>
              <td className="py-3">
                <StatusBadge label={formatLabel(entry.forecast_status)} tone={statusTone(entry.forecast_status)} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function GoalForecastingView({
  forecast,
  history,
  onGenerate,
  onExplain,
  onSimulateCustom,
  generating,
  simulating,
  showRegenerate,
}: {
  forecast: GoalForecastResponse | undefined;
  history?: ForecastHistoryEntry[];
  onGenerate?: () => void;
  onExplain?: () => Promise<ForecastExplainResponse>;
  onSimulateCustom?: (weeklyMinutes: number) => void;
  generating?: boolean;
  simulating?: boolean;
  showRegenerate?: boolean;
}) {
  const [explanation, setExplanation] = useState<ForecastExplainResponse | null>(null);
  const [customHours, setCustomHours] = useState("10");

  const handleExplain = async () => {
    if (!onExplain) return;
    const result = await onExplain();
    setExplanation(result);
  };

  if (!forecast) {
    return (
      <div className="card space-y-3">
        <p className="text-sm text-slate-600">
          No goal forecast yet. Generate one to see readiness projection, probability, and scenarios.
        </p>
        {onGenerate ? (
          <button type="button" className="btn-primary" disabled={generating} onClick={onGenerate}>
            {generating ? "Generating…" : "Generate forecast"}
          </button>
        ) : null}
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card">
          <p className="text-xs uppercase text-slate-500">Current readiness</p>
          <p className="text-2xl font-semibold text-brand-700">
            {formatScore(forecast.current_readiness)}
          </p>
        </div>
        <div className="card">
          <p className="text-xs uppercase text-slate-500">Projected readiness</p>
          <p className="text-2xl font-semibold text-brand-700">
            {formatScore(forecast.projected_readiness)}
          </p>
        </div>
        <div className="card">
          <p className="text-xs uppercase text-slate-500">Target readiness</p>
          <p className="text-2xl font-semibold text-brand-700">
            {formatScore(forecast.target_readiness)}
          </p>
        </div>
        <div className="card">
          <p className="text-xs uppercase text-slate-500">Status</p>
          <div className="mt-2">
            <StatusBadge
              label={formatLabel(forecast.forecast_status)}
              tone={statusTone(forecast.forecast_status)}
            />
          </div>
          <p className="mt-2 text-xs text-slate-500">Target date: {forecast.target_date}</p>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ReadinessProjectionChart
          current={forecast.current_readiness}
          projected={forecast.projected_readiness}
          target={forecast.target_readiness}
        />
        <ProbabilityMeter probability={forecast.probability_of_success} />
      </div>

      <section className="card">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-sm font-semibold text-slate-900">Top drivers</h2>
          <div className="flex gap-2">
            {onExplain ? (
              <button type="button" className="btn-secondary text-xs" onClick={() => void handleExplain()}>
                Explain forecast
              </button>
            ) : null}
            {showRegenerate && onGenerate ? (
              <button type="button" className="btn-secondary text-xs" disabled={generating} onClick={onGenerate}>
                Regenerate
              </button>
            ) : null}
          </div>
        </div>
        <ul className="mt-3 flex flex-wrap gap-2">
          {forecast.top_drivers.map((driver) => (
            <li
              key={driver}
              className="rounded-full bg-brand-50 px-3 py-1 text-xs font-medium text-brand-800"
            >
              {driver}
            </li>
          ))}
        </ul>
        {forecast.explanations.length > 0 ? (
          <ul className="mt-4 space-y-2 text-sm text-slate-700">
            {forecast.explanations.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        ) : null}
      </section>

      <section className="card">
        <h2 className="text-sm font-semibold text-slate-900">Scenario comparison</h2>
        <div className="mt-4">
          <ScenarioTable scenarios={forecast.scenarios} />
        </div>
      </section>

      {onSimulateCustom ? (
        <section className="card">
          <h2 className="text-sm font-semibold text-slate-900">What-if simulator</h2>
          <p className="mt-1 text-sm text-slate-600">
            Enter weekly study hours to simulate a custom scenario.
          </p>
          <div className="mt-4 flex flex-wrap items-end gap-3">
            <label className="text-sm text-slate-700">
              Hours per week
              <input
                type="number"
                min={1}
                max={42}
                step={0.5}
                className="mt-1 block w-32 rounded-lg border border-slate-200 px-3 py-2"
                value={customHours}
                onChange={(event) => setCustomHours(event.target.value)}
              />
            </label>
            <button
              type="button"
              className="btn-primary"
              disabled={simulating}
              onClick={() => {
                const hours = Number(customHours);
                if (Number.isFinite(hours) && hours > 0) {
                  onSimulateCustom(Math.round(hours * 60));
                }
              }}
            >
              {simulating ? "Simulating…" : "Simulate"}
            </button>
          </div>
        </section>
      ) : null}

      {history ? (
        <section className="card">
          <h2 className="text-sm font-semibold text-slate-900">Forecast history</h2>
          <div className="mt-4">
            <ForecastHistoryTable entries={history} />
          </div>
        </section>
      ) : null}

      {explanation ? (
        <div className="card">
          <h3 className="text-sm font-semibold text-slate-900">Forecast explanation</h3>
          <div className="mt-3 grid gap-3 sm:grid-cols-3 text-sm text-slate-700">
            <p>Weekly gain: +{formatScore(explanation.weekly_gain)}</p>
            <p>Adherence: {formatPercent(explanation.adherence_rate * 100)}</p>
            <p>Effectiveness: {formatScore(explanation.effectiveness_multiplier)}×</p>
          </div>
          <ul className="mt-4 space-y-2 text-sm text-slate-700">
            {explanation.explanations.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
          <button type="button" className="btn-secondary mt-4" onClick={() => setExplanation(null)}>
            Close
          </button>
        </div>
      ) : null}
    </div>
  );
}
