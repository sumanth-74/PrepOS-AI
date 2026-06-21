"use client";

import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bot, Sparkles, User } from "lucide-react";

import type { CopilotMessage } from "@/features/copilot/types";
import { CopilotCardList } from "@/features/copilot/components/copilot-cards";
import { followUpsForIntent } from "@/features/copilot/follow-up-prompts";
import { cn } from "@/lib/utils/cn";

interface CopilotMessageListProps {
  messages: CopilotMessage[];
  isLoading: boolean;
  onFollowUp?: (question: string) => void;
}

function confidenceTone(confidence: string): string {
  if (confidence === "high") return "bg-growth-100 text-growth-800 dark:bg-growth-900/50 dark:text-growth-300";
  if (confidence === "medium") return "bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-300";
  return "bg-surface-raised text-foreground-muted";
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-2 px-2 py-1" aria-live="polite" aria-label="Copilot is thinking">
      <div className="flex gap-1">
        {[0, 1, 2].map((i) => (
          <motion.span
            key={i}
            className="h-2 w-2 rounded-full bg-growth-400"
            animate={{ opacity: [0.4, 1, 0.4], y: [0, -3, 0] }}
            transition={{ duration: 1, repeat: Infinity, delay: i * 0.15 }}
          />
        ))}
      </div>
      <span className="text-xs text-foreground-muted">Analyzing your preparation data…</span>
    </div>
  );
}

function StreamingText({ text }: { text: string }) {
  return (
    <motion.p
      className="whitespace-pre-wrap leading-relaxed"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      {text}
    </motion.p>
  );
}

export function CopilotMessageList({ messages, isLoading, onFollowUp }: CopilotMessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-4 p-8 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-growth shadow-glow">
          <Sparkles className="h-8 w-8 text-white" />
        </div>
        <div>
          <p className="text-sm font-semibold text-foreground">Your AI learning companion</p>
          <p className="mt-1 max-w-xs text-xs text-foreground-muted">
            Ask about readiness, weak concepts, study plans, forecasts, or PYQ patterns.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div
      className="flex-1 space-y-4 overflow-y-auto p-4"
      role="log"
      aria-live="polite"
      aria-relevant="additions"
      aria-label="Copilot conversation"
    >
      <AnimatePresence initial={false}>
        {messages.map((message, index) => (
          <motion.article
            key={message.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: index * 0.02, ease: [0.22, 1, 0.36, 1] }}
            className={cn(
              "flex gap-3",
              message.role === "user" ? "flex-row-reverse" : "flex-row",
            )}
            aria-label={message.role === "user" ? "Your message" : "Copilot response"}
          >
            <div
              className={cn(
                "flex h-8 w-8 shrink-0 items-center justify-center rounded-xl",
                message.role === "user"
                  ? "bg-growth-600 text-white"
                  : "bg-gradient-growth text-white shadow-soft",
              )}
            >
              {message.role === "user" ? (
                <User className="h-4 w-4" />
              ) : (
                <Bot className="h-4 w-4" />
              )}
            </div>
            <div
              className={cn(
                "max-w-[85%] rounded-2xl px-4 py-3 text-sm",
                message.role === "user"
                  ? "bg-growth-600 text-white"
                  : "border border-border bg-surface-raised text-foreground shadow-soft",
              )}
            >
              <StreamingText text={message.content} />

              {message.role === "assistant" && message.cards && message.cards.length > 0 ? (
                <CopilotCardList cards={message.cards} />
              ) : null}

              {message.role === "assistant" && message.explanation ? (
                <p className="mt-3 rounded-lg bg-surface p-2.5 text-xs text-foreground-muted">
                  <span className="font-semibold text-foreground">How calculated: </span>
                  {message.explanation}
                </p>
              ) : null}

              {message.role === "assistant" && message.confidence ? (
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  <span
                    className={cn(
                      "inline-flex rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide",
                      confidenceTone(message.confidence),
                    )}
                  >
                    {message.confidence} confidence
                  </span>
                  {message.studentContextUsed ? (
                    <span className="inline-flex rounded-full bg-indigo-100 px-2.5 py-0.5 text-[10px] font-semibold text-indigo-800 dark:bg-indigo-900/50 dark:text-indigo-300">
                      Twin context
                    </span>
                  ) : null}
                </div>
              ) : null}

              {message.role === "assistant" &&
              message.recommendations &&
              message.recommendations.length > 0 ? (
                <div className="mt-3 space-y-2">
                  {message.recommendations.map((item) => (
                    <div
                      key={item.concept_id}
                      className="rounded-xl border border-growth-200/60 bg-growth-50/50 p-3 dark:border-growth-800/40 dark:bg-growth-950/30"
                    >
                      <p className="text-sm font-semibold text-foreground">{item.concept_name}</p>
                      <p className="mt-1 text-xs text-foreground-muted">
                        Impact {item.impact_score.toFixed(1)}/10 · Readiness gain +
                        {item.estimated_readiness_gain.toFixed(1)}
                      </p>
                      {item.reasons && item.reasons.length > 0 ? (
                        <p className="mt-1 text-[11px] text-foreground-subtle">
                          {item.reasons.join(" · ")}
                        </p>
                      ) : null}
                    </div>
                  ))}
                </div>
              ) : null}

              {message.role === "assistant" && message.citations && message.citations.length > 0 ? (
                <details className="mt-3 text-xs">
                  <summary className="cursor-pointer font-medium text-growth-600">
                    {message.citations.length} source
                    {message.citations.length === 1 ? "" : "s"}
                  </summary>
                  <ul className="mt-2 space-y-1 text-foreground-muted">
                    {message.citations.map((citation) => (
                      <li key={citation.chunk_id} className="flex items-start gap-2">
                        <FileText className="mt-0.5 h-3 w-3 shrink-0" />
                        {citation.source_title}
                      </li>
                    ))}
                  </ul>
                </details>
              ) : null}

              {message.role === "assistant" &&
              onFollowUp &&
              !isLoading &&
              index === messages.length - 1 ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  {followUpsForIntent(message.intent).map((followUp) => (
                    <button
                      key={followUp}
                      type="button"
                      className="rounded-full border border-growth-200 bg-growth-50 px-2.5 py-1 text-[11px] font-medium text-growth-800 hover:bg-growth-100 dark:border-growth-800 dark:bg-growth-950/40 dark:text-growth-300"
                      onClick={() => onFollowUp(followUp)}
                    >
                      {followUp}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          </motion.article>
        ))}
      </AnimatePresence>

      {isLoading ? <TypingIndicator /> : null}
      <div ref={bottomRef} />
    </div>
  );
}

function FileText({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
    </svg>
  );
}
