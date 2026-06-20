"use client";

import { useEffect, useRef } from "react";

import type { CopilotMessage } from "@/features/copilot/types";

interface CopilotMessageListProps {
  messages: CopilotMessage[];
  isLoading: boolean;
}

function confidenceBadgeClass(confidence: string): string {
  if (confidence === "high") {
    return "bg-emerald-100 text-emerald-800";
  }
  if (confidence === "medium") {
    return "bg-amber-100 text-amber-800";
  }
  return "bg-slate-200 text-slate-700";
}

export function CopilotMessageList({ messages, isLoading }: CopilotMessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center p-6 text-center text-sm text-slate-500">
        Ask a question or choose a suggested prompt below.
      </div>
    );
  }

  return (
    <div
      className="flex-1 space-y-3 overflow-y-auto p-4"
      role="log"
      aria-live="polite"
      aria-relevant="additions"
      aria-label="Copilot conversation"
    >
      {messages.map((message) => (
        <article
          key={message.id}
          className={`rounded-lg px-3 py-2 text-sm ${
            message.role === "user"
              ? "ml-8 bg-brand-600 text-white"
              : "mr-4 bg-slate-100 text-slate-800"
          }`}
          aria-label={message.role === "user" ? "Your message" : "Copilot response"}
        >
          <p className="whitespace-pre-wrap">{message.content}</p>
          {message.role === "assistant" && message.confidence ? (
            <p className="mt-2 flex flex-wrap items-center gap-2">
              <span
                className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${confidenceBadgeClass(message.confidence)}`}
              >
                Confidence: {message.confidence}
              </span>
              {message.studentContextUsed ? (
                <span className="inline-flex rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-medium text-indigo-800">
                  Student context used
                </span>
              ) : null}
            </p>
          ) : null}
          {message.role === "assistant" && message.recommendations && message.recommendations.length > 0 ? (
            <div className="mt-3 space-y-2 rounded-md border border-slate-200 bg-white p-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Recommendations
              </p>
              <ul className="space-y-2">
                {message.recommendations.map((item) => (
                  <li key={item.concept_id} className="text-xs text-slate-700">
                    <span className="font-medium text-slate-900">{item.concept_name}</span>
                    {" — "}
                    impact {item.impact_score.toFixed(1)}/10, gain +
                    {item.estimated_readiness_gain.toFixed(1)}
                    {item.reasons && item.reasons.length > 0 ? (
                      <span className="block text-slate-500">Why: {item.reasons.join("; ")}</span>
                    ) : null}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          {message.role === "assistant" && message.citations && message.citations.length > 0 ? (
            <details className="mt-2 text-xs opacity-90">
              <summary className="cursor-pointer">
                Citations ({message.citations.length})
              </summary>
              <ul className="mt-1 list-inside list-disc">
                {message.citations.map((citation) => (
                  <li key={citation.chunk_id}>{citation.source_title}</li>
                ))}
              </ul>
            </details>
          ) : null}
          {message.role === "assistant" && message.sources && message.sources.length > 0 ? (
            <details className="mt-2 text-xs opacity-80">
              <summary className="cursor-pointer">Sources ({message.sources.length})</summary>
              <ul className="mt-1 list-inside list-disc">
                {message.sources.map((source) => (
                  <li key={`${source.reference}-${source.label}`}>
                    {source.label} — {source.reference}
                  </li>
                ))}
              </ul>
            </details>
          ) : null}
        </article>
      ))}
      {isLoading ? (
        <p className="text-sm text-slate-500" aria-live="polite">
          Copilot is preparing a response…
        </p>
      ) : null}
      <div ref={bottomRef} />
    </div>
  );
}
