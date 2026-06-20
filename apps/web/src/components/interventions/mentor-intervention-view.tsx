"use client";

import { useState } from "react";

import { StatusBadge } from "@/components/ui/status-badge";
import type {
  InterventionExplainResponse,
  InterventionRecordItem,
  RecommendedInterventionItem,
  StudentInterventionResponse,
} from "@/lib/types/api";
import { formatLabel, formatScore } from "@/lib/utils/format";

function confidenceTone(confidence: string): "success" | "warning" | "info" {
  if (confidence === "high") return "success";
  if (confidence === "medium") return "warning";
  return "info";
}

function statusTone(status: string): "success" | "warning" | "info" {
  if (status === "completed") return "success";
  if (status === "in_progress") return "warning";
  return "info";
}

export function MentorInterventionView({
  bundle,
  onGenerate,
  onExecute,
  onComplete,
  onExplain,
  generating,
  executing,
  completing,
}: {
  bundle: StudentInterventionResponse;
  onGenerate?: () => void;
  onExecute?: (interventionId: string) => void;
  onComplete?: (interventionId: string) => void;
  onExplain?: (interventionId: string) => Promise<InterventionExplainResponse>;
  generating?: boolean;
  executing?: boolean;
  completing?: boolean;
}) {
  const [explanation, setExplanation] = useState<InterventionExplainResponse | null>(null);

  const handleExplain = async (interventionId: string) => {
    if (!onExplain) return;
    setExplanation(await onExplain(interventionId));
  };

  return (
    <div className="space-y-8">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div className="card">
          <p className="text-xs uppercase text-slate-500">Current readiness</p>
          <p className="text-2xl font-semibold text-brand-700">
            {bundle.current_readiness != null ? formatScore(bundle.current_readiness) : "—"}
          </p>
        </div>
        <div className="card">
          <p className="text-xs uppercase text-slate-500">Forecast status</p>
          <div className="mt-2">
            {bundle.forecast_status ? (
              <StatusBadge label={formatLabel(bundle.forecast_status)} tone="info" />
            ) : (
              <span className="text-sm text-slate-600">—</span>
            )}
          </div>
        </div>
        <div className="card">
          <p className="text-xs uppercase text-slate-500">Active interventions</p>
          <p className="text-2xl font-semibold text-brand-700">{bundle.active_interventions.length}</p>
        </div>
      </div>

      {onGenerate ? (
        <div className="flex justify-end">
          <button type="button" className="btn-primary" disabled={generating} onClick={onGenerate}>
            {generating ? "Generating…" : "Generate interventions"}
          </button>
        </div>
      ) : null}

      <section className="card">
        <h2 className="text-sm font-semibold text-slate-900">Recommended interventions</h2>
        <div className="mt-4 overflow-x-auto">
          <RecommendationTable items={bundle.recommended_interventions} />
        </div>
      </section>

      <section className="card">
        <h2 className="text-sm font-semibold text-slate-900">Active & tracked interventions</h2>
        <div className="mt-4 space-y-3">
          {bundle.active_interventions.length === 0 ? (
            <p className="text-sm text-slate-600">No active interventions. Generate recommendations to begin.</p>
          ) : (
            bundle.active_interventions.map((item) => (
              <InterventionActionCard
                key={item.id}
                item={item}
                executing={executing}
                completing={completing}
                onExecute={onExecute}
                onComplete={onComplete}
                onExplain={onExplain ? () => void handleExplain(item.id) : undefined}
              />
            ))
          )}
        </div>
      </section>

      {explanation ? (
        <div className="card">
          <h3 className="text-sm font-semibold text-slate-900">Intervention explanation</h3>
          <ul className="mt-3 space-y-2 text-sm text-slate-700">
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

function RecommendationTable({ items }: { items: RecommendedInterventionItem[] }) {
  if (items.length === 0) {
    return <p className="text-sm text-slate-600">No recommendations yet.</p>;
  }

  return (
    <table className="min-w-full text-sm">
      <thead>
        <tr className="border-b border-slate-100 text-left text-xs uppercase text-slate-500">
          <th className="py-2 pr-4">Intervention</th>
          <th className="py-2 pr-4">Concept</th>
          <th className="py-2 pr-4">Gain</th>
          <th className="py-2 pr-4">Priority</th>
          <th className="py-2">Reason</th>
        </tr>
      </thead>
      <tbody>
        {items.map((item, index) => (
          <tr key={`${item.intervention_type}-${item.concept_id ?? index}`} className="border-b border-slate-50">
            <td className="py-3 pr-4 font-medium text-slate-900">{formatLabel(item.intervention_type)}</td>
            <td className="py-3 pr-4 text-slate-700">{item.concept ?? "—"}</td>
            <td className="py-3 pr-4 text-slate-700">+{formatScore(item.predicted_gain)}</td>
            <td className="py-3 pr-4">
              <StatusBadge label={formatScore(item.priority_score)} tone={confidenceTone(item.confidence)} />
            </td>
            <td className="py-3 text-slate-700">{item.reason}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function InterventionActionCard({
  item,
  onExecute,
  onComplete,
  onExplain,
  executing,
  completing,
}: {
  item: InterventionRecordItem;
  onExecute?: (id: string) => void;
  onComplete?: (id: string) => void;
  onExplain?: () => void;
  executing?: boolean;
  completing?: boolean;
}) {
  return (
    <div className="rounded-lg border border-slate-100 p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-medium text-slate-900">{formatLabel(item.intervention_type)}</p>
          <p className="text-sm text-slate-600">{item.concept ?? item.reason}</p>
        </div>
        <StatusBadge label={formatLabel(item.status)} tone={statusTone(item.status)} />
      </div>
      <div className="mt-3 flex flex-wrap gap-3 text-xs text-slate-500">
        <span>Priority {formatScore(item.priority_score)}</span>
        <span>Expected +{formatScore(item.predicted_gain)} readiness</span>
      </div>
      <div className="mt-3 flex gap-2">
        {onExplain ? (
          <button type="button" className="btn-secondary text-xs" onClick={onExplain}>
            Explain
          </button>
        ) : null}
        {onExecute && item.status === "pending" ? (
          <button
            type="button"
            className="btn-primary text-xs"
            disabled={executing}
            onClick={() => onExecute(item.id)}
          >
            Execute
          </button>
        ) : null}
        {onComplete && item.status === "in_progress" ? (
          <button
            type="button"
            className="btn-primary text-xs"
            disabled={completing}
            onClick={() => onComplete(item.id)}
          >
            Complete
          </button>
        ) : null}
      </div>
    </div>
  );
}

export function MentorInterventionQueueView({
  items,
}: {
  items: import("@/lib/types/api").MentorInterventionQueueItem[];
}) {
  if (items.length === 0) {
    return <p className="text-sm text-slate-600">No students in the intervention queue yet.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="border-b border-slate-100 text-left text-xs uppercase text-slate-500">
            <th className="py-2 pr-4">Student</th>
            <th className="py-2 pr-4">Top action</th>
            <th className="py-2 pr-4">Priority</th>
            <th className="py-2 pr-4">Gain</th>
            <th className="py-2">Reason</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={`${item.student_id}-${item.top_intervention_type}`} className="border-b border-slate-50">
              <td className="py-3 pr-4 font-mono text-xs text-slate-700">{item.student_id.slice(0, 8)}…</td>
              <td className="py-3 pr-4 text-slate-900">
                {formatLabel(item.top_intervention_type)}
                {item.top_concept ? ` · ${item.top_concept}` : ""}
              </td>
              <td className="py-3 pr-4">{formatScore(item.priority_score)}</td>
              <td className="py-3 pr-4">+{formatScore(item.predicted_gain)}</td>
              <td className="py-3 text-slate-700">{item.reason}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
