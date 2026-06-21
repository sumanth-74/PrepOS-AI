"use client";

import { motion } from "framer-motion";
import { Send, Sparkles, Trash2, X } from "lucide-react";

import { CopilotMessageList } from "@/features/copilot/components/copilot-message-list";
import { Button } from "@/components/design-system/button";
import type { useCopilot } from "@/features/copilot/hooks/use-copilot";

type CopilotController = ReturnType<typeof useCopilot>;

interface CopilotPanelProps {
  controller: CopilotController;
  onClose: () => void;
}

export function CopilotPanel({ controller, onClose }: CopilotPanelProps) {
  const {
    input,
    setInput,
    messages,
    isLoading,
    persona,
    personaLabel,
    suggestedPrompts,
    context,
    sendQuestion,
    clearConversation,
  } = controller;

  return (
    <motion.section
      initial={{ opacity: 0, y: 20, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 20, scale: 0.96 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      className="flex h-[min(36rem,calc(100vh-5rem))] w-[min(28rem,calc(100vw-2rem))] flex-col overflow-hidden rounded-2xl border border-border bg-surface shadow-elevated"
      role="dialog"
      aria-modal="true"
      aria-labelledby="copilot-panel-title"
    >
      <header className="relative overflow-hidden border-b border-border px-4 py-4">
        <div className="absolute inset-0 bg-gradient-growth opacity-[0.07]" />
        <div className="relative flex items-start justify-between gap-2">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-growth shadow-glow">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 id="copilot-panel-title" className="text-sm font-bold text-foreground">
                {persona === "student" ? "AI Coach" : personaLabel}
              </h2>
              <p className="mt-0.5 text-xs text-foreground-muted">
                {persona === "student"
                  ? "Personal, progress-aware guidance for your UPSC journey"
                  : persona === "mentor"
                    ? "Student coaching + cited explanations"
                    : "Platform intelligence & operations"}
              </p>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {context.studentId ? (
                  <span className="rounded-full bg-growth-100 px-2 py-0.5 text-[10px] font-medium text-growth-800 dark:bg-growth-900/50 dark:text-growth-300">
                    Student context
                  </span>
                ) : null}
                {persona === "student" ? (
                  <span className="rounded-full bg-surface-raised px-2 py-0.5 text-[10px] font-medium text-foreground-muted">
                    Twin connected
                  </span>
                ) : null}
                {persona === "mentor" && !context.studentId ? (
                  <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-medium text-amber-800">
                    Open a student profile
                  </span>
                ) : null}
              </div>
            </div>
          </div>
          <div className="flex gap-1">
            <button
              type="button"
              className="btn-ghost p-2"
              onClick={clearConversation}
              disabled={messages.length === 0}
              aria-label="Clear conversation"
            >
              <Trash2 className="h-4 w-4" />
            </button>
            <button
              type="button"
              className="btn-ghost p-2"
              onClick={onClose}
              aria-label="Close copilot panel"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      </header>

      <CopilotMessageList messages={messages} isLoading={isLoading} onFollowUp={sendQuestion} />

      <div className="border-t border-border bg-surface-raised/50 p-3">
        <div className="mb-2 flex gap-2 overflow-x-auto pb-1" aria-label="Suggested prompts">
          {suggestedPrompts.map((prompt) => (
            <button
              key={prompt}
              type="button"
              className="shrink-0 rounded-full border border-border bg-surface px-3 py-1.5 text-xs font-medium text-foreground-muted transition-colors hover:border-growth-300 hover:bg-growth-50 hover:text-growth-700 dark:hover:bg-growth-950/40"
              onClick={() => void sendQuestion(prompt)}
              disabled={isLoading}
            >
              {prompt}
            </button>
          ))}
        </div>
        <form
          className="flex gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            void sendQuestion(input);
          }}
        >
          <label htmlFor="copilot-input" className="sr-only">
            Ask the copilot
          </label>
          <input
            id="copilot-input"
            className="input flex-1"
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask anything about your preparation…"
            disabled={isLoading}
            autoComplete="off"
          />
          <Button type="submit" size="icon" disabled={isLoading || !input.trim()} aria-label="Send message">
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </motion.section>
  );
}
