"use client";

import { CopilotMessageList } from "@/features/copilot/components/copilot-message-list";
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
    <section
      className="flex h-[min(32rem,calc(100vh-6rem))] w-[min(24rem,calc(100vw-2rem))] flex-col overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xl"
      role="dialog"
      aria-modal="true"
      aria-labelledby="copilot-panel-title"
    >
      <header className="flex items-start justify-between gap-2 border-b border-slate-200 px-4 py-3">
        <div>
          <h2 id="copilot-panel-title" className="text-base font-semibold text-slate-900">
            {personaLabel}
          </h2>
          <p className="text-xs text-slate-500">
            {persona === "student"
              ? "Study insights from your twin plus grounded answers from indexed content."
              : persona === "mentor"
                ? "Student coaching insights plus grounded content explanations with citations."
                : "Deterministic answers from your PrepOS data."}
          </p>
          {context.studentId ? (
            <p className="mt-1 text-xs text-slate-500">Student context active</p>
          ) : controller.persona === "mentor" ? (
            <p className="mt-1 text-xs text-amber-700">
              Open a student profile or case to enable student-specific prompts.
            </p>
          ) : null}
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            className="btn-secondary px-2 py-1 text-xs"
            onClick={clearConversation}
            disabled={messages.length === 0}
          >
            Clear
          </button>
          <button
            type="button"
            className="btn-secondary px-2 py-1 text-xs"
            onClick={onClose}
            aria-label="Close copilot panel"
          >
            Close
          </button>
        </div>
      </header>

      <CopilotMessageList messages={messages} isLoading={isLoading} />

      <div className="border-t border-slate-200 p-3">
        <div className="mb-2 flex flex-wrap gap-2" aria-label="Suggested prompts">
          {suggestedPrompts.map((prompt) => (
            <button
              key={prompt}
              type="button"
              className="rounded-full border border-slate-200 bg-slate-50 px-2 py-1 text-xs text-slate-700 hover:bg-slate-100"
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
            placeholder="Ask about readiness, concepts, plans, or platform health…"
            disabled={isLoading}
            autoComplete="off"
          />
          <button type="submit" className="btn-primary shrink-0" disabled={isLoading || !input.trim()}>
            Send
          </button>
        </form>
      </div>
    </section>
  );
}
