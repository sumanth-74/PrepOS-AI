"use client";

import { useConceptInfo } from "@/hooks/use-concept-lookup";

interface ConceptLabelProps {
  conceptId: string;
  examId?: string | null;
  showPath?: boolean;
  className?: string;
}

export function ConceptLabel({
  conceptId,
  examId,
  showPath = false,
  className = "",
}: ConceptLabelProps) {
  const info = useConceptInfo(examId ?? null, conceptId);

  if (!info) {
    return (
      <span className={`inline-block h-4 w-32 animate-pulse rounded bg-slate-200 ${className}`} />
    );
  }

  return (
    <span className={className}>
      <span className="font-medium text-slate-900">{info.name}</span>
      {showPath ? (
        <span className="mt-0.5 block text-xs text-slate-500">{info.path}</span>
      ) : null}
    </span>
  );
}
