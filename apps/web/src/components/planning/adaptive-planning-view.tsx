"use client";

import { useState } from "react";

import { ConceptLabel } from "@/components/ui/concept-label";
import { StatusBadge } from "@/components/ui/status-badge";
import type { AdaptivePlanItem, AdaptivePlanResponse, PlanExplainResponse } from "@/lib/types/api";
import { formatLabel, formatScore } from "@/lib/utils/format";

function PlanItemCard({
  item,
  examId,
  onComplete,
  onExplain,
  busy,
}: {
  item: AdaptivePlanItem;
  examId: string | null;
  onComplete?: () => void;
  onExplain?: () => void;
  busy?: boolean;
}) {
  return (
    <div className="rounded-lg border border-slate-100 p-4">
      <div className="flex items-start justify-between gap-3">
        <ConceptLabel conceptId={item.concept_id} examId={examId} showPath />
        <StatusBadge
          label={item.completion_status === "completed" ? "Completed" : formatScore(item.priority_score)}
          tone={item.completion_status === "completed" ? "success" : "info"}
        />
      </div>
      <p className="mt-2 text-sm text-slate-600">{item.source_reason}</p>
      <div className="mt-3 flex flex-wrap gap-3 text-xs text-slate-500">
        <span>{item.estimated_minutes} min</span>
        <span>+{item.estimated_readiness_gain.toFixed(1)} readiness</span>
        <span>{formatLabel(item.activity_type)}</span>
        <span>{item.scheduled_date}</span>
      </div>
      <div className="mt-3 flex gap-2">
        {onExplain ? (
          <button type="button" className="btn-secondary text-xs" onClick={onExplain}>
            Explain
          </button>
        ) : null}
        {onComplete && item.completion_status !== "completed" ? (
          <button type="button" className="btn-primary text-xs" disabled={busy} onClick={onComplete}>
            Mark complete
          </button>
        ) : null}
      </div>
    </div>
  );
}

export function AdaptivePlanningView({
  plan,
  examId,
  onGenerate,
  onCompleteItem,
  onExplainConcept,
  generating,
  completing,
  showRegenerate,
}: {
  plan: AdaptivePlanResponse | undefined;
  examId: string | null;
  onGenerate?: () => void;
  onCompleteItem?: (itemId: string) => void;
  onExplainConcept?: (conceptId: string) => Promise<PlanExplainResponse>;
  generating?: boolean;
  completing?: boolean;
  showRegenerate?: boolean;
}) {
  const [explanation, setExplanation] = useState<PlanExplainResponse | null>(null);

  const handleExplain = async (conceptId: string) => {
    if (!onExplainConcept) return;
    const result = await onExplainConcept(conceptId);
    setExplanation(result);
  };

  if (!plan) {
    return (
      <div className="card space-y-3">
        <p className="text-sm text-slate-600">No adaptive plan yet.</p>
        {onGenerate ? (
          <button type="button" className="btn-primary" disabled={generating} onClick={onGenerate}>
            {generating ? "Generating…" : "Generate weekly plan"}
          </button>
        ) : null}
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card">
          <p className="text-xs uppercase text-slate-500">Readiness snapshot</p>
          <p className="text-2xl font-semibold text-brand-700">
            {plan.readiness_snapshot != null ? formatScore(plan.readiness_snapshot) : "—"}
          </p>
        </div>
        <div className="card">
          <p className="text-xs uppercase text-slate-500">Forecast snapshot</p>
          <p className="text-2xl font-semibold text-brand-700">
            {plan.forecast_snapshot != null ? formatScore(plan.forecast_snapshot) : "—"}
          </p>
        </div>
        <div className="card">
          <p className="text-xs uppercase text-slate-500">Estimated gain</p>
          <p className="text-2xl font-semibold text-brand-700">
            +{plan.total_estimated_gain.toFixed(1)}
          </p>
        </div>
        <div className="card">
          <p className="text-xs uppercase text-slate-500">Daily budget</p>
          <p className="text-2xl font-semibold text-brand-700">{plan.daily_minutes_budget} min</p>
        </div>
      </div>

      {showRegenerate && onGenerate ? (
        <div className="flex justify-end">
          <button type="button" className="btn-secondary" disabled={generating} onClick={onGenerate}>
            Regenerate plan
          </button>
        </div>
      ) : null}

      <section>
        <h2 className="mb-3 text-sm font-semibold text-slate-900">Today</h2>
        <div className="space-y-3">
          {plan.today_items.length === 0 ? (
            <p className="text-sm text-slate-600">No items scheduled for today.</p>
          ) : (
            plan.today_items.map((item) => (
              <PlanItemCard
                key={item.id}
                item={item}
                examId={examId}
                busy={completing}
                onComplete={onCompleteItem ? () => onCompleteItem(item.id) : undefined}
                onExplain={onExplainConcept ? () => void handleExplain(item.concept_id) : undefined}
              />
            ))
          )}
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold text-slate-900">This week</h2>
        <div className="space-y-3">
          {plan.week_items.map((item) => (
            <PlanItemCard key={item.id} item={item} examId={examId} />
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold text-slate-900">Next week draft</h2>
        <div className="space-y-3">
          {plan.next_week_draft.map((item) => (
            <PlanItemCard key={item.id} item={item} examId={examId} />
          ))}
        </div>
      </section>

      {explanation ? (
        <div className="card">
          <h3 className="text-sm font-semibold text-slate-900">
            Plan explanation — {explanation.concept_name}
          </h3>
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
